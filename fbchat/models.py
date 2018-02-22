# -*- coding: UTF-8 -*-

from __future__ import unicode_literals
import enum


class FBchatException(Exception):
    """Custom exception thrown by fbchat. All exceptions in the fbchat module inherits this"""

class FBchatFacebookError(FBchatException):
    #: The error code that Facebook returned
    fb_error_code = None
    #: The error message that Facebook returned (In the user's own language)
    fb_error_message = None
    #: The status code that was sent in the http response (eg. 404) (Usually only set if not successful, aka. not 200)
    request_status_code = None
    def __init__(self, message, fb_error_code=None, fb_error_message=None, request_status_code=None):
        super(FBchatFacebookError, self).__init__(message)
        """Thrown by fbchat when Facebook returns an error"""
        self.fb_error_code = str(fb_error_code)
        self.fb_error_message = fb_error_message
        self.request_status_code = request_status_code

class FBchatUserError(FBchatException):
    """Thrown by fbchat when wrong values are entered"""

class Thread(object):
    #: The unique identifier of the thread. Can be used a `thread_id`. See :ref:`intro_threads` for more info
    uid = None
    #: Specifies the type of thread. Can be used a `thread_type`. See :ref:`intro_threads` for more info
    type = None
    #: A url to the thread's picture
    photo = None
    #: The name of the thread
    name = None
    #: Timestamp of last message
    last_message_timestamp = None
    #: Number of messages in the thread
    message_count = None
    def __init__(self, _type, uid, photo=None, name=None, last_message_timestamp=None, message_count=None):
        """Represents a Facebook thread"""
        self.uid = str(uid)
        self.type = _type
        self.photo = photo
        self.name = name
        self.last_message_timestamp = last_message_timestamp
        self.message_count = message_count

    def __repr__(self):
        return self.__unicode__()

    def __unicode__(self):
        return '<{} {} ({})>'.format(self.type.name, self.name, self.uid)


class User(Thread):
    #: The profile url
    url = None
    #: The users first name
    first_name = None
    #: The users last name
    last_name = None
    #: Whether the user and the client are friends
    is_friend = None
    #: The user's gender
    gender = None
    #: From 0 to 1. How close the client is to the user
    affinity = None
    #: The user's nickname
    nickname = None
    #: The clients nickname, as seen by the user
    own_nickname = None
    #: A :class:`ThreadColor`. The message color
    color = None
    #: The default emoji
    emoji = None

    def __init__(self, uid, url=None, first_name=None, last_name=None, is_friend=None, gender=None, affinity=None, nickname=None, own_nickname=None, color=None, emoji=None, **kwargs):
        """Represents a Facebook user. Inherits `Thread`"""
        super(User, self).__init__(ThreadType.USER, uid, **kwargs)
        self.url = url
        self.first_name = first_name
        self.last_name = last_name
        self.is_friend = is_friend
        self.gender = gender
        self.affinity = affinity
        self.nickname = nickname
        self.own_nickname = own_nickname
        self.color = color
        self.emoji = emoji


class Group(Thread):
    #: Unique list (set) of the group thread's participant user IDs
    participants = None
    #: A dict, containing user nicknames mapped to their IDs
    nicknames = None
    #: A :class:`ThreadColor`. The groups's message color
    color = None
    #: The groups's default emoji
    emoji = None

    def __init__(self, uid, participants=None, nicknames=None, color=None, emoji=None, **kwargs):
        """Represents a Facebook group. Inherits `Thread`"""
        super(Group, self).__init__(ThreadType.GROUP, uid, **kwargs)
        if participants is None:
            participants = set()
        self.participants = participants
        if nicknames is None:
            nicknames = []
        self.nicknames = nicknames
        self.color = color
        self.emoji = emoji


