# -*- coding: UTF-8 -*-

import attr

from datetime import datetime
from typing import Dict, List, Set, Union, Optional

from .core import ID, JSON

from . import events


__all__ = ("Thread", "User", "Group", "Page")


@attr.s(slots=True)
class Thread:
    """Represents a Facebook chat-thread"""

    #: The unique identifier of the thread
    id: ID = attr.ib(converter=ID)
    #: The name of the thread
    name = attr.ib(type=str)
    #: When the thread was last updated
    last_activity = attr.ib(type=datetime)
    #: Number of `Message`\s in the thread
    message_count = attr.ib(type=int)
    #: The thread colour
    colour = attr.ib(type=str)
    #: The thread's default emoji
    emoji = attr.ib(type=str)
    #: A url to the thread's thumbnail/profile picture
    image = attr.ib(None, type=str)
    #: `User`\s and `Page`\s, mapped to their nicknames
    nicknames = attr.ib(factory=dict, type="Dict[Union[User, Page], str]")

    _events = attr.ib(factory=list, type="List[events.Event]")

    @attr.s(slots=True)
    class Colour:
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

    def to_send(self) -> JSON:
        raise NotImplementedError


@attr.s(slots=True)
class User(Thread):
    """Represents a Facebook user and the thread between that user and the client"""

    #: The user's first name
    first_name = attr.ib(None, type=str)  # TODO: Shouldn't be ``None``
    #: The user's last name
    last_name = attr.ib(None, type=str)  # TODO: Shouldn't be ``None``
    #: The user's gender
    gender = attr.ib(None, type=str)
    #: Between 0 and 1. How close the client is to the user
    affinity = attr.ib(None, type=float)
    #: Whether the user and the client are friends
    is_friend = attr.ib(None, type=bool)

    def to_send(self) -> JSON:
        return {"other_user_fbid": self.id}


@attr.s(slots=True)
class Group(Thread):
    """Represents a group-thread"""

    #: Whether users need approval to join
    approval_mode = attr.ib(None, type=bool)
    #: `User`\s, denoting the thread's participants
    participants = attr.ib(factory=set, type=Set[User])
    #: Set containing `User`\s, denoting the group's admins
    admins = attr.ib(factory=set, type=Set[User])
    #: Set containing `User`\s requesting to join the group
    approval_requests = attr.ib(factory=set, type=Set[User])

    def to_send(self) -> JSON:
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
