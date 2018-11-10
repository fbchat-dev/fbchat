import logging
import requests
import trio

from random import randint

from ._http import BaseSession

__all__ = ("Listener",)

log = logging.getLogger(__name__)


class Listener:
    """Enables basic listening"""

    __slots__ = ("_session", "_clientid", "_sticky", "_pool", "_seq")

    PULL_URL = "https://0-edge-chat.facebook.com/pull"

    def __init__(self, session: BaseSession) -> None:
        self._session = session
        self._clientid = "{:x}".format(randint(0, 2 ** 31))
        self._clean()

    def _clean(self) -> None:
        self._sticky = self._pool = None
        self._seq = 0

    def __enter__(self) -> None:
        self._clean()

    def __exit__(self, *exc) -> None:
        self._clean()

    async def pull(self, mark_alive=False):
        r = await self._session.get(
            self.PULL_URL,
            params={
                "seq": self._seq,
                "msgs_recv": 0,
                "sticky_token": self._sticky,
                "sticky_pool": self._pool,
                "clientid": self._clientid,
                "state": "active" if mark_alive else "offline",
                "uid": 100002950119740,
            },
            timeout=60,
        )
        return r.json()

    async def step(self, mark_alive=False):
        """Do one cycle of the listening loop.

        This method is useful if you want to control the listener from an
        external event loop
        """

        try:
            data = await self.pull(mark_alive=mark_alive)
        except (requests.ConnectionError, requests.Timeout):
            # If we lost our internet connection, keep trying every minute
            await trio.sleep(60)
            return

        return self.parse_raw(data)

    def parse_raw(self, data):
        log.debug("Data from listening: %s", data)

        if "seq" in data:
            self._seq = data["seq"]

        type_ = data["t"]

        if type_ == "msg":
            self.parse_ms(data)
        elif type_ == "heartbeat":
            # Pull request refresh, no need to do anything
            pass
        elif type_ == "fullReload":
            self.parse_full_reload(data)
        elif type_ == "lb":
            self.parse_lb_info(data)
        else:
            log.info("Unknown data: %s", data)

    def parse_lb_info(self, data):
        self._pool = data["lb_info"]["pool"]
        self._sticky = data["lb_info"]["sticky"]

    def parse_full_reload(self, data):
        if "ms" in data:
            self.parse_ms(data)

    def parse_ms(self, data):
        for item in data["ms"]:
            self.parse(item, item["type"])

    def parse(self, data, type_):
        if type_ == "qprimer":
            return "QPrimer(Event)"
        log.info("Unknown msg: %s", data)
