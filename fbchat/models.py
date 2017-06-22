# -*- coding: UTF-8 -*-

from __future__ import unicode_literals
import enum


class Thread(object):
    #: The unique identifier of the thread. Can be used a `thread_id`. See :ref:`intro_threads` for more info
    uid = str
    #: Specifies the type of thread. Can be used a `thread_type`. See :ref:`intro_threads` for more info
    type = None
    #: The thread's picture
    photo = str
    #: The name of the thread
    name = str

    def __init__(self, _type, uid, photo=None, name=None):
        """Represents a Facebook thread"""
        self.uid = str(uid)
        self.type = _type
        self.photo = photo
        self.name = name

    def __repr__(self):
        return self.__unicode__()

    def __unicode__(self):
        return '<{} {} ({})>'.format(self.type.name, self.name, self.uid)


class User(Thread):
    #: The profile url
    url = str
    #: The users first name
    first_name = str
    #: The users last name
    last_name = str
    #: Whether the user and the client are friends
    is_friend = bool
    #: The user's gender
    gender = str
    #: From 0 to 1. How close the client is to the user
    affinity = float

    def __init__(self, uid, url=None, first_name=None, last_name=None, is_friend=None, gender=None, affinity=None, **kwargs):
        """Represents a Facebook user. Inherits `Thread`"""
        super(User, self).__init__(ThreadType.USER, uid, **kwargs)
        self.url = url
        self.first_name = first_name
        self.last_name = last_name
        self.is_friend = is_friend
        self.gender = gender
        self.affinity = affinity


class Group(Thread):
    #: List of the group thread's participant user IDs
    participants = list

    def __init__(self, uid, participants=[], **kwargs):
        """Represents a Facebook group. Inherits `Thread`"""
        super(Group, self).__init__(ThreadType.GROUP, uid, **kwargs)
        self.participants = participants


class Page(Thread):
    #: The page's custom url
    url = str
    #: The name of the page's location city
    city = str
    #: Amount of likes the page has
    likes = int
    #: Some extra information about the page
    sub_title = str
    #: The page's category
    category = str

    def __init__(self, uid, url=None, city=None, likes=None, sub_title=None, category=None, **kwargs):
        """Represents a Facebook page. Inherits `Thread`"""
        super(Page, self).__init__(ThreadType.PAGE, uid, **kwargs)
        self.url = url
        self.city = city
        self.likes = likes
        self.sub_title = sub_title
        self.category = category


class Message(object):
    #: The message ID
    uid = str
    #: ID of the sender
    author = int
    #: Timestamp of when the message was sent
    timestamp = str
    #: Whether the message is read
    is_read = bool
    #: A list of message reactions
    reactions = list
    #: The actual message
    text = str
    #: A list of :class:`Mention` objects
    mentions = list
    #: An ID of a sent sticker
    sticker = str
    #: A list of attachments
    attachments = list

    def __init__(self, uid, author=None, timestamp=None, is_read=None, reactions=[], text=None, mentions=[], sticker=None, attachments=[]):
        """Represents a Facebook message"""
        self.uid = uid
        self.author = author
        self.timestamp = timestamp
        self.is_read = is_read
        self.reactions = reactions
        self.text = text
        self.mentions = mentions
        self.sticker = sticker
        self.attachments = attachments


class Mention(object):
    #: The user ID the mention is pointing at
    user_id = str
    #: The character where the mention starts
    offset = int
    #: The length of the mention
    length = int

    def __init__(self, user_id, offset=0, length=10):
        """Represents a @mention"""
        self.user_id = user_id
        self.offset = offset
        self.length = length

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

LIKES = {
    'large': EmojiSize.LARGE,
    'medium': EmojiSize.MEDIUM,
    'small': EmojiSize.SMALL,
    'l': EmojiSize.LARGE,
    'm': EmojiSize.MEDIUM,
    's': EmojiSize.SMALL
}

MessageReactionFix = {
    '😍': ('0001f60d', '%F0%9F%98%8D'),
    '😆': ('0001f606', '%F0%9F%98%86'),
    '😮': ('0001f62e', '%F0%9F%98%AE'),
    '😢': ('0001f622', '%F0%9F%98%A2'),
    '😠': ('0001f620', '%F0%9F%98%A0'),
    '👍': ('0001f44d', '%F0%9F%91%8D'),
    '👎': ('0001f44e', '%F0%9F%91%8E')
}
