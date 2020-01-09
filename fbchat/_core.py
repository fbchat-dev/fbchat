import sys
import attr
import logging

log = logging.getLogger("fbchat")

# Enable kw_only if the python version supports it
kw_only = sys.version_info[:2] > (3, 5)

#: Default attrs settings for classes
attrs_default = attr.s(slots=True, kw_only=kw_only)


# Frozen, so that it can be used in sets
@attr.s(frozen=True, slots=True, kw_only=kw_only)
class Image:
    #: URL to the image
    url = attr.ib(type=str)
    #: Width of the image
    width = attr.ib(None, type=int)
    #: Height of the image
    height = attr.ib(None, type=int)

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
