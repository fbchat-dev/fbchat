import json
import requests

from random import choice
from typing import Type, List, Dict, Any, ClassVar, Optional
from copy import copy

__all__ = ("BaseSession", "Response", "Session")


class BaseSession(requests.Session):
    response_cls = requests.Response  # type: ClassVar[Type[requests.Response]]

    BASE_URL = None  # type: ClassVar[str]

    def _rewrite_response_class(self, resp: requests.Response) -> requests.Response:
        """Override default `asks.Response` class with our own class

        Note:
            Will not call `__init__` on the response, as the response is already
            initialized. Only used to fix convenience methods like `.json`
        """
        resp.__class__ = self.response_cls
        return resp

    async def request(self, method: str, url: str, **kwargs) -> requests.Response:
        """Overwritten to enable base url, async and customizing response class"""
        if url.startswith("/") and self.BASE_URL is not None:
            url = self.BASE_URL + url

        r = super().request(method, url, **kwargs)

        return self._rewrite_response_class(r)


class Response(requests.Response):
    def json(self):
        return json.loads(self._strip_text_for_json(self.text))

    @staticmethod
    def _strip_text_for_json(text: str) -> str:
        """Removes `for(;;);` (and other cruft) that preceeds JSON responses"""
        try:
            return text[text.index("{") :]
        except ValueError:
            raise ValueError("No JSON object found: {!r}".format(text))


class Session(BaseSession):
    response_cls = Response

    USER_AGENTS = [
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.90 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_3) AppleWebKit/601.1.10 (KHTML, like Gecko) Version/8.0.5 Safari/601.1.10",
        "Mozilla/5.0 (Windows NT 6.3; WOW64; ; NCT50_AAP285C84A1328) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.90 Safari/537.36",
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/22.0.1207.1 Safari/537.1",
        "Mozilla/5.0 (X11; CrOS i686 2268.111.0) AppleWebKit/536.11 (KHTML, like Gecko) Chrome/20.0.1132.57 Safari/536.11",
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.6 (KHTML, like Gecko) Chrome/20.0.1092.0 Safari/536.6",
    ]

    BASE_URL = "https://www.facebook.com"

    def __init__(self, user_agent: str = None) -> None:
        super().__init__()

        if user_agent is None:
            user_agent = choice(self.USER_AGENTS)

        self.header = {"Referer": self.BASE_URL, "User-Agent": user_agent}
