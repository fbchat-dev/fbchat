# -*- coding: UTF-8 -*-

from __future__ import unicode_literals

import attr

from datetime import datetime
from typing import Dict, Set, List, Union, Optional
from enum import Enum


@attr.s(slots=True, str=True)
class FacebookError(Exception):
    """Thrown when Facebook returns an error"""

    #: The error code that Facebook returned
    fb_error_code = attr.ib(type=int, converter=int)
    #: A localized error message that Facebook returned
    fb_error_message = attr.ib(type=str)


@attr.s(slots=True)
class Thread(object):
    """Represents a Facebook chat-thread"""

    #: The unique identifier of the thread
    id = attr.ib(type=int, converter=int)
    #: The name of the thread
    name = attr.ib(type=str)
    #: When the thread was last updated
    last_activity = attr.ib(type=datetime)
    #: A url to the thread's thumbnail/profile picture
    image = attr.ib(None, type=str)
    #: Number of `Message`\s in the thread
    message_count = attr.ib(None, type=int)
    #: `User`\s and `Page`\s, mapped to their nicknames
    nicknames = attr.ib(type="Dict[Union[User, Page], str]", factory=dict)
    #: The thread colour
    colour = attr.ib(None, type=str)
    #: The thread's default emoji
    emoji = attr.ib(None, type=str)

    _events = attr.ib(type="List[Event]", factory=list)

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
    gender = attr.ib(None)  # TODO: The type of this
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
    approval_mode = attr.ib(None, type=bool, converter=bool)
    #: Set containing `User`\s requesting to join the group
    approval_requests = attr.ib(type=Set[User], factory=set)


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


@attr.s(slots=True)
class Event(object):
    """Represents an event in a Facebook thread"""

    #: The unique identifier of the event
    id = attr.ib(type=int, converter=int)
    #: The thread the event was sent to
    thread = attr.ib(type=Thread)
    #: The person who sent the event
    author = attr.ib(type=Union[User, Page])
    #: When the event was sent
    time = attr.ib(type=datetime)
    #: Whether the event is read
    is_read = attr.ib(type=bool, converter=bool)

    def __eq__(self, other):
        return isinstance(other, Event) and self.id == other.id

    def __ne__(self, other):
        return not self.__eq__(other)


@attr.s(slots=True)
class Message(Event):
    """Represents a message"""

    #: `User`\s, mapped to their reaction. A reaction can be ``😍``, ``😆``, ``😮``, ``😢``, ``😠``, ``👍`` or ``👎``
    reactions = attr.ib(type=Dict[User, str])


@attr.s(slots=True)
class Action(Event):
    """Represents an action in a thread"""


@attr.s(slots=True)
class Sticker(Message):
    """Represents a sent sticker"""

    #: The sticker's ID
    sticker_id = attr.ib(type=int, converter=int)
    #: The sticker's label/name
    name = attr.ib(type=str)
    #: Width of the sticker
    width = attr.ib(type=int, converter=int)
    #: Height of the sticker
    height = attr.ib(type=int, converter=int)
    #: The sticker's pack
    pack = attr.ib(None, type="Sticker.Pack")

    @attr.s(slots=True, repr_ns="Sticker")
    class Pack(object):
        """TODO: This"""


@attr.s(slots=True)
class AnimatedSticker(Sticker):
    """TODO: This"""


@attr.s(slots=True)
class Emoji(Message):
    """Represents a sent emoji"""

    #: The actual emoji
    emoji = attr.ib(type=str)
    #: The size of the emoji
    size = attr.ib(type="Emoji.Size")

    class Size(Enum):
        """Represents the size of an emoji"""

        SMALL = "small"
        MEDIUM = "medium"
        LARGE = "large"


@attr.s(slots=True)
class Text(Message):
    """Represents a text message"""

    #: The text-contents
    text = attr.ib(type=str)
    #: List of `Mention`\s, ordered by `.offset`
    mentions = attr.ib(type="List[Text.Mention]")

    @attr.s(slots=True, repr_ns="Text")
    class Mention(object):
        """Represents a @mention"""

        #: Person that the mention is pointing at
        thread = attr.ib(type=Union[User, Page])
        #: The character in the message where the mention starts
        offset = attr.ib(type=int, converter=int)
        #: The length of the mention
        length = attr.ib(type=int, converter=int)


@attr.s(slots=True)
class FileMessage(Text):
    """Represents a text message with files / attachments"""

    #: List of `File`\s sent in the message
    files = attr.ib(type="List[File]")


@attr.s(slots=True)
class File(object):
    """Represents a file / an attachment"""

    #: The unique identifier of the file
    id = attr.ib(type=int, converter=int)
    #: Name of the file
    name = attr.ib(type=str)
    #: URL where you can download the file
    url = attr.ib(type=str)
    #: Size of the file, in bytes
    size = attr.ib(type=int, converter=int)
    #: Whether Facebook determines that this file may be harmful
    is_malicious = attr.ib(None, type=bool)


@attr.s(slots=True)
class Audio(File):
    """Todo: This"""


@attr.s(slots=True)
class Image(File):
    """Todo: This"""


@attr.s(slots=True)
class AnimatedImage(Image):
    """Todo: This"""


@attr.s(slots=True)
class Video(File):
    """Todo: This"""


@attr.s(slots=True)
class UsersAdded(Action):
    """Represents an action where people were added to a group"""

    #: The added `User`\s
    users = attr.ib(type=List[User])


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
    nickname = attr.ib(type=str)


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
