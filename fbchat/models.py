# -*- coding: UTF-8 -*-

from __future__ import unicode_literals

import json
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
    name = attr.ib(None, type=str)
    #: When the thread was last updated
    last_activity = attr.ib(None, type=datetime)
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
    approval_mode = attr.ib(None, type=bool)
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
    id = attr.ib(None, type=str)
    #: The thread the event was sent to
    thread = attr.ib(None, type=Thread)
    #: The person who sent the event
    author = attr.ib(None, type=Union[User, Page])
    #: When the event was sent
    time = attr.ib(None, type=datetime)
    #: Whether the event is read
    is_read = attr.ib(None, type=bool)

    def __eq__(self, other):
        return isinstance(other, Event) and self.id == other.id

    def __ne__(self, other):
        return not self.__eq__(other)

    @staticmethod
    def pull_data_get_thread(delta, time):
        thread_key = delta["messageMetadata"]["threadKey"]
        if "threadFbId" in thread_key:
            return Group(thread_key["threadFbId"], last_activity=time)
        elif "otherUserFbId" in thread_key:
            return User(thread_key["otherUserFbId"], last_activity=time)

    @classmethod
    def from_pull(cls, delta):
        metadata = delta["messageMetadata"]
        time = datetime.fromtimestamp(int(metadata["timestamp"]) / 1000)
        return cls(
            id=metadata["messageId"],
            thread=cls.pull_data_get_thread(delta, time),
            author=User(metadata["actorFbId"]),
            time=time,
        )


@attr.s(slots=True)
class Message(Event):
    """Represents a message"""

    reactions = attr.ib(type=Dict[User, str], factory=dict)
    r"""`User`\s, mapped to their reaction

    A reaction can be ``😍``, ``😆``, ``😮``, ``😢``, ``😠``, ``👍`` or ``👎``
    """


@attr.s(slots=True)
class Action(Event):
    """Represents an action in a thread"""


@attr.s(slots=True)
class Sticker(Message):
    """Represents a sent sticker"""

    #: The sticker's ID
    sticker_id = attr.ib(None, type=int)
    #: The sticker's label/name
    name = attr.ib(None, type=str)
    #: URL to the sticker's image
    url = attr.ib(None, type=str)
    #: Width of the sticker
    width = attr.ib(None, type=int)
    #: Height of the sticker
    height = attr.ib(None, type=int)
    #: The sticker's pack
    pack = attr.ib(None, type="Sticker.Pack")

    @classmethod
    def from_pull(cls, delta):
        message = super(Sticker, cls).from_pull(delta)
        attachment, = [x["mercury"]["sticker_attachment"] for x in delta["attachments"]]

        message.sticker_id = int(attachment["id"])
        message.name = attachment["label"]
        message.url = attachment["url"]
        message.width = int(attachment["width"])
        message.height = int(attachment["height"])
        message.pack = Sticker.Pack(attachment["pack"]["id"])

        return message

    @attr.s(slots=True, repr_ns="Sticker")
    class Pack(object):
        """TODO: This"""

        id = attr.ib(type=int, converter=int)


@attr.s(slots=True)
class AnimatedSticker(Sticker):
    """Represents a sent sticker that's animated"""

    #: URL to a spritemap
    sprite_image = attr.ib(None, type=str)
    #: URL to a large spritemap
    large_sprite_image = attr.ib(None, type=str)
    #: The amount of frames present in the spritemap pr. row
    frames_per_row = attr.ib(None, type=int)
    #: The amount of frames present in the spritemap pr. coloumn
    frames_per_col = attr.ib(None, type=int)
    #: The frame rate the spritemap is intended to be played in
    frame_rate = attr.ib(None, type=int)

    @classmethod
    def from_pull(cls, delta):
        message = super(AnimatedSticker, cls).from_pull(delta)
        attachment, = [x["mercury"]["sticker_attachment"] for x in delta["attachments"]]

        message.sprite_image = attachment["sprite_image"].get("uri")
        message.large_sprite_image = attachment["sprite_image_2x"].get("uri")
        message.frames_per_row = attachment["frames_per_row"]
        message.frames_per_col = attachment["frames_per_column"]
        message.frame_rate = attachment["frame_rate"]

        message.pack = Sticker.Pack(attachment["pack"]["id"])
        return message


@attr.s(slots=True)
class Emoji(Message):
    """Represents a sent emoji"""

    #: The actual emoji
    emoji = attr.ib(None, type=str)
    #: The size of the emoji
    size = attr.ib(None, type="Emoji.Size")

    @classmethod
    def from_pull(cls, delta):
        message = super(Emoji, cls).from_pull(delta)
        message.emoji = delta["body"]
        message.size = Emoji.Size.from_pull(delta["messageMetadata"]["tags"])
        return message

    class Size(Enum):
        """Represents the size of an emoji"""

        SMALL = "small"
        MEDIUM = "medium"
        LARGE = "large"

        @classmethod
        def from_pull(cls, tags):
            tag, = [x for x in tags if x.startswith("hot_emoji_size:")]
            tag = tag.split(":", maxsplit=1)[1]
            return cls(tag)


