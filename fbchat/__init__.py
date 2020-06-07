"""Facebook Messenger for Python.

Copyright:
    (c) 2015 - 2018 by Taehoon Kim
    (c) 2018 - 2020 by Mads Marquart

License:
    BSD 3-Clause, see LICENSE for more details.
"""

import logging as _logging

# Set default logging handler to avoid "No handler found" warnings.
_logging.getLogger(__name__).addHandler(_logging.NullHandler())

# The order of these is somewhat significant, e.g. User has to be imported after Thread!
from . import _common, _util
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
from ._threads import (
    ThreadABC,
    Thread,
    User,
    UserData,
    Group,
    GroupData,
    Page,
    PageData,
)

# Models
from ._models import (
    Image,
    ThreadLocation,
    ActiveStatus,
    Attachment,
    UnsentMessage,
    ShareAttachment,
    LocationAttachment,
    LiveLocationAttachment,
    Sticker,
    FileAttachment,
    AudioAttachment,
    ImageAttachment,
    VideoAttachment,
    Poll,
    PollOption,
    GuestStatus,
    Plan,
    PlanData,
    QuickReply,
    QuickReplyText,
    QuickReplyLocation,
    QuickReplyPhoneNumber,
    QuickReplyEmail,
    EmojiSize,
    Mention,
    Message,
    MessageSnippet,
    MessageData,
)

# Events
from ._events import (
    # _common
    Event,
    UnknownEvent,
    ThreadEvent,
    Connect,
    Disconnect,
    # _client_payload
    ReactionEvent,
    UserStatusEvent,
    LiveLocationEvent,
    UnsendEvent,
    MessageReplyEvent,
    # _delta_class
    PeopleAdded,
    PersonRemoved,
    TitleSet,
    UnfetchedThreadEvent,
    MessagesDelivered,
    ThreadsRead,
    MessageEvent,
    ThreadFolder,
    # _delta_type
    ColorSet,
    EmojiSet,
    NicknameSet,
    AdminsAdded,
    AdminsRemoved,
    ApprovalModeSet,
    CallStarted,
    CallEnded,
    CallJoined,
    PollCreated,
    PollVoted,
    PlanCreated,
    PlanEnded,
    PlanEdited,
    PlanDeleted,
    PlanResponded,
    # __init__
    Typing,
    FriendRequest,
    Presence,
)
from ._listen import Listener

from ._client import Client

__version__ = "2.0.0a4"

__all__ = ("Session", "Listener", "Client")


from . import _fix_module_metadata

_fix_module_metadata.fixup_module_metadata(globals())
del _fix_module_metadata
