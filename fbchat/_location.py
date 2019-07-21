# -*- coding: UTF-8 -*-
from __future__ import unicode_literals

import attr
from ._attachment import Attachment
from . import _util


@attr.s(cmp=False)
class LocationAttachment(Attachment):
    """Represents a user location.

    Latitude and longitude OR address is provided by Facebook.
    """

    #: Latitude of the location
    latitude = attr.ib(None)
    #: Longitude of the location
    longitude = attr.ib(None)
    #: URL of image showing the map of the location
    image_url = attr.ib(None, init=False)
    #: Width of the image
    image_width = attr.ib(None, init=False)
    #: Height of the image
    image_height = attr.ib(None, init=False)
    #: URL to Bing maps with the location
    url = attr.ib(None, init=False)
    # Address of the location
    address = attr.ib(None)

    # Put here for backwards compatibility, so that the init argument order is preserved
    uid = attr.ib(None)

    @classmethod
    def _from_graphql(cls, data):
        url = data.get("url")
        address = _util.get_url_parameter(_util.get_url_parameter(url, "u"), "where1")
        try:
            latitude, longitude = [float(x) for x in address.split(", ")]
            address = None
        except ValueError:
            latitude, longitude = None, None
        rtn = cls(
            uid=int(data["deduplication_key"]),
            latitude=latitude,
            longitude=longitude,
            address=address,
        )
        media = data.get("media")
        if media and media.get("image"):
            image = media["image"]
            rtn.image_url = image.get("uri")
            rtn.image_width = image.get("width")
            rtn.image_height = image.get("height")
        rtn.url = url
        return rtn


@attr.s(cmp=False, init=False)
class LiveLocationAttachment(LocationAttachment):
    """Represents a live user location."""

    #: Name of the location
    name = attr.ib(None)
    #: Timestamp when live location expires
    expiration_time = attr.ib(None)
    #: True if live location is expired
    is_expired = attr.ib(None)

    def __init__(self, name=None, expiration_time=None, is_expired=None, **kwargs):
        super(LiveLocationAttachment, self).__init__(**kwargs)
        self.expiration_time = expiration_time
        self.is_expired = is_expired

    @classmethod
    def _from_pull(cls, data):
        return cls(
            uid=data["id"],
            latitude=data["coordinate"]["latitude"] / (10 ** 8)
            if not data.get("stopReason")
            else None,
            longitude=data["coordinate"]["longitude"] / (10 ** 8)
            if not data.get("stopReason")
            else None,
            name=data.get("locationTitle"),
            expiration_time=data["expirationTime"],
            is_expired=bool(data.get("stopReason")),
        )

    @classmethod
    def _from_graphql(cls, data):
        target = data["target"]
        rtn = cls(
            uid=int(target["live_location_id"]),
            latitude=target["coordinate"]["latitude"]
            if target.get("coordinate")
            else None,
            longitude=target["coordinate"]["longitude"]
            if target.get("coordinate")
            else None,
            name=data["title_with_entities"]["text"],
            expiration_time=target.get("expiration_time"),
            is_expired=target.get("is_expired"),
        )
        media = data.get("media")
        if media and media.get("image"):
            image = media["image"]
            rtn.image_url = image.get("uri")
            rtn.image_width = image.get("width")
            rtn.image_height = image.get("height")
        rtn.url = data.get("url")
        return rtn
