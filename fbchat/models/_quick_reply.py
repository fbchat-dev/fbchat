# -*- coding: UTF-8 -*-
from __future__ import unicode_literals


class QuickReply(object):
    #: Payload of the quick reply
    payload = None
    #: External payload for responses
    external_payload = None
    #: Additional data
    data = None
    #: Whether it's a response for a quick reply
    is_response = None

    def __init__(self, payload=None, data=None, is_response=False):
        """Represents a quick reply"""
        self.payload = payload
        self.data = data
        self.is_response = is_response

    def __repr__(self):
        return self.__unicode__()

    def __unicode__(self):
        return "<{}: payload={!r}>".format(self.__class__.__name__, self.payload)


class QuickReplyText(QuickReply):
    #: Title of the quick reply
    title = None
    #: URL of the quick reply image (optional)
    image_url = None
    #: Type of the quick reply
    _type = "text"

    def __init__(self, title=None, image_url=None, **kwargs):
        """Represents a text quick reply"""
        super(QuickReplyText, self).__init__(**kwargs)
        self.title = title
        self.image_url = image_url


class QuickReplyLocation(QuickReply):
    #: Type of the quick reply
    _type = "location"

    def __init__(self, **kwargs):
        """Represents a location quick reply (Doesn't work on mobile)"""
        super(QuickReplyLocation, self).__init__(**kwargs)
        self.is_response = False


class QuickReplyPhoneNumber(QuickReply):
    #: URL of the quick reply image (optional)
    image_url = None
    #: Type of the quick reply
    _type = "user_phone_number"

    def __init__(self, image_url=None, **kwargs):
        """Represents a phone number quick reply (Doesn't work on mobile)"""
        super(QuickReplyPhoneNumber, self).__init__(**kwargs)
        self.image_url = image_url


class QuickReplyEmail(QuickReply):
    #: URL of the quick reply image (optional)
    image_url = None
    #: Type of the quick reply
    _type = "user_email"

    def __init__(self, image_url=None, **kwargs):
        """Represents an email quick reply (Doesn't work on mobile)"""
        super(QuickReplyEmail, self).__init__(**kwargs)
        self.image_url = image_url
