# -*- coding: UTF-8 -*-

from __future__ import unicode_literals
import enum

class Thread(object):
    #: The unique identifier of the user. Can be used a `thread_id`. See :ref:`intro_threads` for more info
    id = None
    #: Specifies the type of thread. Uses ThreadType
    type = None
    #: The thread's picture
    photo = None
    #: The name of the thread
    name = None

    def __init__(self, _type, _id, photo=None, name=None):
        """Represents a Facebook thread"""
        self.id = str(_id)
        self.type = _type
        self.photo = photo
        self.name = name

    def __repr__(self):
        return self.__unicode__()

    def __unicode__(self):
        return '<{} {} ({})>'.format(self.type.name, self.name, self.id)


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

    def __init__(self, _id, url=None, first_name=None, last_name=None, is_friend=None, gender=None, **kwargs):
        """Represents a Facebook user. Inherits `Thread`"""
        super(User, self).__init__(ThreadType.USER, _id, **kwargs)
        self.url = url
        self.first_name = first_name
        self.last_name = last_name
        self.is_friend = is_friend
        self.gender = gender


class Group(Thread):
    def __init__(self, _id, **kwargs):
        """Represents a Facebook group. Inherits `Thread`"""
        super(Group, self).__init__(ThreadType.GROUP, _id, **kwargs)


class Page(Thread):
    #: The page's custom url
    url = None
    #: The name of the page's location city
    city = None
    #: Amount of likes the page has
    likees = None
    #: Some extra information about the page
    sub_text = None

    def __init__(self, _id, url=None, city=None, likees=None, sub_text=None, **kwargs):
        """Represents a Facebook page. Inherits `Thread`"""
        super(Page, self).__init__(ThreadType.PAGE, _id, **kwargs)
        self.url = url
        self.city = city
        self.likees = likees
        self.sub_text = sub_text


class Message(object):
    """Represents a message. Currently just acts as a dict"""
    def __init__(self, **entries):
        self.__dict__.update(entries)

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
