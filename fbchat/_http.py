import json
import asks

from random import choice
from typing import Type, List, Dict, Any, ClassVar, Optional
from copy import copy
from asks.response_objects import Response

__all__ = ("BaseSession", "FacebookResponse", "FacebookSession")


class BaseSession(asks.Session):
    response_cls = Response  # type: ClassVar[Type[Response]]

    ENDPOINTS = []  # type: List[str]

    def __init__(self, params: Dict = None, **kwargs) -> None:
        if params is None:
            params = {}
        self.params = params
        super().__init__(**kwargs)

    def _rewrite_response_class(self, resp: Response) -> Response:
        """Override default `asks.Response` class with our own class

        Note:
            Will not call `__init__` on the response, as the response is already
            initialized. Only used to fix convenience methods like `.json`
        """
        resp.__class__ = self.response_cls
        return resp

    def get_cookies(self, netloc: str = None, path: str = "") -> Dict[str, str]:
        """Get a dict of cookie values"""
        if netloc is None:
            netloc = self.base_location
        return self._cookie_tracker.get_additional_cookies(netloc, path)

    def get_cookie(
        self, name: str, netloc: str = None, path: str = ""
    ) -> Optional[str]:
        """Get a single cookie"""
        return self.get_cookies(netloc=netloc, path=path).get(name)

    async def request(self, method: str, url: str = None, **kwargs) -> Response:
        """Overwritten to enable default parameters and customizing response class"""
        params = copy(self.params)
        params.update(kwargs.pop("params", {}))

        resp = await super().request(method, url=url, params=params, **kwargs)

        return self._rewrite_response_class(resp)


class FacebookResponse(Response):
    def json(self):
        return json.loads(self._strip_text_for_json(self.text))

    @staticmethod
    def _strip_text_for_json(text: str) -> str:
        """Removes `for(;;);` (and other cruft) that preceeds JSON responses"""
        try:
            return text[text.index("{") :]
        except ValueError:
            raise ValueError("No JSON object found: {!r}".format(text))


class FacebookSession(BaseSession):
    response_cls = FacebookResponse

    USER_AGENTS = [
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.90 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_3) AppleWebKit/601.1.10 (KHTML, like Gecko) Version/8.0.5 Safari/601.1.10",
        "Mozilla/5.0 (Windows NT 6.3; WOW64; ; NCT50_AAP285C84A1328) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.90 Safari/537.36",
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/22.0.1207.1 Safari/537.1",
        "Mozilla/5.0 (X11; CrOS i686 2268.111.0) AppleWebKit/536.11 (KHTML, like Gecko) Chrome/20.0.1132.57 Safari/536.11",
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.6 (KHTML, like Gecko) Chrome/20.0.1092.0 Safari/536.6",
    ]

    BASE_URL = "https://www.facebook.com"

    def __init__(self, user_agent: str = None, **kwargs) -> None:
        kwargs["base_location"] = self.BASE_URL
        kwargs.setdefault("persist_cookies", True)

        if not user_agent:
            user_agent = choice(self.USER_AGENTS)

        kwargs.setdefault("headers", {})
        kwargs["headers"].setdefault("Referer", self.BASE_URL)
        kwargs["headers"].setdefault("User-Agent", user_agent)

        super().__init__(**kwargs)
