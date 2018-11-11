import logging
import random
import requests
import trio

from ._http import BaseSession

__all__ = ("Listener",)

log = logging.getLogger(__name__)


class Listener:
    """Handles listening for events"""

    __slots__ = (
        "_session",
        "_clientid",
        "_sticky_token",
        "_sticky_pool",
        "_seq",
        "_msgs_recv",
        "_backoff",
        "mark_alive",
    )

    CONNECT_TIMEOUT = 10
    READ_TIMEOUT = 60  # The server holds the request open for 50 seconds

    PULL_URL = "https://0-edge-chat.facebook.com/pull"

    def __init__(self, session: BaseSession, mark_alive=False) -> None:
        self._session = session
        self.mark_alive = mark_alive
        self._clientid = "{:x}".format(random.randint(0, 2 ** 31))
        self._clean()

    def _clean(self) -> None:
        self._sticky_token = self._sticky_pool = None
        self._msgs_recv = 0
        self._seq = 0
        self._backoff = 0

    def __enter__(self):
        return self

    def __exit__(self, *exc) -> None:
        self._clean()

    def _get_pull_params(self):
        return {
            "seq": self._seq,
            "msgs_recv": self._msgs_recv,
            "sticky_token": self._sticky_token,
            "sticky_pool": self._sticky_pool,
            "clientid": self._clientid,
            "state": "active" if self.mark_alive else "offline",
        }

    async def _pull(self, **kwargs):
        return await self._session.get(
            self.PULL_URL,
            params=self._get_pull_params(),
            timeout=(self.CONNECT_TIMEOUT, self.READ_TIMEOUT),
            **kwargs
        )

    async def pull(self):
        try:
            r = await self._pull()
        except (requests.ConnectionError, requests.Timeout):
            # If we lost our connection, keep trying every minute
            await trio.sleep(60)
            return None

        if not r.content:
            return None

        return r.json()

    def get_backoff_delay(self):
        if self._backoff > 0:
            delay = min(5 * (2 ** max(0, self._backoff - 1)), 320)
            # self.proxyDown && "proxy_down_delay_millis" in n && (x = n.proxy_down_delay_millis)
            # self.proxyDown = False
            return delay * random.uniform(1, 1.5)
        return 0

    def handle_protocol_data(self, data):
        """Handle pull protocol data, and yield data frames ready for further parsing"""
        prev_seq = self._seq

        if "seq" in data:
            self._seq = data["seq"]
        if "s" in data:
            self._seq = data["s"]

        t = data.get("t")

        # Don't worry if you've never seen a lot of these types, this is implemented
        # based on reading the JavaScript source for Facebook's `ChannelManager`
        # Also, it seems like Facebook has some kind of streaming support, though I'm
        # not quite sure what that entails yet. But a lot of of these events is for that

        if t in ("continue", "fullReload", "msg"):
            self._backoff = 0

        if t == "backoff":
            self._backoff += 1
            log.warning("Server told us to back off")

        elif t == "lb":
            lb_info = data["lb_info"]
            self._sticky_token = lb_info["sticky"]
            if "pool" in lb_info:
                self._sticky_pool = lb_info["pool"]

        elif t == "fullReload":  # Not yet sure what consequence this has
            if "ms" in data:
                yield from self._process_ms(data, prev_seq)

        elif t == "msg":
            yield from self._process_ms(data, prev_seq)

        elif t == "heartbeat":
            # Pull request refresh, no need to do anything
            pass

        elif t == "batched":
            for item in data["batches"]:
                yield from self.handle_protocol_data(item)

        elif t == ("continue", "refresh", "refreshDelay", "test_streaming"):
            log.info("Unused protocol message: %s, %s", t, data)

        else:
            log.error("Unknown protocol message: %s, %s", t, data)

    def _process_ms(self, data, prev_seq):
        items = data["ms"]
        if self._seq - prev_seq < len(items):
            msg = "Sequence regression. Some items may have been duplicated! %s, %s, %s"
            log.error(msg, prev_seq, self._seq, items)
            # We could strip the duplicated items with:
            # items = items[len(items) - (self._seq - prev_seq): ]
            # But I'm not sure what causes a sequence regression, and there might be
            # other factors involved, so it's safer to just allow duplicates for now
        for item in items:
            self._msgs_recv += 1
            yield item
