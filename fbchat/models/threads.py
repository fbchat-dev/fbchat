# -*- coding: UTF-8 -*-

from __future__ import unicode_literals

import attr

from datetime import datetime
from typing import Dict, List, Set, Union


@attr.s(slots=True)
class Thread(object):
    """Represents a Facebook chat-thread"""

    #: The unique identifier of the thread
    id = attr.ib(type=int, converter=int)
    #: The name of the thread
    name = attr.ib(None, type=str)
    #: When the thread was last updated
    last_activity = attr.ib(None, type=datetime)
    #: A url to the thread's thumbnail/profile picture
    image = attr.ib(None, type=str)
    #: Number of `Message`\s in the thread
    message_count = attr.ib(None, type=int)
    #: `User`\s and `Page`\s, mapped to their nicknames
    nicknames = attr.ib(factory=dict)  # type: Dict[Union[User, Page], str]
    #: The thread colour
    colour = attr.ib(None, type=str)
    #: The thread's default emoji
    emoji = attr.ib(None, type=str)

    _events = attr.ib(factory=list)  # type: List[Event]

    def __eq__(self, other):
        return isinstance(other, Thread) and self.id == other.id

    def __ne__(self, other):
        return not self.__eq__(other)

    @attr.s(slots=True, repr_ns="Thread")
    class Colour(object):
        """Used to specify thread colours"""

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

    def to_send(self):
        return {"other_user_fbid": self.id}


@attr.s(slots=True)
class User(Thread):
    """Represents a Facebook user and the thread between that user and the client"""

    #: The user's first name
    first_name = attr.ib(None, type=str)
    #: The user's last name
    last_name = attr.ib(None, type=str)
    #: Whether the user and the client are friends
    is_friend = attr.ib(None, type=bool)
    #: The user's gender
    gender = attr.ib(None, type=str)
    #: Between 0 and 1. How close the client is to the user
    affinity = attr.ib(None, type=float)


@attr.s(slots=True)
class Group(Thread):
    """Represents a group-thread"""

    #: `User`\s, denoting the thread's participants
    participants = attr.ib(type=Set[User], factory=set)
    #: Set containing `User`\s, denoting the group's admins
    admins = attr.ib(type=Set[User], factory=set)
    #: Whether users need approval to join
    approval_mode = attr.ib(None, type=bool)
    #: Set containing `User`\s requesting to join the group
    approval_requests = attr.ib(type=Set[User], factory=set)

    def to_send(self):
        return {"thread_fbid": self.id}


@attr.s(slots=True)
class Page(Thread):
    """Represents a Facebook page

    TODO: The attributes on this class
    """

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
