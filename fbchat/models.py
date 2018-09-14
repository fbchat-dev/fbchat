# -*- coding: UTF-8 -*-

from __future__ import unicode_literals

import json
import attr

from datetime import datetime, timedelta
from typing import Dict, Set, List, Union
from enum import Enum


@attr.s(slots=True)
class Dimension(object):
    """Represents the width and height of an object"""

    #: Width of the object
    width = attr.ib(type=int, converter=int)
    #: Height of the object
    height = attr.ib(type=int, converter=int)

    @classmethod
    def from_dict(cls, items):
        return cls(items["width"], items["height"])


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
    actor = attr.ib(None, type=Union[User, Page])
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
    def from_pull(cls, delta, **kwargs):
        metadata = delta["messageMetadata"]
        time = datetime.fromtimestamp(int(metadata["timestamp"]) / 1000)
        return cls(
            id=metadata["messageId"],
            thread=cls.pull_data_get_thread(delta, time),
            actor=User(metadata["actorFbId"]),
            time=time,
            **kwargs
        )


@attr.s(slots=True)
class Message(Event):
    """Represents a message"""

    #: `User`\s, mapped to their `Reaction`
    reactions = attr.ib(factory=dict)  # type: Dict[User, Message.Reaction]

    class Reaction(Enum):
        """Used to specify a message reaction"""

        LOVE = "😍"
        SMILE = "😆"
        WOW = "😮"
        SAD = "😢"
        ANGRY = "😠"
        YES = "👍"
        NO = "👎"


@attr.s(slots=True)
class Action(Event):
    """Represents an action in a thread"""


@attr.s(slots=True)
class Sticker(Message):
    """Represents a sent sticker"""

    #: The sticker's ID
    sticker_id = attr.ib(None, type=int, converter=int)
    #: The sticker's label/name
    name = attr.ib(None, type=str)
    #: URL to the sticker's image
    url = attr.ib(None, type=str)
    #: The stickers dimensions
    dimensions = attr.ib(None, type=Dimension)
    #: The sticker's pack
    pack = attr.ib(None)  # type: Sticker.Pack

    @classmethod
    def from_pull(cls, delta, **kwargs):
        attachment, = [x["mercury"]["sticker_attachment"] for x in delta["attachments"]]
        return super(Sticker, cls).from_pull(
            delta,
            sticker_id=attachment["id"],
            name=attachment["label"],
            url=attachment["url"],
            dimensions=Dimension.from_dict(attachment),
            pack=Sticker.Pack(attachment["pack"]["id"]),
            **kwargs
        )

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
    def from_pull(cls, delta, **kwargs):
        attachment, = [x["mercury"]["sticker_attachment"] for x in delta["attachments"]]

        return super(AnimatedSticker, cls).from_pull(
            delta,
            sprite_image=attachment["sprite_image"]["uri"],
            large_sprite_image=attachment["sprite_image_2x"].get("uri"),
            frames_per_row=int(attachment["frames_per_row"]),
            frames_per_col=int(attachment["frames_per_column"]),
            frame_rate=int(attachment["frame_rate"]),
            **kwargs
        )


@attr.s(slots=True)
class Emoji(Message):
    """Represents a sent emoji"""

    #: The actual emoji
    emoji = attr.ib(None, type=str)
    #: The size of the emoji
    size = attr.ib(None)  # type: Emoji.Size

    @classmethod
    def from_pull(cls, delta, **kwargs):
        return super(Emoji, cls).from_pull(
            delta,
            emoji=delta["body"],
            size=Emoji.Size.from_pull(delta["messageMetadata"]["tags"]),
            **kwargs
        )

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
    mentions = attr.ib(factory=list)  # type: List[Text.Mention]

    @classmethod
    def from_pull(cls, delta, **kwargs):
        message = super(Text, cls).from_pull(delta, text=delta["body"], **kwargs)

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
        def from_pull(cls, data, **kwargs):
            return cls(Thread(x["i"]), offset=x["o"], length=x["l"], **kwargs)


@attr.s(slots=True)
class FileMessage(Message):
    """Represents a message with files / attachments"""

    #: List of `File`\s sent in the message
    files = attr.ib(factory=list)  # type: List[File]

    @staticmethod
    def pull_data_get_file(attachment, mercury):
        blob = mercury["blob_attachment"]
        return {
            "MessageImage": Image,
            "MessageAnimatedImage": AnimatedImage,
            "MessageVideo": Video,
            "MessageAudio": Audio,
            "MessageFile": File,
        }[blob["__typename"]].from_pull(attachment, blob)

    @classmethod
    def from_pull(cls, delta, **kwargs):
        message = super(FileMessage, cls).from_pull(delta, **kwargs)

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
    def from_pull(cls, attachment, blob, **kwargs):
        return cls(
            id=attachment["id"],
            name=attachment["filename"],
            mimetype=attachment["mimeType"],
            size=attachment["fileSize"],
            url=blob.get("url"),
            is_malicious=blob.get("is_malicious"),
            **kwargs
        )


