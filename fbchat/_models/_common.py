import attr
import datetime
import enum
from .._common import attrs_default
from .. import _util

from typing import Optional


class ThreadLocation(enum.Enum):
    """Used to specify where a thread is located (inbox, pending, archived, other)."""

    INBOX = "INBOX"
    PENDING = "PENDING"
    ARCHIVED = "ARCHIVED"
    OTHER = "OTHER"

    @classmethod
    def _parse(cls, value: str):
        return cls(value.lstrip("FOLDER_"))


@attrs_default
class ActiveStatus:
    #: Whether the user is active now
    active = attr.ib(type=bool)
    #: When the user was last active
    last_active = attr.ib(None, type=Optional[datetime.datetime])
    #: Whether the user is playing Messenger game now
    in_game = attr.ib(None, type=Optional[bool])

    @classmethod
    def _from_orca_presence(cls, data):
        # TODO: Handle `c` and `vc` keys (Probably some binary data)
        return cls(
            active=data["p"] in [2, 3],
            last_active=_util.seconds_to_datetime(data["l"]) if "l" in data else None,
            in_game=None,
        )


@attrs_default
class Image:
    #: URL to the image
    url = attr.ib(type=str)
    #: Width of the image
    width = attr.ib(None, type=Optional[int])
    #: Height of the image
    height = attr.ib(None, type=Optional[int])

    @classmethod
    def _from_uri(cls, data):
        return cls(
            url=data["uri"],
            width=int(data["width"]) if data.get("width") else None,
            height=int(data["height"]) if data.get("height") else None,
        )

    @classmethod
    def _from_url(cls, data):
        return cls(
            url=data["url"],
            width=int(data["width"]) if data.get("width") else None,
            height=int(data["height"]) if data.get("height") else None,
        )

    @classmethod
    def _from_uri_or_none(cls, data):
        if data is None:
            return None
        if data.get("uri") is None:
            return None
        return cls._from_uri(data)

    @classmethod
    def _from_url_or_none(cls, data):
        if data is None:
            return None
        if data.get("url") is None:
            return None
        return cls._from_url(data)
