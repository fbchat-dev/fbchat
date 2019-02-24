# -*- coding: UTF-8 -*-
from __future__ import unicode_literals

import attr
from ._attachment import Attachment


@attr.s(cmp=False)
class LocationAttachment(Attachment):
    """Represents a user location

    Latitude and longitude OR address is provided by Facebook
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


@attr.s(cmp=False, init=False)
class LiveLocationAttachment(LocationAttachment):
    """Represents a live user location"""

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
