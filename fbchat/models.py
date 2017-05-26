# -*- coding: UTF-8 -*-

from __future__ import unicode_literals
import enum

class User(object):
    """Represents a Facebook User"""

    #: The unique identifier of the user. Can be used a `thread_id`. See :ref:`intro_thread_id` for more info
    uid = None
    #: Currently always set to `user`. Might change in the future
    type = 'user'
    #: The profile picture of the user
    photo = None
    #: The profile url
    url = None
    #: The name of the user
    name = None
    #: Only used by :any:`Client.getUsers`. Each user is assigned a score between 0 and 1, based on how likely it is that they were the person being searched for
    score = None
    #: Dictionary containing raw userdata from when the :class:`User` was created
    data = None

    def __init__(self, data):
        """Represents a Facebook User"""
        if data['type'] != 'user':
            raise Exception("[!] %s <%s> is not a user" % (data['text'], data['path']))
        self.uid = data['uid']
        self.type = data['type']
        self.photo = data['photo']
        self.url = data['path']
        self.name = data['text']
        self.score = float(data['score'])
        self.data = data

    def __repr__(self):
        return self.__unicode__()

    def __unicode__(self):
        return u'<%s %s (%s)>' % (self.type.upper(), self.name, self.url)

    @staticmethod
    def _adaptFromChat(user_in_chat):
        """Adapts user info from chat to User model acceptable initial dict

        :param user_in_chat: user info from chat
        :return: :class:`User` object

        'dir': None,
        'mThumbSrcSmall': None,
        'is_friend': False,
        'is_nonfriend_messenger_contact': True,
        'alternateName': '',
        'i18nGender': 16777216,
        'vanity': '',
        'type': 'friend',
        'searchTokens': ['Voznesenskij', 'Sergej'],
        'thumbSrc': 'https://fb-s-b-a.akamaihd.net/h-ak-xfa1/v/t1.0-1/c9.0.32.32/p32x32/10354686_10150004552801856_220367501106153455_n.jpg?oh=71a87d76d4e4d17615a20c43fb8dbb47&oe=59118CE4&__gda__=1493753268_ae75cef40e9785398e744259ccffd7ff',
        'mThumbSrcLarge': None,
        'firstName': 'Sergej',
        'name': 'Sergej Voznesenskij',
        'uri': 'https://www.facebook.com/profile.php?id=100014812758264',
        'id': '100014812758264',
        'gender': 2
        """

        return {
            'type': 'user',
            'uid': user_in_chat['id'],
            'photo': user_in_chat['thumbSrc'],
            'path': user_in_chat['uri'],
            'text': user_in_chat['name'],
            'score': 1,
            'data': user_in_chat,
        }

class Thread(object):
    def __init__(self, **entries): 
        self.__dict__.update(entries)

class Message(object):
    def __init__(self, **entries):
        self.__dict__.update(entries)

class Enum(enum.Enum):
    """Used internally by fbchat to support enumerations"""
    def __repr__(self):
        # For documentation:
        return '{}.{}'.format(type(self).__name__, self.name)

class ThreadType(Enum):
    """Used to specify what type of Facebook thread is being used. See :ref:`intro_thread_type` for more info"""
    USER = 1
    GROUP = 2

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
