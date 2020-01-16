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
    GraphQLError,
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

from ._event_common import Event, UnknownEvent, ThreadEvent

from ._client import Client

__title__ = "fbchat"
__version__ = "1.9.4"
__description__ = "Facebook Chat (Messenger) for Python"

__copyright__ = "Copyright 2015 - 2019 by Taehoon Kim"
__license__ = "BSD 3-Clause"

__author__ = "Taehoon Kim; Moreels Pieter-Jan; Mads Marquart"
__email__ = "carpedm20@gmail.com"

__all__ = ("Session", "Client")

# Everything below is taken from the excellent trio project:


def fixup_module_metadata(namespace):
    def fix_one(qualname, name, obj):
        mod = getattr(obj, "__module__", None)
        if mod is not None and mod.startswith("fbchat."):
            obj.__module__ = "fbchat"
            # Modules, unlike everything else in Python, put fully-qualitied
            # names into their __name__ attribute. We check for "." to avoid
            # rewriting these.
            if hasattr(obj, "__name__") and "." not in obj.__name__:
                obj.__name__ = name
                obj.__qualname__ = qualname
            if isinstance(obj, type):
                # Fix methods
                for attr_name, attr_value in obj.__dict__.items():
                    fix_one(objname + "." + attr_name, attr_name, attr_value)

    for objname, obj in namespace.items():
        if not objname.startswith("_"):  # ignore private attributes
            fix_one(objname, objname, obj)


# Having the public path in .__module__ attributes is important for:
# - exception names in printed tracebacks
# - sphinx :show-inheritance:
# - deprecation warnings
# - pickle
# - probably other stuff
fixup_module_metadata(globals())
del fixup_module_metadata
