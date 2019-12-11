import attr
import json
from string import Formatter
from ._core import log, attrs_default, Enum
from . import _util, _attachment, _location, _file, _quick_reply, _sticker


class EmojiSize(Enum):
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
            data = tag.split(":", maxsplit=1)
            if len(data) > 1 and data[0] == "hot_emoji_size":
                return string_to_emojisize.get(data[1])
        return None


class MessageReaction(Enum):
    """Used to specify a message reaction."""

    HEART = "❤"
    LOVE = "😍"
    SMILE = "😆"
    WOW = "😮"
    SAD = "😢"
    ANGRY = "😠"
    YES = "👍"
    NO = "👎"


@attrs_default
class Mention:
    """Represents a ``@mention``."""

    #: The thread ID the mention is pointing at
    thread_id = attr.ib()
    #: The character where the mention starts
    offset = attr.ib(0)
    #: The length of the mention
    length = attr.ib(10)


@attrs_default
class Message:
    """Represents a Facebook message."""

    #: The actual message
    text = attr.ib(None)
    #: A list of :class:`Mention` objects
    mentions = attr.ib(factory=list)
    #: A :class:`EmojiSize`. Size of a sent emoji
    emoji_size = attr.ib(None)
    #: The message ID
    uid = attr.ib(None)
    #: ID of the sender
    author = attr.ib(None)
    #: Datetime of when the message was sent
    created_at = attr.ib(None)
    #: Whether the message is read
    is_read = attr.ib(None)
    #: A list of people IDs who read the message, works only with :func:`fbchat.Client.fetch_thread_messages`
    read_by = attr.ib(factory=list)
    #: A dictionary with user's IDs as keys, and their :class:`MessageReaction` as values
    reactions = attr.ib(factory=dict)
    #: A :class:`Sticker`
    sticker = attr.ib(None)
    #: A list of attachments
    attachments = attr.ib(factory=list)
    #: A list of :class:`QuickReply`
    quick_replies = attr.ib(factory=list)
    #: Whether the message is unsent (deleted for everyone)
    unsent = attr.ib(False)
    #: Message ID you want to reply to
    reply_to_id = attr.ib(None)
    #: Replied message
    replied_to = attr.ib(None)
    #: Whether the message was forwarded
    forwarded = attr.ib(False)

    @classmethod
    def format_mentions(cls, text, *args, **kwargs):
        """Like `str.format`, but takes tuples with a thread id and text instead.

        Return a `Message` object, with the formatted string and relevant mentions.

        >>> Message.format_mentions("Hey {!r}! My name is {}", ("1234", "Peter"), ("4321", "Michael"))
        <Message (None): "Hey 'Peter'! My name is Michael", mentions=[<Mention 1234: offset=4 length=7>, <Mention 4321: offset=24 length=7>] emoji_size=None attachments=[]>

        >>> Message.format_mentions("Hey {p}! My name is {}", ("1234", "Michael"), p=("4321", "Peter"))
        <Message (None): 'Hey Peter! My name is Michael', mentions=[<Mention 4321: offset=4 length=5>, <Mention 1234: offset=22 length=7>] emoji_size=None attachments=[]>
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

        return cls(text=result, mentions=mentions)

    @staticmethod
    def _get_forwarded_from_tags(tags):
        if tags is None:
            return False
        return any(map(lambda tag: "forward" in tag or "copy" in tag, tags))

    def _to_send_data(self):
        data = {}

        if self.text or self.sticker or self.emoji_size:
            data["action_type"] = "ma-type:user-generated-message"

        if self.text:
            data["body"] = self.text

        for i, mention in enumerate(self.mentions):
            data["profile_xmd[{}][id]".format(i)] = mention.thread_id
            data["profile_xmd[{}][offset]".format(i)] = mention.offset
            data["profile_xmd[{}][length]".format(i)] = mention.length
            data["profile_xmd[{}][type]".format(i)] = "p"

        if self.emoji_size:
            if self.text:
                data["tags[0]"] = "hot_emoji_size:" + self.emoji_size.name.lower()
            else:
                data["sticker_id"] = self.emoji_size.value

        if self.sticker:
            data["sticker_id"] = self.sticker.uid

        if self.quick_replies:
            xmd = {"quick_replies": []}
            for quick_reply in self.quick_replies:
                # TODO: Move this to `_quick_reply.py`
                q = dict()
                q["content_type"] = quick_reply._type
                q["payload"] = quick_reply.payload
                q["external_payload"] = quick_reply.external_payload
                q["data"] = quick_reply.data
                if quick_reply.is_response:
                    q["ignore_for_webhook"] = False
                if isinstance(quick_reply, _quick_reply.QuickReplyText):
                    q["title"] = quick_reply.title
                if not isinstance(quick_reply, _quick_reply.QuickReplyLocation):
                    q["image_url"] = quick_reply.image_url
                xmd["quick_replies"].append(q)
            if len(self.quick_replies) == 1 and self.quick_replies[0].is_response:
                xmd["quick_replies"] = xmd["quick_replies"][0]
            data["platform_xmd"] = json.dumps(xmd)

        if self.reply_to_id:
            data["replied_to_message_id"] = self.reply_to_id

        return data

    @staticmethod
    def _parse_quick_replies(data):
        if data:
            data = json.loads(data).get("quick_replies")
            if isinstance(data, list):
                return [_quick_reply.graphql_to_quick_reply(q) for q in data]
            elif isinstance(data, dict):
                return [_quick_reply.graphql_to_quick_reply(data, is_response=True)]
        return []

    @classmethod
    def _from_graphql(cls, data, read_receipts=None):
        if data.get("message_sender") is None:
            data["message_sender"] = {}
        if data.get("message") is None:
            data["message"] = {}
        tags = data.get("tags_list")

        created_at = _util.millis_to_datetime(int(data.get("timestamp_precise")))

        attachments = [
            _file.graphql_to_attachment(attachment)
            for attachment in data["blob_attachments"] or ()
        ]
        unsent = False
        if data.get("extensible_attachment") is not None:
            attachment = graphql_to_extensible_attachment(data["extensible_attachment"])
            if isinstance(attachment, _attachment.UnsentMessage):
                unsent = True
            elif attachment:
                attachments.append(attachment)

        replied_to = None
        if data.get("replied_to_message"):
            replied_to = cls._from_graphql(data["replied_to_message"]["message"])

        return cls(
            text=data["message"].get("text"),
            mentions=[
                Mention(
                    m.get("entity", {}).get("id"),
                    offset=m.get("offset"),
                    length=m.get("length"),
                )
                for m in data["message"].get("ranges") or ()
            ],
            emoji_size=EmojiSize._from_tags(tags),
            uid=str(data["message_id"]),
            author=str(data["message_sender"]["id"]),
            created_at=created_at,
            is_read=not data["unread"] if data.get("unread") is not None else None,
            read_by=[
                receipt["actor"]["id"]
                for receipt in read_receipts or ()
                if _util.millis_to_datetime(int(receipt["watermark"])) >= created_at
            ],
            reactions={
                str(r["user"]["id"]): MessageReaction._extend_if_invalid(r["reaction"])
                for r in data["message_reactions"]
            },
            sticker=_sticker.Sticker._from_graphql(data.get("sticker")),
            attachments=attachments,
            quick_replies=cls._parse_quick_replies(data.get("platform_xmd_encoded")),
            unsent=unsent,
            reply_to_id=replied_to.uid if replied_to else None,
            replied_to=replied_to,
            forwarded=cls._get_forwarded_from_tags(tags),
        )

    @classmethod
    def _from_reply(cls, data, replied_to=None):
        tags = data["messageMetadata"].get("tags")
        metadata = data.get("messageMetadata", {})

        attachments = []
        unsent = False
        sticker = None
        for attachment in data.get("attachments") or ():
            attachment = json.loads(attachment["mercuryJSON"])
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
            text=data.get("body"),
            mentions=[
                Mention(m.get("i"), offset=m.get("o"), length=m.get("l"))
                for m in json.loads(data.get("data", {}).get("prng", "[]"))
            ],
            emoji_size=EmojiSize._from_tags(tags),
            uid=metadata.get("messageId"),
            author=str(metadata.get("actorFbId")),
            created_at=_util.millis_to_datetime(metadata.get("timestamp")),
            sticker=sticker,
            attachments=attachments,
            quick_replies=cls._parse_quick_replies(data.get("platform_xmd_encoded")),
            unsent=unsent,
            reply_to_id=replied_to.uid if replied_to else None,
            replied_to=replied_to,
            forwarded=cls._get_forwarded_from_tags(tags),
        )

    @classmethod
    def _from_pull(cls, data, mid=None, tags=None, author=None, created_at=None):
        mentions = []
        if data.get("data") and data["data"].get("prng"):
            try:
                mentions = [
                    Mention(
                        str(mention.get("i")),
                        offset=mention.get("o"),
                        length=mention.get("l"),
                    )
                    for mention in _util.parse_json(data["data"]["prng"])
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
                        mercury["blob_attachment"], a["fileSize"]
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
            text=data.get("body"),
            mentions=mentions,
            emoji_size=EmojiSize._from_tags(tags),
            uid=mid,
            author=author,
            created_at=created_at,
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
        return _attachment.UnsentMessage(uid=data.get("legacy_attachment_id"))

    _type = target["__typename"]
    if _type == "MessageLocation":
        return _location.LocationAttachment._from_graphql(story)
    elif _type == "MessageLiveLocation":
        return _location.LiveLocationAttachment._from_graphql(story)
    elif _type in ["ExternalUrl", "Story"]:
        return _attachment.ShareAttachment._from_graphql(story)

    return None