class Room(Group):
    # Set containing user IDs of thread admins
    admins = None
    # True if users need approval to join
    approval_mode = None
    # Set containing user IDs requesting to join
    approval_requests = None
    # Link for joining room
    join_link = None
    # True is room is not discoverable
    privacy_mode = None

    def __init__(self, uid, admins=None, approval_mode=None, approval_requests=None, join_link=None, privacy_mode=None, **kwargs):
        """Represents a Facebook room. Inherits `Group`"""
        super(Room, self).__init__(uid, **kwargs)
        self.type = ThreadType.ROOM
        if admins is None:
            admins = set()
        self.admins = admins
        self.approval_mode = approval_mode
        if approval_requests is None:
            approval_requests = set()
        self.approval_requests = approval_requests
        self.join_link = join_link
        self.privacy_mode = privacy_mode


class Page(Thread):
    #: The page's custom url
    url = None
    #: The name of the page's location city
    city = None
    #: Amount of likes the page has
    likes = None
    #: Some extra information about the page
    sub_title = None
    #: The page's category
    category = None

    def __init__(self, uid, url=None, city=None, likes=None, sub_title=None, category=None, **kwargs):
        """Represents a Facebook page. Inherits `Thread`"""
        super(Page, self).__init__(ThreadType.PAGE, uid, **kwargs)
        self.url = url
        self.city = city
        self.likes = likes
        self.sub_title = sub_title
        self.category = category


class Message(object):
    #: The actual message
    text = None
    #: A list of :class:`Mention` objects
    mentions = None
    #: A :class:`EmojiSize`. Size of a sent emoji
    emoji_size = None
    #: The message ID
    uid = None
    #: ID of the sender
    author = None
    #: Timestamp of when the message was sent
    timestamp = None
    #: Whether the message is read
    is_read = None
    #: A dict with user's IDs as keys, and their :class:`MessageReaction` as values
    reactions = None
    #: The actual message
    text = None
    #: A :class:`Sticker`
    sticker = None
    #: A list of attachments
    attachments = None

    def __init__(self, text=None, mentions=None, emoji_size=None, sticker=None, attachments=None):
        """Represents a Facebook message"""
        self.text = text
        if mentions is None:
            mentions = []
        self.mentions = mentions
        self.emoji_size = emoji_size
        self.sticker = sticker
        if attachments is None:
            attachments = []
        self.attachments = attachments
        self.reactions = {}

    def __repr__(self):
        return self.__unicode__()

    def __unicode__(self):
        return '<Message ({}): {}, mentions={} emoji_size={} attachments={}>'.format(self.uid, repr(self.text), self.mentions, self.emoji_size, self.attachments)

class Attachment(object):
    #: The attachment ID
    uid = None

    def __init__(self, uid=None):
        """Represents a Facebook attachment"""
        self.uid = uid

class Sticker(Attachment):
    #: The sticker-pack's ID
    pack = None
    #: Whether the sticker is animated
    is_animated = False

    # If the sticker is animated, the following should be present
    #: URL to a medium spritemap
    medium_sprite_image = None
    #: URL to a large spritemap
    large_sprite_image = None
    #: The amount of frames present in the spritemap pr. row
    frames_per_row = None
    #: The amount of frames present in the spritemap pr. coloumn
    frames_per_col = None
    #: The frame rate the spritemap is intended to be played in
    frame_rate = None

    #: URL to the sticker's image
    url = None
    #: Width of the sticker
    width = None
    #: Height of the sticker
    height = None
    #: The sticker's label/name
    label = None

    def __init__(self, *args, **kwargs):
        """Represents a Facebook sticker that has been sent to a Facebook thread as an attachment"""
        super(Sticker, self).__init__(*args, **kwargs)

