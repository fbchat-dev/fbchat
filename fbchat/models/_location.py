# -*- coding: UTF-8 -*-
from __future__ import unicode_literals


class LocationAttachment(Attachment):
    """Latitude and longitude OR address is provided by Facebook"""

    #: Latitude of the location
    latitude = None
    #: Longitude of the location
    longitude = None
    #: URL of image showing the map of the location
    image_url = None
    #: Width of the image
    image_width = None
    #: Height of the image
    image_height = None
    #: URL to Bing maps with the location
    url = None
    # Address of the location
    address = None

    def __init__(self, latitude=None, longitude=None, address=None, **kwargs):
        """Represents a user location"""
        super(LocationAttachment, self).__init__(**kwargs)
        self.latitude = latitude
        self.longitude = longitude
        self.address = address


class LiveLocationAttachment(LocationAttachment):
    #: Name of the location
    name = None
    #: Timestamp when live location expires
    expiration_time = None
    #: True if live location is expired
    is_expired = None

    def __init__(self, name=None, expiration_time=None, is_expired=None, **kwargs):
        """Represents a live user location"""
        super(LiveLocationAttachment, self).__init__(**kwargs)
        self.expiration_time = expiration_time
        self.is_expired = is_expired
