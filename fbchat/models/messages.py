# -*- coding: UTF-8 -*-

import json
import attr

from typing import Optional, Dict, List, Any, Type, T
from enum import Enum

from .core import Dimension, ID, JSON
from .threads import Thread, User, Group
from .events import Event
from .files import File, Audio, Image, AnimatedImage, Video


__all__ = ("Message", "Sticker", "AnimatedSticker", "Emoji", "Text", "FileMessage")


@attr.s(slots=True)
class Message(Event):
    """Represents a message"""

    #: `User`\s, mapped to their `Reaction`
    reactions = attr.ib(type="Dict[User, Message.Reaction]")  # factory=dict

    class Reaction(Enum):
        """Used to specify a message reaction"""

        LOVE = "😍"
        SMILE = "😆"
        WOW = "😮"
        SAD = "😢"
        ANGRY = "😠"
        YES = "👍"
        NO = "👎"

    def to_send(self) -> JSON:
        data = super().to_send()

        data["action_type"] = "ma-type:user-generated-message"

        return data


@attr.s(slots=True)
class Sticker(Message):
    """Represents a sent sticker"""

    #: The sticker's ID
    sticker_id = attr.ib(type=ID)
    #: The sticker's label/name
    name = attr.ib(type=str)
    #: URL to the sticker's image
    url = attr.ib(type=str)
    #: The stickers dimensions
    dimension = attr.ib(type=Dimension)
    #: The sticker's pack
    pack = attr.ib(type="Optional[Sticker.Pack]")

    def load_graphql_data(self, data: JSON) -> Dict[str, Any]:
        self.sticker_id = data["id"]
        self.name = data["label"]
        self.url = data["url"]
        self.dimensions = Dimension.from_dict(data)
        self.pack = Sticker.Pack.from_graphql(data["id"])

    @classmethod
    def from_pull(cls: Type[T], delta: JSON) -> T:
        self = super().from_pull(delta)

        attachment, = [x["mercury"]["sticker_attachment"] for x in delta["attachments"]]
        self.load_graphql_data(attachment)

        return self

    def to_send(self) -> JSON:
        data = super().to_send()

        data["sticker_id"] = self.sticker_id

        return data

    @classmethod
    def from_send(cls: Type[T], action: JSON, old: T) -> T:
        self = super().from_send(action, old)

        payload, = action["graphql_payload"]
        self.load_graphql_data(payload["node"])

        return self

    @attr.s(slots=True)
    class Pack:
        """TODO: This"""

        id: ID = attr.ib(converter=ID)

        def from_graphql(cls: Type[T], data: JSON) -> T:
            return cls(data["id"])


@attr.s(slots=True)
class AnimatedSticker(Sticker):
    """Represents a sent sticker that's animated"""

    #: URL to a spritemap
    sprite_image = attr.ib(type=str)
    #: The amount of frames present in the spritemap pr. row
    frames_per_row = attr.ib(type=int)
    #: The amount of frames present in the spritemap pr. coloumn
    frames_per_col = attr.ib(type=int)
    #: The frame rate the spritemap is intended to be played in
    frame_rate = attr.ib(type=int)
    #: URL to a large spritemap
    large_sprite_image = attr.ib(type=Optional[str])

    def load_graphql_data(self, data: JSON) -> Dict[str, Any]:
        super().load_graphql_data(data)

        self.sprite_image = data["sprite_image"]["uri"]
        self.large_sprite_image = data["sprite_image_2x"].get("uri")
        self.frames_per_row = int(data["frames_per_row"])
        self.frames_per_col = int(data["frames_per_column"])
        self.frame_rate = int(data["frame_rate"])


