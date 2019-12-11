import attr
import logging
import aenum

log = logging.getLogger("fbchat")

#: Default attrs settings for classes
attrs_default = attr.s(slots=True)  # TODO: Add kw_only=True


class Enum(aenum.Enum):
    """Used internally by ``fbchat`` to support enumerations"""

    def __repr__(self):
        # For documentation:
        return "{}.{}".format(type(self).__name__, self.name)

    @classmethod
    def _extend_if_invalid(cls, value):
        try:
            return cls(value)
        except ValueError:
            log.warning(
                "Failed parsing {.__name__}({!r}). Extending enum.".format(cls, value)
            )
            aenum.extend_enum(cls, "UNKNOWN_{}".format(value).upper(), value)
            return cls(value)


@attr.s(frozen=True, slots=True)  # TODO: Add kw_only=True
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
