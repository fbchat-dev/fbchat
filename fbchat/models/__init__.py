# -*- coding: UTF-8 -*-

from __future__ import unicode_literals
import aenum
from ._exception import FBchatException, FBchatFacebookError, FBchatUserError
from ._thread import Thread
from ._user import User
from ._group import Group, Room
from ._page import Page
from ._message import Mention, Message
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


class Poll(object):
    #: ID of the poll
    uid = None
    #: Title of the poll
    title = None
    #: List of :class:`PollOption`, can be fetched with :func:`fbchat.Client.fetchPollOptions`
    options = None
    #: Options count
    options_count = None

    def __init__(self, title, options):
        """Represents a poll"""
        self.title = title
        self.options = options

    def __repr__(self):
        return self.__unicode__()

    def __unicode__(self):
        return "<Poll ({}): {} options={}>".format(
            self.uid, repr(self.title), self.options
        )


class PollOption(object):
    #: ID of the poll option
    uid = None
    #: Text of the poll option
    text = None
    #: Whether vote when creating or client voted
    vote = None
    #: ID of the users who voted for this poll option
    voters = None
    #: Votes count
    votes_count = None

    def __init__(self, text, vote=False):
        """Represents a poll option"""
        self.text = text
        self.vote = vote

    def __repr__(self):
        return self.__unicode__()

    def __unicode__(self):
        return "<PollOption ({}): {} voters={}>".format(
            self.uid, repr(self.text), self.voters
        )


class Plan(object):
    #: ID of the plan
    uid = None
    #: Plan time (unix time stamp), only precise down to the minute
    time = None
    #: Plan title
    title = None
    #: Plan location name
    location = None
    #: Plan location ID
    location_id = None
    #: ID of the plan creator
    author_id = None
    #: List of the people IDs who will take part in the plan
    going = None
    #: List of the people IDs who won't take part in the plan
    declined = None
    #: List of the people IDs who are invited to the plan
    invited = None

    def __init__(self, time, title, location=None, location_id=None):
        """Represents a plan"""
        self.time = int(time)
        self.title = title
        self.location = location or ""
        self.location_id = location_id or ""
        self.author_id = None
        self.going = []
        self.declined = []
        self.invited = []

    def __repr__(self):
        return self.__unicode__()

    def __unicode__(self):
        return "<Plan ({}): {} time={}, location={}, location_id={}>".format(
            self.uid,
            repr(self.title),
            self.time,
            repr(self.location),
            repr(self.location_id),
        )


class ActiveStatus(object):
    #: Whether the user is active now
    active = None
    #: Timestamp when the user was last active
    last_active = None
    #: Whether the user is playing Messenger game now
    in_game = None

    def __init__(self, active=None, last_active=None, in_game=None):
        self.active = active
        self.last_active = last_active
        self.in_game = in_game

    def __repr__(self):
        return self.__unicode__()

    def __unicode__(self):
        return "<ActiveStatus: active={} last_active={} in_game={}>".format(
            self.active, self.last_active, self.in_game
        )


class Enum(aenum.Enum):
    """Used internally by fbchat to support enumerations"""

    def __repr__(self):
        # For documentation:
        return "{}.{}".format(type(self).__name__, self.name)


class ThreadType(Enum):
    """Used to specify what type of Facebook thread is being used. See :ref:`intro_threads` for more info"""

    USER = 1
    GROUP = 2
    ROOM = 2
    PAGE = 3


class ThreadLocation(Enum):
    """Used to specify where a thread is located (inbox, pending, archived, other)."""

    INBOX = "INBOX"
    PENDING = "PENDING"
    ARCHIVED = "ARCHIVED"
    OTHER = "OTHER"


class TypingStatus(Enum):
    """Used to specify whether the user is typing or has stopped typing"""

    STOPPED = 0
    TYPING = 1


class EmojiSize(Enum):
    """Used to specify the size of a sent emoji"""

    LARGE = "369239383222810"
    MEDIUM = "369239343222814"
    SMALL = "369239263222822"


class ThreadColor(Enum):
    """Used to specify a thread colors"""

    MESSENGER_BLUE = "#0084ff"
    VIKING = "#44bec7"
    GOLDEN_POPPY = "#ffc300"
    RADICAL_RED = "#fa3c4c"
    SHOCKING = "#d696bb"
    PICTON_BLUE = "#6699cc"
    FREE_SPEECH_GREEN = "#13cf13"
    PUMPKIN = "#ff7e29"
    LIGHT_CORAL = "#e68585"
    MEDIUM_SLATE_BLUE = "#7646ff"
    DEEP_SKY_BLUE = "#20cef5"
    FERN = "#67b868"
    CAMEO = "#d4a88c"
    BRILLIANT_ROSE = "#ff5ca1"
    BILOBA_FLOWER = "#a695c7"


class MessageReaction(Enum):
    """Used to specify a message reaction"""

    LOVE = "😍"
    SMILE = "😆"
    WOW = "😮"
    SAD = "😢"
    ANGRY = "😠"
    YES = "👍"
    NO = "👎"
