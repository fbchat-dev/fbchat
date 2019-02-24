# -*- coding: UTF-8 -*-
from __future__ import unicode_literals

from string import Formatter


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


class Mention(object):
    #: The thread ID the mention is pointing at
    thread_id = None
    #: The character where the mention starts
    offset = None
    #: The length of the mention
    length = None

    def __init__(self, thread_id, offset=0, length=10):
        """Represents a @mention"""
        self.thread_id = thread_id
        self.offset = offset
        self.length = length

    def __repr__(self):
        return self.__unicode__()

    def __unicode__(self):
        return "<Mention {}: offset={} length={}>".format(
            self.thread_id, self.offset, self.length
        )


class Message(object):
    #: The actual message
    text = None
    #: A list of :class:`Mention` objects
    mentions = None
    #: A :class:`EmojiSize`. Size of a sent emoji
    emoji_size = None
    #: The message ID
    uid = None
    #: ID of the sender
    author = None
    #: Timestamp of when the message was sent
    timestamp = None
    #: Whether the message is read
    is_read = None
    #: A list of pepole IDs who read the message, works only with :func:`fbchat.Client.fetchThreadMessages`
    read_by = None
    #: A dict with user's IDs as keys, and their :class:`MessageReaction` as values
    reactions = None
    #: The actual message
    text = None
    #: A :class:`Sticker`
    sticker = None
    #: A list of attachments
    attachments = None
    #: A list of :class:`QuickReply`
    quick_replies = None
    #: Whether the message is unsent (deleted for everyone)
    unsent = None

    def __init__(
        self,
        text=None,
        mentions=None,
        emoji_size=None,
        sticker=None,
        attachments=None,
        quick_replies=None,
    ):
        """Represents a Facebook message"""
        self.text = text
        if mentions is None:
            mentions = []
        self.mentions = mentions
        self.emoji_size = emoji_size
        self.sticker = sticker
        if attachments is None:
            attachments = []
        self.attachments = attachments
        if quick_replies is None:
            quick_replies = []
        self.quick_replies = quick_replies
        self.reactions = {}
        self.read_by = []
        self.deleted = False

    def __repr__(self):
        return self.__unicode__()

    def __unicode__(self):
        return "<Message ({}): {}, mentions={} emoji_size={} attachments={}>".format(
            self.uid, repr(self.text), self.mentions, self.emoji_size, self.attachments
        )

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
