# -*- coding: UTF-8 -*-

from __future__ import unicode_literals

from .listen import ListenerClient
from .models import Message, Emoji


class SenderClient(ListenerClient):
    """Enables sending various messages to threads

    Every method in this class, except `send`, `on_message` and `upload`, are
    shortcuts of the aforementioned

    Attributes:
        sent_messages (list): All messages sent by the client
    """

    def send(self, thread, message):
        """Send the contents specified in a message object to a thread

        If ``message.thread``, ``message.author`` or ``message.id`` is set,
        they will be ignored (Which means it's safe to send a previously
        recieved message)

        Args:
            thread (`Thread`): Thread to send the message to
            message (`Message`): Message to send

        Return:
            New `Message`, denoting the sent message
        """

    def on_event(self, event):
        if isinstance(event, Message):
            self.on_message(event)
        super(self, SenderClient).on_event(event)

    def on_message(self, message):
        """Called when someone sends a message

        Args:
            message (`Message`): Message that was sent
        """

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

    def on_text(self, thread, author, text, mentions):
        """Called when text is recieved. Shortcut of `on_message`

        Args:
            thread (`Thread`): Thread that the text was sent to
            author (`Thread`): User that sent the text
            text: Text that was sent
            mentions (list): `Mention` objects
        """

    def send_sticker(self, thread, sticker):
        """Send a sticker to a thread. Shortcut of `send`

        Args:
            thread (`Thread`): Thread to send the sticker to
            sticker (`Sticker`): Sticker to send

        Return:
            `Message`, denoting the sent message
        """

    def on_sticker(self, thread, author, sticker):
        """Called when a sticker is recieved. Shortcut of `on_message`

        Args:
            thread (`Thread`): Thread that the sticker was sent to
            author (`Thread`): User that sent the sticker
            sticker (`Sticker`): Sticker that was sent
        """

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

    def on_emoji(self, thread, author, emoji, size):
        """Called when an emoji is recieved. Shortcut of `on_message`

        Args:
            thread (`Thread`): Thread that the emoji was sent to
            author (`Thread`): User that sent the emoji
            emoji: Emoji that was sent
            size (`Size`): Size of the sent emoji
        """

    def send_file(self, thread, path, name=None):
        """Send a file to a thread. Shortcut combination of `send` and `upload`

        Args:
            thread: Thread to send the files to
            path: Path to the file which should be sent
            name: Name of the file which is sent

        Return:
            `Message`, denoting the sent message
        """

    def on_file(self, thread, author, file):
        """Called when a file is recieved. Shortcut of `on_message`

        Args:
            thread (`Thread`): Thread that the file was sent to
            author (`Thread`): User that sent the file
            file (`Attachment`): Recieved file
        """

    # More shortcuts could be added
