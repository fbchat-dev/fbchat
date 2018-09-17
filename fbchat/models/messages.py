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

    def to_send(self, **kwargs):
        return super(Message, self).to_send(
            action_type="ma-type:user-generated-message", **kwargs
        )


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

    @staticmethod
    def graphql_data(data, **kwargs):
        return dict(
            sticker_id=data["id"],
            name=data["label"],
            url=data["url"],
            dimensions=Dimension.from_dict(data),
            pack=Sticker.Pack(data["pack"]["id"]),
            **kwargs
        )

    @classmethod
    def from_pull(cls, delta, **kwargs):
        attachment, = [x["mercury"]["sticker_attachment"] for x in delta["attachments"]]
        data = cls.graphql_data(attachment, **kwargs)
        return super(Sticker, cls).from_pull(delta, **data)

    def to_send(self, **kwargs):
        return super(Sticker, self).to_send(sticker_id=self.sticker_id, **kwargs)

    @classmethod
    def from_send(cls, action, old, **kwargs):
        payload, = action["graphql_payload"]
        data = cls.graphql_data(payload["node"], **kwargs)
        return super(Sticker, cls).from_send(action, old, **data)

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

    @staticmethod
    def graphql_data(data, **kwargs):
        return super(AnimatedSticker, cls).graphql_data(
            data,
            sprite_image=data["sprite_image"]["uri"],
            large_sprite_image=data["sprite_image_2x"].get("uri"),
            frames_per_row=int(data["frames_per_row"]),
            frames_per_col=int(data["frames_per_column"]),
            frame_rate=int(data["frame_rate"]),
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

    def to_send(self, **kwargs):
        data = super(Emoji, self).to_send(body=self.emoji, **kwargs)

        data["tags[0]"] = "hot_emoji_size:{}".format(self.size.value)

        return data

    @classmethod
    def from_send(cls, action, old, **kwargs):
        return super(Emoji, cls).from_send(
            action, old, emoji=old.emoji, size=old.size, **kwargs
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
    def mentions_from_prng(cls, data):
        if data and data.get("prng"):
            prng = json.loads(data["prng"])
            return sorted(map(cls.Mention.from_prng, prng), key=lambda x: x.offset)
        return list()

    @classmethod
    def from_pull(cls, delta, **kwargs):
        return super(Text, cls).from_pull(
            delta,
            text=delta["body"],
            mentions=cls.mentions_from_prng(delta.get("data")),
            **kwargs
        )

    def to_send(self, **kwargs):
        data = super(Text, self).to_send(body=self.text, **kwargs)

        for i, mention in enumerate(self.mentions):
            data["profile_xmd[{}][id]".format(i)] = mention.thread.id
            data["profile_xmd[{}][offset]".format(i)] = mention.offset
            data["profile_xmd[{}][length]".format(i)] = mention.length
            data["profile_xmd[{}][type]".format(i)] = "p"

        return data

    @classmethod
    def from_send(cls, action, old, **kwargs):
        return super(Text, cls).from_send(
            action, old, text=old.text, mentions=old.mentions, **kwargs
        )

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
        def from_prng(cls, data, **kwargs):
            return cls(Thread(data["i"]), offset=data["o"], length=data["l"], **kwargs)


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

    @staticmethod
    def mimetype_to_key(mimetype):
        if not mimetype:
            return "file_id"
        if mimetype == "image/gif":
            return "gif_id"
        x = mimetype.split("/")
        if x[0] in ["video", "image", "audio"]:
            return "{}_id".format(x[0])
        return "file_id"

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

    def to_send(self, **kwargs):
        data = super(FileMessage, self).to_send(has_attachment=True, **kwargs)

        for i, file in enumerate(self.files):
            data["{}s[{}]".format(self.mimetype_to_key(file.mimetype), i)] = file.id

        return data

    @classmethod
    def from_send(cls, action, old, **kwargs):
        # TODO: Parse `action["graphql_payload"]` to retrieve updated file info
        return super(FileMessage, cls).from_send(action, old, files=old.files, **kwargs)
