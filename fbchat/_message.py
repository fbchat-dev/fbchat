# -*- coding: UTF-8 -*-
from __future__ import unicode_literals

import attr
import json
from string import Formatter
from . import _attachment, _location, _file, _quick_reply, _sticker
from ._core import Enum


class EmojiSize(Enum):
    """Used to specify the size of a sent emoji"""

    LARGE = "369239383222810"
    MEDIUM = "369239343222814"
    SMALL = "369239263222822"

    @classmethod
    def _from_tags(cls, tags):
        string_to_emojisize = {
            "large": cls.LARGE,
            "medium": cls.MEDIUM,
            "small": cls.SMALL,
            "l": cls.LARGE,
            "m": cls.MEDIUM,
            "s": cls.SMALL,
        }
        for tag in tags or ():
            data = tag.split(":", maxsplit=1)
            if len(data) > 1 and data[0] == "hot_emoji_size":
                return string_to_emojisize.get(data[1])
        return None


class MessageReaction(Enum):
    """Used to specify a message reaction"""

    LOVE = "😍"
    SMILE = "😆"
    WOW = "😮"
    SAD = "😢"
    ANGRY = "😠"
    YES = "👍"
    NO = "👎"


@attr.s(cmp=False)
class Mention(object):
    """Represents a @mention"""

    #: The thread ID the mention is pointing at
    thread_id = attr.ib()
    #: The character where the mention starts
    offset = attr.ib(0)
    #: The length of the mention
    length = attr.ib(10)


@attr.s(cmp=False)
class Message(object):
    """Represents a Facebook message"""

    #: The actual message
    text = attr.ib(None)
    #: A list of :class:`Mention` objects
    mentions = attr.ib(factory=list, converter=lambda x: [] if x is None else x)
    #: A :class:`EmojiSize`. Size of a sent emoji
    emoji_size = attr.ib(None)
    #: The message ID
    uid = attr.ib(None, init=False)
    #: ID of the sender
    author = attr.ib(None, init=False)
    #: Timestamp of when the message was sent
    timestamp = attr.ib(None, init=False)
    #: Whether the message is read
    is_read = attr.ib(None, init=False)
    #: A list of pepole IDs who read the message, works only with :func:`fbchat.Client.fetchThreadMessages`
    read_by = attr.ib(factory=list, init=False)
    #: A dict with user's IDs as keys, and their :class:`MessageReaction` as values
    reactions = attr.ib(factory=dict, init=False)
    #: A :class:`Sticker`
    sticker = attr.ib(None)
    #: A list of attachments
    attachments = attr.ib(factory=list, converter=lambda x: [] if x is None else x)
    #: A list of :class:`QuickReply`
    quick_replies = attr.ib(factory=list, converter=lambda x: [] if x is None else x)
    #: Whether the message is unsent (deleted for everyone)
    unsent = attr.ib(False, init=False)

    @classmethod
    def formatMentions(cls, text, *args, **kwargs):
        """Like `str.format`, but takes tuples with a thread id and text instead.

        Returns a `Message` object, with the formatted string and relevant mentions.

        ```
        >>> Message.formatMentions("Hey {!r}! My name is {}", ("1234", "Peter"), ("4321", "Michael"))
        <Message (None): "Hey 'Peter'! My name is Michael", mentions=[<Mention 1234: offset=4 length=7>, <Mention 4321: offset=24 length=7>] emoji_size=None attachments=[]>

        >>> Message.formatMentions("Hey {p}! My name is {}", ("1234", "Michael"), p=("4321", "Peter"))
        <Message (None): 'Hey Peter! My name is Michael', mentions=[<Mention 4321: offset=4 length=5>, <Mention 1234: offset=22 length=7>] emoji_size=None attachments=[]>
        ```
        """
        result = ""
        mentions = list()
        offset = 0
        f = Formatter()
        field_names = [field_name[1] for field_name in f.parse(text)]
        automatic = "" in field_names
        i = 0

        for (literal_text, field_name, format_spec, conversion) in f.parse(text):
            offset += len(literal_text)
            result += literal_text

            if field_name is None:
                continue

            if field_name == "":
                field_name = str(i)
                i += 1
            elif automatic and field_name.isdigit():
                raise ValueError(
                    "cannot switch from automatic field numbering to manual field specification"
                )

            thread_id, name = f.get_field(field_name, args, kwargs)[0]

            if format_spec:
                name = f.format_field(name, format_spec)
            if conversion:
                name = f.convert_field(name, conversion)

            result += name
            mentions.append(
                Mention(thread_id=thread_id, offset=offset, length=len(name))
            )
            offset += len(name)

        message = cls(text=result, mentions=mentions)
        return message

    @classmethod
    def _from_graphql(cls, data):
        if data.get("message_sender") is None:
            data["message_sender"] = {}
        if data.get("message") is None:
            data["message"] = {}
        rtn = cls(
            text=data["message"].get("text"),
            mentions=[
                Mention(
                    m.get("entity", {}).get("id"),
                    offset=m.get("offset"),
                    length=m.get("length"),
                )
                for m in data["message"].get("ranges") or ()
            ],
            emoji_size=EmojiSize._from_tags(data.get("tags_list")),
            sticker=_sticker.Sticker._from_graphql(data.get("sticker")),
        )
        rtn.uid = str(data["message_id"])
        rtn.author = str(data["message_sender"]["id"])
        rtn.timestamp = data.get("timestamp_precise")
        rtn.unsent = False
        if data.get("unread") is not None:
            rtn.is_read = not data["unread"]
        rtn.reactions = {
            str(r["user"]["id"]): MessageReaction._extend_if_invalid(r["reaction"])
            for r in data["message_reactions"]
        }
        if data.get("blob_attachments") is not None:
            rtn.attachments = [
                _file.graphql_to_attachment(attachment)
                for attachment in data["blob_attachments"]
            ]
        if data.get("platform_xmd_encoded"):
            quick_replies = json.loads(data["platform_xmd_encoded"]).get(
                "quick_replies"
            )
            if isinstance(quick_replies, list):
                rtn.quick_replies = [
                    _quick_reply.graphql_to_quick_reply(q) for q in quick_replies
                ]
            elif isinstance(quick_replies, dict):
                rtn.quick_replies = [
                    _quick_reply.graphql_to_quick_reply(quick_replies, is_response=True)
                ]
        if data.get("extensible_attachment") is not None:
            attachment = graphql_to_extensible_attachment(data["extensible_attachment"])
            if isinstance(attachment, _attachment.UnsentMessage):
                rtn.unsent = True
            elif attachment:
                rtn.attachments.append(attachment)
        return rtn


def graphql_to_extensible_attachment(data):
    story = data.get("story_attachment")
    if not story:
        return None

    target = story.get("target")
    if not target:
        return _attachment.UnsentMessage(uid=data.get("legacy_attachment_id"))

    _type = target["__typename"]
    if _type == "MessageLocation":
        return _location.LocationAttachment._from_graphql(story)
    elif _type == "MessageLiveLocation":
        return _location.LiveLocationAttachment._from_graphql(story)
    elif _type in ["ExternalUrl", "Story"]:
        return _attachment.ShareAttachment._from_graphql(story)

    return None
