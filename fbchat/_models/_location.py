import attr
import datetime
from . import Image, Attachment
from .._common import attrs_default
from .. import _util, _exception

from typing import Optional


@attrs_default
class LocationAttachment(Attachment):
    """Represents a user location.

    Latitude and longitude OR address is provided by Facebook.
    """

    #: Latitude of the location
    latitude = attr.ib(None, type=Optional[float])
    #: Longitude of the location
    longitude = attr.ib(None, type=Optional[float])
    #: Image showing the map of the location
    image = attr.ib(None, type=Optional[Image])
    #: URL to Bing maps with the location
    url = attr.ib(None, type=Optional[str])
    # Address of the location
    address = attr.ib(None, type=Optional[str])

    @classmethod
    def _from_graphql(cls, data):
        url = data.get("url")
        address = _util.get_url_parameter(_util.get_url_parameter(url, "u"), "where1")
        if not address:
            raise _exception.ParseError("Could not find location address", data=data)
        try:
            latitude, longitude = [float(x) for x in address.split(", ")]
            address = None
        except ValueError:
            latitude, longitude = None, None

        return cls(
            id=int(data["deduplication_key"]),
            latitude=latitude,
            longitude=longitude,
            image=Image._from_uri_or_none(data["media"].get("image"))
            if data.get("media")
            else None,
            url=url,
            address=address,
        )


@attrs_default
class LiveLocationAttachment(LocationAttachment):
    """Represents a live user location."""

    #: Name of the location
    name = attr.ib(None, type=Optional[str])
    #: When live location expires
    expires_at = attr.ib(None, type=Optional[datetime.datetime])
    #: True if live location is expired
    is_expired = attr.ib(None, type=Optional[bool])

    @classmethod
    def _from_pull(cls, data):
        return cls(
            id=data["id"],
            latitude=data["coordinate"]["latitude"] / (10 ** 8)
            if not data.get("stopReason")
            else None,
            longitude=data["coordinate"]["longitude"] / (10 ** 8)
            if not data.get("stopReason")
            else None,
            name=data.get("locationTitle"),
            expires_at=_util.millis_to_datetime(data["expirationTime"]),
            is_expired=bool(data.get("stopReason")),
        )

    @classmethod
    def _from_graphql(cls, data):
        target = data["target"]

        image = None
        media = data.get("media")
        if media and media.get("image"):
            image = Image._from_uri(media["image"])

        return cls(
            id=int(target["live_location_id"]),
            latitude=target["coordinate"]["latitude"]
            if target.get("coordinate")
            else None,
            longitude=target["coordinate"]["longitude"]
            if target.get("coordinate")
            else None,
            image=image,
            url=data.get("url"),
            name=data["title_with_entities"]["text"],
            expires_at=_util.seconds_to_datetime(target.get("expiration_time")),
            is_expired=target.get("is_expired"),
        )
