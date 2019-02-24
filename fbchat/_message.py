# -*- coding: UTF-8 -*-
from __future__ import unicode_literals

import attr
from string import Formatter
from ._core import Enum


class EmojiSize(Enum):
    """Used to specify the size of a sent emoji"""

    LARGE = "369239383222810"
    MEDIUM = "369239343222814"
    SMALL = "369239263222822"


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
