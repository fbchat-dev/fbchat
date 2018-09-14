# -*- coding: UTF-8 -*-

from __future__ import unicode_literals

import logging

from .listen import ListenerClient
from .models import Message, Sticker, AnimatedSticker, Emoji, Text, FileMessage

log = logging.getLogger(__name__)


class SenderClient(ListenerClient):
    """Enables sending various messages to threads

    Every method in this class, except `send`, `on_message` and `upload`, are
    shortcuts of the aforementioned

    Attributes:
        sent_messages (list): All messages sent by the client
    """

    def send(self, thread, message):
        """Send the contents specified in a message object to a thread

        If ``message.thread``, ``message.actor`` or ``message.id`` is set, they will be
        ignored (Which means it's safe to send a previously recieved message)

        Args:
            thread (`Thread`): Thread to send the message to
            message (`Message`): Message to send

        Return:
            New `Message`, denoting the sent message
        """

    def on_event(self, event):
        super(SenderClient, self).on_event(event)
        if isinstance(event, Message):
            self.on_message(event)

    def on_message(self, message):
        """Called when someone sends a message

        Args:
            message (`Message`): Message that was sent
        """
        if isinstance(message, Text):
            self.on_text(message.thread, message.actor, message.text, message.mentions)
        elif isinstance(message, Emoji):
            self.on_emoji(message.thread, message.actor, message.emoji, message.size)

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

    def send_text(self, thread, text, mentions=None):
        """Send a piece of text to a thread. Shortcut of `send`

        If ``mentions`` is ``None``, it will act like an empty list

        Args:
            thread (`Thread`): Thread to send the text to
            text: Text to send
            mentions (list): `Mention` objects

        Return:
            `Message`, denoting the sent message
        """
        return self.send(thread, Text(text=text, mentions=mentions))

    def on_text(self, thread, actor, text, mentions):
        """Called when text is recieved. Shortcut of `on_message`

        Args:
            thread (`Thread`): Thread that the text was sent to
            actor (`Thread`): User that sent the text
            text: Text that was sent
            mentions (list): `Mention` objects
        """
        log.info("Recieved %s, %s in %s, sent by %s", text, mentions, thread, actor)

    def send_emoji(self, thread, emoji=None, size=Emoji.Size.SMALL):
        """Send a emoji to a thread. Shortcut of `send`

        If ``emoji`` is ``None``, the thread's default emoji will be sent

        Args:
            thread (`Thread`): Thread to send the emoji to
            emoji: Emoji to send
            size (`Emoji.Size`): Size of the emoji

        Return:
            `Message`, denoting the sent message
        """
        return self.send(thread, Emoji(emoji=emoji, size=size))

    def on_emoji(self, thread, actor, emoji, size):
        """Called when an emoji is recieved. Shortcut of `on_message`

        Args:
            thread (`Thread`): Thread that the emoji was sent to
            actor (`Thread`): User that sent the emoji
            emoji: Emoji that was sent
            size (`Size`): Size of the sent emoji
        """
        log.info("Recieved %s, %s in %s, sent by %s", emoji, size, thread, actor)

    def send_file(self, thread, path, name=None):
        """Send a file to a thread. Shortcut combination of `send` and `upload`

        Args:
            thread: Thread to send the files to
            path: Path to the file which should be sent
            name: Name of the file which is sent

        Return:
            `Message`, denoting the sent message
        """
        return self.send(thread, self.upload(path, name))

    # More shortcuts could be added