@attr.s(slots=True)
class Emoji(Message):
    """Represents a sent emoji"""

    #: The actual emoji
    emoji = attr.ib(type=str)
    #: The size of the emoji
    size = attr.ib(type="Emoji.Size")

    @classmethod
    def from_pull(cls: Type[T], delta: JSON) -> T:
        self = super().from_pull(delta)

        self.emoji = delta["body"]
        self.size = Emoji.Size.from_pull(delta["messageMetadata"]["tags"])

        return self

    def to_send(self) -> JSON:
        data = super().to_send()
        data["body"] = self.emoji

        data["tags[0]"] = "hot_emoji_size:{}".format(self.size.value)

        return data

    @classmethod
    def from_send(cls: Type[T], action: JSON, old: T) -> T:
        self = super().from_send(action, old)

        self.emoji = old.emoji
        self.size = old.size

        return self

    class Size(Enum):
        """Represents the size of an emoji"""

        SMALL = "small"
        MEDIUM = "medium"
        LARGE = "large"

        @classmethod
        def from_pull(cls: Type[T], tags: List[str]) -> T:
            tag, = (x for x in tags if x.startswith("hot_emoji_size:"))
            _, tag = tag.split(":", maxsplit=1)
            return cls(tag)


@attr.s(slots=True)
class Text(Message):
    """Represents a text message"""

    #: The text-contents
    text = attr.ib(type=str)
    #: List of `Mention`\s, ordered by `.offset`
    mentions = attr.ib(factory=list, type="List[Text.Mention]")

    @classmethod
    def mentions_from_prng(cls, data: Optional[JSON]) -> "List[Text.Mention]":
        if data and data.get("prng"):
            prng = json.loads(data["prng"])
            return sorted(map(Text.Mention.from_prng, prng), key=lambda x: x.offset)
        return []

    @classmethod
    def from_pull(cls: Type[T], delta: JSON) -> T:
        self = super().from_pull(delta)

        self.text = delta["body"]
        self.mentions = cls.mentions_from_prng(delta.get("data"))

        return self

    def to_send(self) -> JSON:
        data = super().to_send()
        data["body"] = self.text

        for i, mention in enumerate(self.mentions):
            data["profile_xmd[{}][id]".format(i)] = mention.thread_id
            data["profile_xmd[{}][offset]".format(i)] = mention.offset
            data["profile_xmd[{}][length]".format(i)] = mention.length
            data["profile_xmd[{}][type]".format(i)] = "p"

        return data

    @classmethod
    def from_send(cls: Type[T], action: JSON, old: T) -> T:
        self = super().from_send(action, old)

        self.text = old.text
        self.mentions = old.mentions

        return self

    @attr.s(slots=True)
    class Mention:
        """Represents a @mention"""

        #: Thread ID that the mention is pointing at
        thread_id = attr.ib(converter=ID, type=ID)
        #: The character in the message where the mention starts
        offset = attr.ib(converter=int, type=int)
        #: The length of the mention
        length = attr.ib(converter=int, type=int)

        @classmethod
        def from_prng(cls: Type[T], data: JSON) -> T:
            return cls(data["i"], offset=data["o"], length=data["l"])


@attr.s(slots=True)
class FileMessage(Message):
    """Represents a message with files / attachments"""

    #: List of `File`\s sent in the message
    files = attr.ib(factory=list, type=List[File])

    @staticmethod
    def pull_data_get_file(attachment: JSON, mercury: JSON) -> File:
        blob = mercury["blob_attachment"]
        return {
            "MessageImage": Image,
            "MessageAnimatedImage": AnimatedImage,
            "MessageVideo": Video,
            "MessageAudio": Audio,
            "MessageFile": File,
        }[blob["__typename"]].from_pull(attachment, blob)

    @staticmethod
    def mimetype_to_key(mimetype: str) -> str:
        if not mimetype:
            return "file_id"
        if mimetype == "image/gif":
            return "gif_id"
        x = mimetype.split("/")
        if x[0] in ["video", "image", "audio"]:
            return "{}_id".format(x[0])
        return "file_id"

    @classmethod
    def from_pull(cls: Type[T], delta) -> T:
        self = super().from_pull(delta)

        for attachment in delta["attachments"]:
            mercury = attachment["mercury"]
            if "blob_attachment" in mercury:
                self.files.append(cls.pull_data_get_file(attachment, mercury))

        return self

    def to_send(self) -> JSON:
        data = super().to_send()
        data["has_attachment"] = True

        for i, file in enumerate(self.files):
            data["{}s[{}]".format(self.mimetype_to_key(file.mimetype), i)] = file.id

        return data

    @classmethod
    def from_send(cls: Type[T], action: JSON, old: T) -> T:
        # TODO: Parse `action["graphql_payload"]` to retrieve updated file info
        self = super().from_send(action, old)

        self.files = old.files

        return self
