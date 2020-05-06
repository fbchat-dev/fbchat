import attr
import datetime
import enum
from string import Formatter
from . import _attachment, _location, _file, _quick_reply, _sticker
from .._common import log, attrs_default
from .. import _exception, _util
from typing import Optional, Mapping, Sequence, Any


class EmojiSize(enum.Enum):
    """Used to specify the size of a sent emoji."""

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
            data = tag.split(":", 1)
            if len(data) > 1 and data[0] == "hot_emoji_size":
                return string_to_emojisize.get(data[1])
        return None


@attrs_default
class Mention:
    """Represents a ``@mention``.

    >>> fbchat.Mention(thread_id="1234", offset=5, length=2)
    Mention(thread_id="1234", offset=5, length=2)
    """

    #: The thread ID the mention is pointing at
    thread_id = attr.ib(type=str)
    #: The character where the mention starts
    offset = attr.ib(type=int)
    #: The length of the mention
    length = attr.ib(type=int)

    @classmethod
    def _from_range(cls, data):
        # TODO: Parse data["entity"]["__typename"]
        return cls(
            # Can be missing
            thread_id=data["entity"].get("id"),
            offset=data["offset"],
            length=data["length"],
        )

    @classmethod
    def _from_prng(cls, data):
        return cls(thread_id=data["i"], offset=data["o"], length=data["l"])

    def _to_send_data(self, i):
        return {
            "profile_xmd[{}][id]".format(i): self.thread_id,
            "profile_xmd[{}][offset]".format(i): self.offset,
            "profile_xmd[{}][length]".format(i): self.length,
            "profile_xmd[{}][type]".format(i): "p",
        }


# Exaustively searched for options by using the list in:
# https://unicode.org/emoji/charts/full-emoji-list.html
SENDABLE_REACTIONS = ("❤", "😍", "😆", "😮", "😢", "😠", "👍", "👎")


