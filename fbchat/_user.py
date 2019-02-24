# -*- coding: UTF-8 -*-
from __future__ import unicode_literals

import attr
from ._core import Enum
from ._thread import ThreadType, Thread


class TypingStatus(Enum):
    """Used to specify whether the user is typing or has stopped typing"""

    STOPPED = 0
    TYPING = 1


@attr.s(cmp=False, init=False)
class User(Thread):
    """Represents a Facebook user. Inherits `Thread`"""

    #: The profile url
    url = attr.ib(None)
    #: The users first name
    first_name = attr.ib(None)
    #: The users last name
    last_name = attr.ib(None)
    #: Whether the user and the client are friends
    is_friend = attr.ib(None)
    #: The user's gender
    gender = attr.ib(None)
    #: From 0 to 1. How close the client is to the user
    affinity = attr.ib(None)
    #: The user's nickname
    nickname = attr.ib(None)
    #: The clients nickname, as seen by the user
    own_nickname = attr.ib(None)
    #: A :class:`ThreadColor`. The message color
    color = attr.ib(None)
    #: The default emoji
    emoji = attr.ib(None)

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


@attr.s(cmp=False)
class ActiveStatus(object):
    #: Whether the user is active now
    active = attr.ib(None)
    #: Timestamp when the user was last active
    last_active = attr.ib(None)
    #: Whether the user is playing Messenger game now
    in_game = attr.ib(None)