@attr.s(slots=True)
class Text(Message):
    """Represents a text message"""

    #: The text-contents
    text = attr.ib(None, type=str)
    #: List of `Mention`\s, ordered by `.offset`
    mentions = attr.ib(type="List[Text.Mention]", factory=list)

    @classmethod
    def from_pull(cls, delta):
        message = super(Text, cls).from_pull(delta)
        message.text = delta["body"]

        if delta.get("data") and delta["data"].get("prng"):
            mention_data = json.loads(delta["data"]["prng"])
            message.mentions = [Text.Mention.from_pull(x) for x in mention_data]
            message.mentions.sort(key="offset")

        return message

    @attr.s(slots=True, repr_ns="Text")
    class Mention(object):
        """Represents a @mention"""

        #: Person that the mention is pointing at
        thread = attr.ib(type=Thread)
        #: The character in the message where the mention starts
        offset = attr.ib(type=int, converter=int)
        #: The length of the mention
        length = attr.ib(type=int, converter=int)

        @classmethod
        def from_pull(cls, data):
            return cls(Thread(x["i"]), offset=x["o"], length=x["l"])


@attr.s(slots=True)
class FileMessage(Message):
    """Represents a message with files / attachments"""

    #: List of `File`\s sent in the message
    files = attr.ib(type="List[File]", factory=list)

    @staticmethod
    def pull_data_get_file(attachment, mercury):
        blob = mercury["blob_attachment"]
        return {
            "MessageImage": Image,
            "MessageAnimatedImage": AnimatedImage,
            "MessageVideo": Video,
            "Audio": Audio,
            "MessageFile": File,
        }[blob["__typename"]].from_pull(attachment, blob)

    @classmethod
    def from_pull(cls, delta):
        message = super(FileMessage, cls).from_pull(delta)
        for attachment in delta["attachments"]:
            mercury = attachment["mercury"]
            if "blob_attachment" in mercury:
                message.files.append(cls.pull_data_get_file(attachment, mercury))
            else:
                return None
        return message


@attr.s(slots=True)
class File(object):
    """Represents a file / an attachment"""

    #: The unique identifier of the file
    id = attr.ib(type=int, converter=int)
    #: Name of the file
    name = attr.ib(type=str)
    #: The mimetype of the file
    mimetype = attr.ib(type=str)
    #: URL where you can download the file
    url = attr.ib(type=str)
    #: Size of the file, in bytes
    size = attr.ib(type=int, converter=int)
    #: Whether Facebook determines that this file may be harmful
    is_malicious = attr.ib(None, type=bool)

    @classmethod
    def from_pull(cls, attachment, blob):
        return cls(
            id=attachment["id"],
            name=attachment["filename"],
            mimetype=attachment["mimeType"],
            size=attachment["fileSize"],
            url=blob["url"],
            is_malicious=blob.get("is_malicious"),
        )


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
    users = attr.ib(type=List[User], factory=list)


@attr.s(slots=True)
class UserRemoved(Action):
    """Represents an action where a person was removed from a group"""

    #: The removed `User`
    user = attr.ib(None, type=User)


@attr.s(slots=True)
class AdminAdded(Action):
    """Represents an action where a group admin was added"""

    #: The promoted `User`
    user = attr.ib(None, type=User)


@attr.s(slots=True)
class AdminRemoved(Action):
    """Represents an action where a group admin was removed"""

    #: The demoted `User`
    user = attr.ib(None, type=User)


@attr.s(slots=True)
class ThreadAdded(Action):
    """Represents an action where a thread was created"""


@attr.s(slots=True)
class ImageSet(Action):
    """Represents an action where a group image was changed"""

    #: The new `Image`
    image = attr.ib(None, type=Image)


@attr.s(slots=True)
class TitleSet(Action):
    """Represents an action where the group title was changed"""

    #: The new title
    title = attr.ib(None, type=str)


@attr.s(slots=True)
class NicknameSet(Action):
    """Represents an action where a nickname was changed"""

    #: Person whose nickname was changed
    subject = attr.ib(None, type=Union[User, Page])
    #: The persons new nickname
    nickname = attr.ib(None, type=str)


@attr.s(slots=True)
class ColourSet(Action):
    """Represents an action where the thread colour was changed"""

    #: The new colour
    colour = attr.ib(None, type=Thread.Colour)


@attr.s(slots=True)
class EmojiSet(Action):
    """Represents an action where the thread emoji was changed"""

    #: The new emoji
    emoji = attr.ib(None, type=str)