@attrs_default
class Message:
    """Represents a Facebook message.

    Example:
        >>> thread = fbchat.User(session=session, id="1234")
        >>> message = fbchat.Message(thread=thread, id="mid.$XYZ")
    """

    #: The thread that this message belongs to.
    thread = attr.ib()
    #: The message ID.
    id = attr.ib(converter=str, type=str)

    @property
    def session(self):
        """The session to use when making requests."""
        return self.thread.session

    @staticmethod
    def _delete_many(session, message_ids):
        data = {}
        for i, id_ in enumerate(message_ids):
            data["message_ids[{}]".format(i)] = id_
        j = session._payload_post("/ajax/mercury/delete_messages.php?dpr=1", data)

    def delete(self):
        """Delete the message (removes it only for the user).

        If you want to delete multiple messages, please use `Client.delete_messages`.

        Example:
            >>> message.delete()
        """
        self._delete_many(self.session, [self.id])

    def unsend(self):
        """Unsend the message (removes it for everyone).

        The message must to be sent by you, and less than 10 minutes ago.

        Example:
            >>> message.unsend()
        """
        data = {"message_id": self.id}
        j = self.session._payload_post("/messaging/unsend_message/?dpr=1", data)

    def react(self, reaction: Optional[str]):
        """React to the message, or removes reaction.

        Currently, you can use "❤", "😍", "😆", "😮", "😢", "😠", "👍" or "👎". It
        should be possible to add support for more, but we haven't figured that out yet.

        Args:
            reaction: Reaction emoji to use, or if ``None``, removes reaction.

        Example:
            >>> message.react("😍")
        """
        if reaction and reaction not in SENDABLE_REACTIONS:
            raise ValueError(
                "Invalid reaction! Please use one of: {}".format(SENDABLE_REACTIONS)
            )

        data = {
            "action": "ADD_REACTION" if reaction else "REMOVE_REACTION",
            "client_mutation_id": "1",
            "actor_id": self.session.user.id,
            "message_id": self.id,
            "reaction": reaction,
        }
        data = {
            "doc_id": 1491398900900362,
            "variables": _util.json_minimal({"data": data}),
        }
        j = self.session._payload_post("/webgraphql/mutation", data)
        _exception.handle_graphql_errors(j)

    def fetch(self) -> "MessageData":
        """Fetch fresh `MessageData` object.

        Example:
            >>> message = message.fetch()
            >>> message.text
            "The message text"
        """
        message_info = self.thread._forced_fetch(self.id).get("message")
        return MessageData._from_graphql(self.thread, message_info)

    @staticmethod
    def format_mentions(text, *args, **kwargs):
        """Like `str.format`, but takes tuples with a thread id and text instead.

        Return a tuple, with the formatted string and relevant mentions.

        >>> Message.format_mentions("Hey {!r}! My name is {}", ("1234", "Peter"), ("4321", "Michael"))
        ("Hey 'Peter'! My name is Michael", [Mention(thread_id=1234, offset=4, length=7), Mention(thread_id=4321, offset=24, length=7)])

        >>> Message.format_mentions("Hey {p}! My name is {}", ("1234", "Michael"), p=("4321", "Peter"))
        ('Hey Peter! My name is Michael', [Mention(thread_id=4321, offset=4, length=5), Mention(thread_id=1234, offset=22, length=7)])
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

        return result, mentions


@attrs_default
class MessageSnippet(Message):
    """Represents data in a Facebook message snippet.

    Inherits `Message`.
    """

    #: ID of the sender
    author = attr.ib(type=str)
    #: When the message was sent
    created_at = attr.ib(type=datetime.datetime)
    #: The actual message
    text = attr.ib(type=str)
    #: A dict with offsets, mapped to the matched text
    matched_keywords = attr.ib(type=Mapping[int, str])

    @classmethod
    def _parse(cls, thread, data):
        return cls(
            thread=thread,
            id=data["message_id"],
            author=data["author"].rstrip("fbid:"),
            created_at=_util.millis_to_datetime(data["timestamp"]),
            text=data["body"],
            matched_keywords={int(k): v for k, v in data["matched_keywords"].items()},
        )


@attrs_default
class MessageData(Message):
    """Represents data in a Facebook message.

    Inherits `Message`.
    """

    #: ID of the sender
    author = attr.ib(type=str)
    #: When the message was sent
    created_at = attr.ib(type=datetime.datetime)
    #: The actual message
    text = attr.ib(None, type=Optional[str])
    #: A list of `Mention` objects
    mentions = attr.ib(factory=list, type=Sequence[Mention])
    #: Size of a sent emoji
    emoji_size = attr.ib(None, type=Optional[EmojiSize])
    #: Whether the message is read
    is_read = attr.ib(None, type=Optional[bool])
    #: People IDs who read the message, only works with `ThreadABC.fetch_messages`
    read_by = attr.ib(factory=list, type=bool)
    #: A dictionary with user's IDs as keys, and their reaction as values
    reactions = attr.ib(factory=dict, type=Mapping[str, str])
    #: A `Sticker`
    sticker = attr.ib(None, type=Optional[_sticker.Sticker])
    #: A list of attachments
    attachments = attr.ib(factory=list, type=Sequence[_attachment.Attachment])
    #: A list of `QuickReply`
    quick_replies = attr.ib(factory=list, type=Sequence[_quick_reply.QuickReply])
    #: Whether the message is unsent (deleted for everyone)
    unsent = attr.ib(False, type=Optional[bool])
    #: Message ID you want to reply to
    reply_to_id = attr.ib(None, type=Optional[str])
    #: Replied message
    replied_to = attr.ib(None, type=Optional[Any])
    #: Whether the message was forwarded
    forwarded = attr.ib(False, type=Optional[bool])

    @staticmethod
    def _get_forwarded_from_tags(tags):
        if tags is None:
            return False
        return any(map(lambda tag: "forward" in tag or "copy" in tag, tags))

    @staticmethod
    def _parse_quick_replies(data):
        if data:
            data = _util.parse_json(data).get("quick_replies")
            if isinstance(data, list):
                return [_quick_reply.graphql_to_quick_reply(q) for q in data]
            elif isinstance(data, dict):
                return [_quick_reply.graphql_to_quick_reply(data, is_response=True)]
        return []

    @classmethod
    def _from_graphql(cls, thread, data, read_receipts=None):
        if data.get("message_sender") is None:
            data["message_sender"] = {}
        if data.get("message") is None:
            data["message"] = {}
        tags = data.get("tags_list")

        created_at = _util.millis_to_datetime(int(data.get("timestamp_precise")))

        attachments = [
            _file.graphql_to_attachment(attachment)
            for attachment in data.get("blob_attachments") or ()
        ]
        unsent = False
        if data.get("extensible_attachment") is not None:
            attachment = graphql_to_extensible_attachment(data["extensible_attachment"])
            if isinstance(attachment, _attachment.UnsentMessage):
                unsent = True
            elif attachment:
                attachments.append(attachment)

        replied_to = None
        if data.get("replied_to_message") and data["replied_to_message"]["message"]:
            # data["replied_to_message"]["message"] is None if the message is deleted
            replied_to = cls._from_graphql(
                thread, data["replied_to_message"]["message"]
            )

        return cls(
            thread=thread,
            id=str(data["message_id"]),
            author=str(data["message_sender"]["id"]),
            created_at=created_at,
            text=data["message"].get("text"),
            mentions=[
                Mention._from_range(m) for m in data["message"].get("ranges") or ()
            ],
            emoji_size=EmojiSize._from_tags(tags),
            is_read=not data["unread"] if data.get("unread") is not None else None,
            read_by=[
                receipt["actor"]["id"]
                for receipt in read_receipts or ()
                if _util.millis_to_datetime(int(receipt["watermark"])) >= created_at
            ],
            reactions={
                str(r["user"]["id"]): r["reaction"] for r in data["message_reactions"]
            },
            sticker=_sticker.Sticker._from_graphql(data.get("sticker")),
            attachments=attachments,
            quick_replies=cls._parse_quick_replies(data.get("platform_xmd_encoded")),
            unsent=unsent,
            reply_to_id=replied_to.id if replied_to else None,
            replied_to=replied_to,
            forwarded=cls._get_forwarded_from_tags(tags),
        )

    @classmethod
    def _from_reply(cls, thread, data):
        tags = data["messageMetadata"].get("tags")
        metadata = data.get("messageMetadata", {})

        attachments = []
        unsent = False
        sticker = None
        for attachment in data.get("attachments") or ():
            attachment = _util.parse_json(attachment["mercuryJSON"])
            if attachment.get("blob_attachment"):
                attachments.append(
                    _file.graphql_to_attachment(attachment["blob_attachment"])
                )
            if attachment.get("extensible_attachment"):
                extensible_attachment = graphql_to_extensible_attachment(
                    attachment["extensible_attachment"]
                )
                if isinstance(extensible_attachment, _attachment.UnsentMessage):
                    unsent = True
                else:
                    attachments.append(extensible_attachment)
            if attachment.get("sticker_attachment"):
                sticker = _sticker.Sticker._from_graphql(
                    attachment["sticker_attachment"]
                )

        return cls(
            thread=thread,
            id=metadata.get("messageId"),
            author=str(metadata["actorFbId"]),
            created_at=_util.millis_to_datetime(metadata["timestamp"]),
            text=data.get("body"),
            mentions=[
                Mention._from_prng(m)
                for m in _util.parse_json(data.get("data", {}).get("prng", "[]"))
            ],
            emoji_size=EmojiSize._from_tags(tags),
            sticker=sticker,
            attachments=attachments,
            quick_replies=cls._parse_quick_replies(data.get("platform_xmd_encoded")),
            unsent=unsent,
            reply_to_id=data["messageReply"]["replyToMessageId"]["id"]
            if "messageReply" in data
            else None,
            forwarded=cls._get_forwarded_from_tags(tags),
        )

    @classmethod
    def _from_pull(cls, thread, data, author, created_at):
        metadata = data["messageMetadata"]

        tags = metadata.get("tags")

        mentions = []
        if data.get("data") and data["data"].get("prng"):
            try:
                mentions = [
                    Mention._from_prng(m)
                    for m in _util.parse_json(data["data"]["prng"])
                ]
            except Exception:
                log.exception("An exception occured while reading attachments")

        attachments = []
        unsent = False
        sticker = None
        try:
            for a in data.get("attachments") or ():
                mercury = a["mercury"]
                if mercury.get("blob_attachment"):
                    image_metadata = a.get("imageMetadata", {})
                    attach_type = mercury["blob_attachment"]["__typename"]
                    attachment = _file.graphql_to_attachment(
                        mercury["blob_attachment"], a.get("fileSize")
                    )
                    attachments.append(attachment)

                elif mercury.get("sticker_attachment"):
                    sticker = _sticker.Sticker._from_graphql(
                        mercury["sticker_attachment"]
                    )

                elif mercury.get("extensible_attachment"):
                    attachment = graphql_to_extensible_attachment(
                        mercury["extensible_attachment"]
                    )
                    if isinstance(attachment, _attachment.UnsentMessage):
                        unsent = True
                    elif attachment:
                        attachments.append(attachment)

        except Exception:
            log.exception(
                "An exception occured while reading attachments: {}".format(
                    data["attachments"]
                )
            )

        return cls(
            thread=thread,
            id=metadata["messageId"],
            author=author,
            created_at=created_at,
            text=data.get("body"),
            mentions=mentions,
            emoji_size=EmojiSize._from_tags(tags),
            sticker=sticker,
            attachments=attachments,
            unsent=unsent,
            forwarded=cls._get_forwarded_from_tags(tags),
        )


def graphql_to_extensible_attachment(data):
    story = data.get("story_attachment")
    if not story:
        return None

    target = story.get("target")
    if not target:
        return _attachment.UnsentMessage(id=data.get("legacy_attachment_id"))

    _type = target["__typename"]
    if _type == "MessageLocation":
        return _location.LocationAttachment._from_graphql(story)
    elif _type == "MessageLiveLocation":
        return _location.LiveLocationAttachment._from_graphql(story)
    elif _type in ["ExternalUrl", "Story"]:
        return _attachment.ShareAttachment._from_graphql(story)

    return None
