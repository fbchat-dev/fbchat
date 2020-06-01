import attr
from . import Attachment
from .._common import attrs_default

from typing import Any, Optional


@attrs_default
class QuickReply:
    """Represents a quick reply."""

    #: Payload of the quick reply
    payload = attr.ib(None, type=Any)
    #: External payload for responses
    external_payload = attr.ib(None, type=Any)
    #: Additional data
    data = attr.ib(None, type=Any)
    #: Whether it's a response for a quick reply
    is_response = attr.ib(False, type=bool)


@attrs_default
class QuickReplyText(QuickReply):
    """Represents a text quick reply."""

    #: Title of the quick reply
    title = attr.ib(None, type=Optional[str])
    #: URL of the quick reply image
    image_url = attr.ib(None, type=Optional[str])
    #: Type of the quick reply
    _type = "text"


@attrs_default
class QuickReplyLocation(QuickReply):
    """Represents a location quick reply (Doesn't work on mobile)."""

    #: Type of the quick reply
    _type = "location"


@attrs_default
class QuickReplyPhoneNumber(QuickReply):
    """Represents a phone number quick reply (Doesn't work on mobile)."""

    #: URL of the quick reply image
    image_url = attr.ib(None, type=Optional[str])
    #: Type of the quick reply
    _type = "user_phone_number"


@attrs_default
class QuickReplyEmail(QuickReply):
    """Represents an email quick reply (Doesn't work on mobile)."""

    #: URL of the quick reply image
    image_url = attr.ib(None, type=Optional[str])
    #: Type of the quick reply
    _type = "user_email"


def graphql_to_quick_reply(q, is_response=False):
    data = dict()
    _type = q.get("content_type").lower()
    if q.get("payload"):
        data["payload"] = q["payload"]
    if q.get("data"):
        data["data"] = q["data"]
    if q.get("image_url") and _type is not QuickReplyLocation._type:
        data["image_url"] = q["image_url"]
    data["is_response"] = is_response
    if _type == QuickReplyText._type:
        if q.get("title") is not None:
            data["title"] = q["title"]
        rtn = QuickReplyText(**data)
    elif _type == QuickReplyLocation._type:
        rtn = QuickReplyLocation(**data)
    elif _type == QuickReplyPhoneNumber._type:
        rtn = QuickReplyPhoneNumber(**data)
    elif _type == QuickReplyEmail._type:
        rtn = QuickReplyEmail(**data)
    return rtn
