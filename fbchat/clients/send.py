from .core import Core
from ..models import Message, Sticker, AnimatedSticker, Emoji, Text, FileMessage

log = logging.getLogger(__name__)


__all__ = ("MessageSending",)


class MessageSending(Core):
    """Enables sending various messages to channels"""

    def _send(self, channel: Channel, message: Message) -> Message:
        data = message.to_send()
        data.update(channel.to_send())

        j = self.session.post("/messaging/send/", data).json()

        action, = j["payload"]["actions"]
        return type(message).from_send(
            action, message, channel=channel, actor=self.user
        )

    def upload(self, paths, names=None):
        """Upload a set of files to Facebook, to later send them in messages

        If ``names`` is shorter than ``paths`` or ``None``, the remainding
        files will get default names. If it's longer, it's truncated

        Args:
            paths (list): Paths of the files to send
            names (list): Names of the files

        Return:
            `File`, denoting the uploaded file
        """

    def _get_message_type(self, delta):
        metadata = delta["messageMetadata"]

        if delta.get("attachments"):
            attachments = delta["attachments"]
            stickers = [x["mercury"].get("sticker_attachment") for x in attachments]
            if any(stickers):
                if stickers[0].get("sprite_image"):
                    return AnimatedSticker
                return Sticker
            return FileMessage

        if any(tag.startswith("hot_emoji_size:") for tag in metadata["tags"]):
            return Emoji

        return Text

    def parse_delta_data(self, delta, delta_type, delta_class):
        if delta_class == "NewMessage":
            return self._get_message_type(delta).from_pull(delta)

        return super(SenderClient, self).parse_delta_data(
            delta, delta_type, delta_class
        )

    def send_text(self, channel, text, mentions=None) -> TextMessage:
        """Send a piece of text to a channel. Shortcut of `send`

        If ``mentions`` is ``None``, it will act like an empty list

        Args:
            channel (`Channel`): Channel to send the text to
            text: Text to send
            mentions (list): `Mention` objects

        Return:
            The sent text message
        """
        return self._send(channel, Text(text=text, mentions=mentions))

    def send_emoji(self, channel, emoji=None, size=Emoji.Size.SMALL) -> Emoji:
        """Send a emoji to a channel. Shortcut of `send`

        If ``emoji`` is ``None``, the channel's default emoji will be sent

        Args:
            channel (`Channel`): Channel to send the emoji to
            emoji: Emoji to send
            size (`Emoji.Size`): Size of the emoji

        Return:
            The sent emoji
        """
        return self._send(channel, Emoji(emoji=emoji, size=size))

    def send_file(self, channel, path, name=None) -> FileMessage:
        """Send a file to a channel. Shortcut combination of `send` and `upload`

        Args:
            channel: Channel to send the files to
            path: Path to the file which should be sent
            name: Name of the file which is sent

        Return:
            The sent file message
        """
        return self._send(channel, self.upload(path, name))

    # More shortcuts could be added
