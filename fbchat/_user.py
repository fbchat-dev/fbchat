# -*- coding: UTF-8 -*-
from __future__ import unicode_literals

from ._core import Enum
from ._thread import ThreadType, Thread


class TypingStatus(Enum):
    """Used to specify whether the user is typing or has stopped typing"""

    STOPPED = 0
    TYPING = 1


class User(Thread):
    """Represents a Facebook user. Inherits `Thread`"""

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

    def __init__(
        self,
        uid,
        url=None,
        first_name=None,
        last_name=None,
        is_friend=None,
        gender=None,
        affinity=None,
        nickname=None,
        own_nickname=None,
        color=None,
        emoji=None,
        **kwargs
    ):
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