@attr.s(slots=True)
class Audio(File):
    """Represents an audio file"""

    #: Duration of the audioclip
    duration = attr.ib(None, type=timedelta)
    #: Audio type
    audio_type = attr.ib(None, type=str)

    @classmethod
    def from_pull(cls, attachment, blob, **kwargs):
        file = super(Audio, cls).from_pull(
            attachment,
            blob,
            duration=timedelta(microseconds=blob["playable_duration_in_ms"] * 1000),
            audio_type=blob["audio_type"],
            **kwargs
        )
        file.url = blob["playable_url"]
        return file


@attr.s(slots=True)
class Image(File):
    """Represents an image"""

    #: The extension of the original image (e.g. 'png')
    extension = attr.ib(None, type=str)
    #: Dimensions of the original image
    dimensions = attr.ib(None, type=Dimension)

    #: URL to a 50x50 thumbnail of the image
    thumbnail_url = attr.ib(None, type=str)

    #: URL to a medium preview of the image
    preview_url = attr.ib(None, type=str)
    #: Dimensions of the medium preview
    preview_dimensions = attr.ib(None, type=Dimension)

    #: URL to a large preview of the image
    large_preview_url = attr.ib(None, type=str)
    #: Dimensions of the large preview
    large_preview_dimensions = attr.ib(None, type=Dimension)

    @classmethod
    def from_pull(cls, attachment, blob, **kwargs):
        preview = blob["preview"]
        large_preview = blob["large_preview"]
        return super(Image, cls).from_pull(
            attachment,
            blob,
            extension=blob["original_extension"],
            dimensions=Dimension.from_dict(attachment["imageMetadata"]),
            thumbnail_url=blob["thumbnail"]["uri"],
            preview_url=preview["uri"],
            preview_dimensions=Dimension.from_dict(preview),
            large_preview_url=large_preview["uri"],
            large_preview_dimensions=Dimension.from_dict(large_preview),
            **kwargs
        )


@attr.s(slots=True)
class AnimatedImage(Image):
    """Represents an image (e.g. "gif")"""

    #: URL to an animated preview of the image
    animated_preview_url = None
    #: Dimensions of the animated preview
    animated_preview_dimensions = attr.ib(None, type=Dimension)

    @classmethod
    def from_pull(cls, attachment, blob, **kwargs):
        animated = blob["animated_image"]
        return super(AnimatedImage, cls).from_pull(
            attachment,
            blob,
            animated_preview_url=animated["uri"],
            animated_preview_dimensions=Dimension.from_dict(animated),
            **kwargs
        )


@attr.s(slots=True)
class Video(File):
    """Represents a video"""

    #: Dimensions of the original image
    dimensions = attr.ib(None, type=Dimension)
    #: Duration of the video
    duration = attr.ib(None, type=timedelta)
    #: URL to very compressed preview video
    preview_url = attr.ib(None, type=str)

    #: URL to a small preview image of the video
    small_image_url = attr.ib(None, type=str)
    #: Dimensions of the small preview
    small_image_dimensions = attr.ib(None, type=Dimension)

    #: URL to a medium preview image of the video
    medium_image_url = attr.ib(None, type=str)
    #: Dimensions of the medium preview
    medium_image_dimensions = attr.ib(None, type=Dimension)

    #: URL to a large preview image of the video
    large_image_url = attr.ib(None, type=str)
    #: Dimensions of the large preview
    large_image_dimensions = attr.ib(None, type=Dimension)

    @classmethod
    def from_pull(cls, attachment, blob, **kwargs):
        small_image = blob["chat_image"]
        medium_image = blob["inbox_image"]
        large_image = blob["large_image"]
        return super(Video, cls).from_pull(
            attachment,
            blob,
            dimensions=Dimension.from_dict(blob["original_dimensions"]),
            duration=timedelta(microseconds=blob["playable_duration_in_ms"] * 1000),
            preview_url=blob["playable_url"],
            small_image_url=small_image["uri"],
            small_image_dimensions=Dimension.from_dict(small_image),
            medium_image_url=medium_image["uri"],
            medium_image_dimensions=Dimension.from_dict(medium_image),
            large_image_url=large_image["uri"],
            large_image_dimensions=Dimension.from_dict(large_image),
            **kwargs
        )


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
