# -*- coding: UTF-8 -*-

import attr

from typing import Set, Union

from .threads import Thread, User, Page
from .events import Event
from .files import Image


__all__ = (
    "Action",
    "UsersAdded",
    "UserRemoved",
    "AdminAdded",
    "AdminRemoved",
    "ThreadAdded",
    "ImageSet",
    "TitleSet",
    "NicknameSet",
    "ColourSet",
    "EmojiSet",
)


@attr.s(slots=True)
class Action(Event):
    """Represents an action in a thread"""


@attr.s(slots=True)
class UsersAdded(Action):
    """Represents an action where people were added to a group"""

    #: The added `User`\s
    users = attr.ib(factory=set, type=Set[User])


@attr.s(slots=True)
class UserRemoved(Action):
    """Represents an action where a person was removed from a group"""

    #: The removed `User`
    user = attr.ib(type=User)


@attr.s(slots=True)
class AdminAdded(Action):
    """Represents an action where a group admin was added"""

    #: The promoted `User`
    user = attr.ib(type=User)


@attr.s(slots=True)
class AdminRemoved(Action):
    """Represents an action where a group admin was removed"""

    #: The demoted `User`
    user = attr.ib(type=User)


@attr.s(slots=True)
class ThreadAdded(Action):
    """Represents an action where a thread was created"""


@attr.s(slots=True)
class ImageSet(Action):
    """Represents an action where a group image was changed"""

    #: The new `Image`
    image = attr.ib(type=Image)


@attr.s(slots=True)
class TitleSet(Action):
    """Represents an action where the group title was changed"""

    #: The new title
    title = attr.ib(type=str)


@attr.s(slots=True)
class NicknameSet(Action):
    """Represents an action where a nickname was changed"""

    #: Person whose nickname was changed
    subject = attr.ib(type=Union[User, Page])
    #: The persons new nickname
    nickname = attr.ib(None, type=str)


@attr.s(slots=True)
class ColourSet(Action):
    """Represents an action where the thread colour was changed"""

    #: The new colour
    colour = attr.ib(type=Thread.Colour)


@attr.s(slots=True)
class EmojiSet(Action):
    """Represents an action where the thread emoji was changed"""

    #: The new emoji
    emoji = attr.ib(type=str)
