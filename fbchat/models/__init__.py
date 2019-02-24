# -*- coding: UTF-8 -*-

from __future__ import unicode_literals
import aenum
from ._exception import FBchatException, FBchatFacebookError, FBchatUserError
from ._thread import Thread
from ._user import User
from ._group import Group, Room
from ._page import Page
from ._message import Message
from ._attachment import Attachment, UnsentMessage, ShareAttachment
from ._sticker import Sticker
from ._location import LocationAttachment, LiveLocationAttachment


class FileAttachment(Attachment):
    #: Url where you can download the file
    url = None
    #: Size of the file in bytes
    size = None
    #: Name of the file
    name = None
    #: Whether Facebook determines that this file may be harmful
    is_malicious = None

    def __init__(self, url=None, size=None, name=None, is_malicious=None, **kwargs):
        """Represents a file that has been sent as a Facebook attachment"""
        super(FileAttachment, self).__init__(**kwargs)
        self.url = url
        self.size = size
        self.name = name
        self.is_malicious = is_malicious


class AudioAttachment(Attachment):
    #: Name of the file
    filename = None
    #: Url of the audio file
    url = None
    #: Duration of the audioclip in milliseconds
    duration = None
    #: Audio type
    audio_type = None

    def __init__(
        self, filename=None, url=None, duration=None, audio_type=None, **kwargs
    ):
        """Represents an audio file that has been sent as a Facebook attachment"""
        super(AudioAttachment, self).__init__(**kwargs)
        self.filename = filename
        self.url = url
        self.duration = duration
        self.audio_type = audio_type


class ImageAttachment(Attachment):
    #: The extension of the original image (eg. 'png')
    original_extension = None
    #: Width of original image
    width = None
    #: Height of original image
    height = None

    #: Whether the image is animated
    is_animated = None

    #: URL to a thumbnail of the image
    thumbnail_url = None

    #: URL to a medium preview of the image
    preview_url = None
    #: Width of the medium preview image
    preview_width = None
    #: Height of the medium preview image
    preview_height = None

    #: URL to a large preview of the image
    large_preview_url = None
    #: Width of the large preview image
    large_preview_width = None
    #: Height of the large preview image
    large_preview_height = None

    #: URL to an animated preview of the image (eg. for gifs)
    animated_preview_url = None
    #: Width of the animated preview image
    animated_preview_width = None
    #: Height of the animated preview image
    animated_preview_height = None

    def __init__(
        self,
        original_extension=None,
        width=None,
        height=None,
        is_animated=None,
        thumbnail_url=None,
        preview=None,
        large_preview=None,
        animated_preview=None,
        **kwargs
    ):
        """
        Represents an image that has been sent as a Facebook attachment
        To retrieve the full image url, use: :func:`fbchat.Client.fetchImageUrl`,
        and pass it the uid of the image attachment
        """
        super(ImageAttachment, self).__init__(**kwargs)
        self.original_extension = original_extension
        if width is not None:
            width = int(width)
        self.width = width
        if height is not None:
            height = int(height)
        self.height = height
        self.is_animated = is_animated
        self.thumbnail_url = thumbnail_url

        if preview is None:
            preview = {}
        self.preview_url = preview.get("uri")
        self.preview_width = preview.get("width")
        self.preview_height = preview.get("height")

        if large_preview is None:
            large_preview = {}
        self.large_preview_url = large_preview.get("uri")
        self.large_preview_width = large_preview.get("width")
        self.large_preview_height = large_preview.get("height")

        if animated_preview is None:
            animated_preview = {}
        self.animated_preview_url = animated_preview.get("uri")
        self.animated_preview_width = animated_preview.get("width")
        self.animated_preview_height = animated_preview.get("height")


class VideoAttachment(Attachment):
    #: Size of the original video in bytes
    size = None
    #: Width of original video
    width = None
    #: Height of original video
    height = None
    #: Length of video in milliseconds
    duration = None
    #: URL to very compressed preview video
    preview_url = None

    #: URL to a small preview image of the video
    small_image_url = None
    #: Width of the small preview image
    small_image_width = None
    #: Height of the small preview image
    small_image_height = None

    #: URL to a medium preview image of the video
    medium_image_url = None
    #: Width of the medium preview image
    medium_image_width = None
    #: Height of the medium preview image
    medium_image_height = None

    #: URL to a large preview image of the video
    large_image_url = None
    #: Width of the large preview image
    large_image_width = None
    #: Height of the large preview image
    large_image_height = None

    def __init__(
        self,
        size=None,
        width=None,
        height=None,
        duration=None,
        preview_url=None,
        small_image=None,
        medium_image=None,
        large_image=None,
        **kwargs
    ):
        """Represents a video that has been sent as a Facebook attachment"""
        super(VideoAttachment, self).__init__(**kwargs)
        self.size = size
        self.width = width
        self.height = height
        self.duration = duration
        self.preview_url = preview_url

        if small_image is None:
            small_image = {}
        self.small_image_url = small_image.get("uri")
        self.small_image_width = small_image.get("width")
        self.small_image_height = small_image.get("height")

        if medium_image is None:
            medium_image = {}
        self.medium_image_url = medium_image.get("uri")
        self.medium_image_width = medium_image.get("width")
        self.medium_image_height = medium_image.get("height")

        if large_image is None:
            large_image = {}
        self.large_image_url = large_image.get("uri")
        self.large_image_width = large_image.get("width")
        self.large_image_height = large_image.get("height")


class Mention(object):
    #: The thread ID the mention is pointing at
    thread_id = None
    #: The character where the mention starts
    offset = None
    #: The length of the mention
    length = None

    def __init__(self, thread_id, offset=0, length=10):
        """Represents a @mention"""
        self.thread_id = thread_id
        self.offset = offset
        self.length = length

    def __repr__(self):
        return self.__unicode__()

    def __unicode__(self):
        return "<Mention {}: offset={} length={}>".format(
            self.thread_id, self.offset, self.length
        )


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
