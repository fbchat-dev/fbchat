"""Facebook Chat (Messenger) for Python

:copyright: (c) 2015 - 2019 by Taehoon Kim
:license: BSD 3-Clause, see LICENSE for more details.
"""

import logging as _logging

# Set default logging handler to avoid "No handler found" warnings.
_logging.getLogger(__name__).addHandler(_logging.NullHandler())

# The order of these is somewhat significant, e.g. User has to be imported after Thread!
from . import _core, _util
from ._core import Image
from ._exception import (
    FacebookError,
    HTTPError,
    ParseError,
    ExternalError,
    InvalidParameters,
    NotLoggedIn,
    PleaseRefresh,
)
from ._session import Session
from ._thread import ThreadLocation, ThreadABC, Thread
from ._user import User, UserData, ActiveStatus
from ._group import Group, GroupData
from ._page import Page, PageData
from ._message import EmojiSize, Mention, Message
from ._attachment import Attachment, UnsentMessage, ShareAttachment
from ._sticker import Sticker
from ._location import LocationAttachment, LiveLocationAttachment
from ._file import FileAttachment, AudioAttachment, ImageAttachment, VideoAttachment
from ._quick_reply import (
    QuickReply,
    QuickReplyText,
    QuickReplyLocation,
    QuickReplyPhoneNumber,
    QuickReplyEmail,
)
from ._poll import Poll, PollOption
from ._plan import GuestStatus, Plan, PlanData

from ._client import Client

__title__ = "fbchat"
__version__ = "1.8.1"
__description__ = "Facebook Chat (Messenger) for Python"

__copyright__ = "Copyright 2015 - 2019 by Taehoon Kim"
__license__ = "BSD 3-Clause"

__author__ = "Taehoon Kim; Moreels Pieter-Jan; Mads Marquart"
__email__ = "carpedm20@gmail.com"

__all__ = ("Session", "Client")
