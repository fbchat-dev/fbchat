import logging
import random
import requests
from async_generator import async_generator, yield_, yield_from_

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

    async def _pull(self):
        r = await self._session.get(
            self.PULL_URL,
            params={
                "seq": self._seq,
                "msgs_recv": self._msgs_recv,
                "sticky_token": self._sticky_token,
                "sticky_pool": self._sticky_pool,
                "clientid": self._clientid,
                "state": "active" if self.mark_alive else "offline",
            },
            timeout=(self.CONNECT_TIMEOUT, self.READ_TIMEOUT),
        )
        return r.json()

    @async_generator
    async def step(self):
        try:
            data = await self._pull()
        except (requests.ConnectionError, requests.Timeout):
            # If we lost our internet connection, keep trying every minute
            await trio.sleep(60)
            return

        log.debug("Data from listening: %s", data)

        await yield_from_(self._handle_protocol_data(data))

    def get_backoff_delay(self):
        if self._backoff > 0:
            delay = min(5 * (2 ** max(0, self._backoff - 1)), 320)
            # self.proxyDown && "proxy_down_delay_millis" in n && (x = n.proxy_down_delay_millis)
            # self.proxyDown = False
            return delay * random.uniform(1, 1.5)
        return 0

    def _handle_protocol_data(self, data):
        """Handle pull protocol data, and yield data frames ready for further parsing"""
        if "seq" in data:
            self._seq = data["seq"]
        if "s" in data:
            self._seq = data["s"]

        t = data.get("t")

        # Don't worry if you've never seen a lot of these types, this is implemented
        # based on reading the JavaScript source for Facebook's `ChannelManager`
        # Also, it seems like Facebook has some kind of streaming support, though I'm
        # not quite sure what that entails yet. But a lot of of these events is for that

        if t == "continue":
            self._backoff = 0
            log.info("Unused protocol message: %s, %s", t, data)

        elif t in ("refresh", "refreshDelay"):
            log.info("Unused protocol message: %s, %s", t, data)

        elif t == "test_streaming":
            log.info("Unused protocol message: %s, %s", t, data)

        elif t == "backoff":
            log.warning("Server told us to back off")
            self._backoff += 1

        elif t == "lb":
            self._pool = data["lb_info"]["pool"]
            self._sticky = data["lb_info"]["sticky"]

        elif t == "fullReload":
            self._backoff = 0
            if "ms" in data:
                for item in data["ms"]:
                    self._msgs_recv += 1
                    yield item

        elif t == "msg":
            self._backoff = 0
            for item in data["ms"]:
                self._msgs_recv += 1
                yield item

        elif t == "heartbeat":
            # Pull request refresh, no need to do anything
            pass

        elif t == "batched":
            for item in data["batches"]:
                yield from self._handle_protocol_data(item)

        else:
            log.error("Unknown protocol message: %s, %s", t, data)