class ShareAttachment(Attachment):
    def __init__(self, **kwargs):
        """Represents a shared item (eg. URL) that has been sent as a Facebook attachment - *Currently Incomplete!*"""
        super(ShareAttachment, self).__init__(**kwargs)

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

    def __init__(self, filename=None, url=None, duration=None, audio_type=None, **kwargs):
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

    def __init__(self, original_extension=None, width=None, height=None, is_animated=None, thumbnail_url=None, preview=None, large_preview=None, animated_preview=None, **kwargs):
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
        self.preview_url = preview.get('uri')
        self.preview_width = preview.get('width')
        self.preview_height = preview.get('height')

        if large_preview is None:
            large_preview = {}
        self.large_preview_url = large_preview.get('uri')
        self.large_preview_width = large_preview.get('width')
        self.large_preview_height = large_preview.get('height')

        if animated_preview is None:
            animated_preview = {}
        self.animated_preview_url = animated_preview.get('uri')
        self.animated_preview_width = animated_preview.get('width')
        self.animated_preview_height = animated_preview.get('height')

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

    def __init__(self, size=None, width=None, height=None, duration=None, preview_url=None, small_image=None, medium_image=None, large_image=None, **kwargs):
        """Represents a video that has been sent as a Facebook attachment"""
        super(VideoAttachment, self).__init__(**kwargs)
        self.size = size
        self.width = width
        self.height = height
        self.duration = duration
        self.preview_url = preview_url

        if small_image is None:
            small_image = {}
        self.small_image_url = small_image.get('uri')
        self.small_image_width = small_image.get('width')
        self.small_image_height = small_image.get('height')

        if medium_image is None:
            medium_image = {}
        self.medium_image_url = medium_image.get('uri')
        self.medium_image_width = medium_image.get('width')
        self.medium_image_height = medium_image.get('height')

        if large_image is None:
            large_image = {}
        self.large_image_url = large_image.get('uri')
        self.large_image_width = large_image.get('width')
        self.large_image_height = large_image.get('height')


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
        return '<Mention {}: offset={} length={}>'.format(self.thread_id, self.offset, self.length)

class Enum(enum.Enum):
    """Used internally by fbchat to support enumerations"""
    def __repr__(self):
        # For documentation:
        return '{}.{}'.format(type(self).__name__, self.name)

class ThreadType(Enum):
    """Used to specify what type of Facebook thread is being used. See :ref:`intro_threads` for more info"""
    USER = 1
    GROUP = 2
    PAGE = 3
    ROOM = 4

class ThreadLocation(Enum):
    """Used to specify where a thread is located (inbox, pending, archived, other)."""
    INBOX = 'INBOX'
    PENDING = 'PENDING'
    ARCHIVED = 'ARCHIVED'
    OTHER = 'OTHER'

class TypingStatus(Enum):
    """Used to specify whether the user is typing or has stopped typing"""
    STOPPED = 0
    TYPING = 1

class EmojiSize(Enum):
    """Used to specify the size of a sent emoji"""
    LARGE = '369239383222810'
    MEDIUM = '369239343222814'
    SMALL = '369239263222822'

class ThreadColor(Enum):
    """Used to specify a thread colors"""
    MESSENGER_BLUE = ''
    VIKING = '#44bec7'
    GOLDEN_POPPY = '#ffc300'
    RADICAL_RED = '#fa3c4c'
    SHOCKING = '#d696bb'
    PICTON_BLUE = '#6699cc'
    FREE_SPEECH_GREEN = '#13cf13'
    PUMPKIN = '#ff7e29'
    LIGHT_CORAL = '#e68585'
    MEDIUM_SLATE_BLUE = '#7646ff'
    DEEP_SKY_BLUE = '#20cef5'
    FERN = '#67b868'
    CAMEO = '#d4a88c'
    BRILLIANT_ROSE = '#ff5ca1'
    BILOBA_FLOWER = '#a695c7'

class MessageReaction(Enum):
    """Used to specify a message reaction"""
    LOVE = '😍'
    SMILE = '😆'
    WOW = '😮'
    SAD = '😢'
    ANGRY = '😠'
    YES = '👍'
    NO = '👎'
