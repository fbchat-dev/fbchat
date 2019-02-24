# -*- coding: UTF-8 -*-
from __future__ import unicode_literals

from ._attachment import Attachment


class QuickReply(object):
    """Represents a quick reply"""

    #: Payload of the quick reply
    payload = None
    #: External payload for responses
    external_payload = None
    #: Additional data
    data = None
    #: Whether it's a response for a quick reply
    is_response = None

    def __init__(self, payload=None, data=None, is_response=False):
        self.payload = payload
        self.data = data
        self.is_response = is_response

    def __repr__(self):
        return self.__unicode__()

    def __unicode__(self):
        return "<{}: payload={!r}>".format(self.__class__.__name__, self.payload)


class QuickReplyText(QuickReply):
    """Represents a text quick reply"""

    #: Title of the quick reply
    title = None
    #: URL of the quick reply image (optional)
    image_url = None
    #: Type of the quick reply
    _type = "text"

    def __init__(self, title=None, image_url=None, **kwargs):
        super(QuickReplyText, self).__init__(**kwargs)
        self.title = title
        self.image_url = image_url


class QuickReplyLocation(QuickReply):
    """Represents a location quick reply (Doesn't work on mobile)"""

    #: Type of the quick reply
    _type = "location"

    def __init__(self, **kwargs):
        super(QuickReplyLocation, self).__init__(**kwargs)
        self.is_response = False


class QuickReplyPhoneNumber(QuickReply):
    """Represents a phone number quick reply (Doesn't work on mobile)"""

    #: URL of the quick reply image (optional)
    image_url = None
    #: Type of the quick reply
    _type = "user_phone_number"

    def __init__(self, image_url=None, **kwargs):
        super(QuickReplyPhoneNumber, self).__init__(**kwargs)
        self.image_url = image_url


class QuickReplyEmail(QuickReply):
    """Represents an email quick reply (Doesn't work on mobile)"""

    #: URL of the quick reply image (optional)
    image_url = None
    #: Type of the quick reply
    _type = "user_email"

    def __init__(self, image_url=None, **kwargs):
        super(QuickReplyEmail, self).__init__(**kwargs)
        self.image_url = image_url
