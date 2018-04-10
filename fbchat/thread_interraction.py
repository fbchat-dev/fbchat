# -*- coding: UTF-8 -*-

from __future__ import unicode_literals
from .listener import Listener


class ThreadInterraction(Listener):
    """Enables the client to interract with and listen on threads"""

    def set_image(self, thread, image):
        """Set a group's image

        Args:
            thread (`Thread`): Group whose image to change
            image (`Image`): New image
        """

    def on_image_set(self, thread, actor, old_image):
        """Called when a group's image is set

        Args:
            thread (`Thread`): Group whose image was changed
            actor (`Thread`): User that set the image
            old_image (`Image`): The previous image
        """

    def set_title(self, thread, title=None):
        """Set a group's title

        If ``title`` is ``None``, then the title is removed

        Args:
            thread (`Thread`): Group whose title to change
            title: New title
        """

    def on_title_set(self, thread, actor, old_title):
        """Called when a group's title is set

        Args:
            thread (`Thread`): Group whose title was changed
            actor (`Thread`): User that set the title
            old_title: The previous title
        """

    def set_nickname(self, thread, user, nickname=None):
        """Set the nickname of a user in a group

        If ``nickname`` is ``None``, then the nickname is removed

        Args:
            thread (`Thread`): Group in which the user's nickname will be set
            user (`Thread`): User whose nickname to change
            nickname: User's new nickname
        """

    def on_nickname_set(self, thread, actor, subject, old_nickname):
        """Called when a user's nickname is set in a group

        Args:
            thread (`Thread`): Group where the nickname was changed in
            actor (`Thread`): User that set the nickname
            subject (`Thread`): User whose nickname was changed
            old_nickname: The previous nickname
        """

    def set_colour(self, thread, colour):
        """Set a thread's colour

        Args:
            thread (`Thread`): Thread whose colour to change
            colour (`Colour`): New colour
        """

    def on_colour_set(self, thread, actor, old_colour):
        """Called when a group's colour is set

        Args:
            thread (`Thread`): Group whose colour was changed
            actor (`Thread`): User that set the colour
            old_colour (`Colour`): The previous colour
        """

    def set_color(self, thread, color):
        """Alias of `set_colour`"""

    def on_color_set(self, thread, actor, old_color):
        """Alias of `on_colour_set`"""

    def set_emoji(self, thread, emoji=None):
        """Set a thread's emoji

        Args:
            thread (`Thread`): Thread whose emoji to change
            emoji: New emoji
        """

    def on_emoji_set(self, thread, actor, old_emoji):
        """Called when a group's emoji is set

        Args:
            thread (`Thread`): Group whose emoji was changed
            actor (`Thread`): User that set the emoji
            old_emoji: The previous emoji
        """


    def start_typing(self, thread):
        """Notify the thread that the client is currently typing

        Args:
            thread (`Thread`): Thread to notify
        """

    def on_typing_started(self, thread, actor):
        """Called when someone starts typing in a thread

        Args:
            thread (`Thread`): Thread where the user started typing
            actor (`Thread`): User that started typing
        """

    def stop_typing(self, thread):
        """Notify the thread that the client is no longer typing

        Args:
            thread (`Thread`): Thread to notify
        """

    def on_typing_stopped(self, thread, actor):
        """Called when someone stops typing in a thread

        Args:
            thread (`Thread`): Thread where the user stopped typing
            actor (`Thread`): User that stopped typing
        """


    def mark_delivered(self, thread):
        """Notify the thread that the last messages have been delivered

        Args:
            thread (`Thread`): Thread to notify
        """

    def on_marked_delivered(self, thread, actor):
        """Called when the thread is notified that messages have been delivered

        Args:
            thread (`Thread`): Thread where the messages were delivered
            actor (`Thread`): User that marked the messages as delivered
        """

    def mark_read(self, thread):
        """Notify the thread that the last messages have been read

        Args:
            thread (`Thread`): Thread to notify
        """

    def on_marked_read(self, thread, actor):
        """Called when the thread is notified that messages have been read

        Args:
            thread (`Thread`): Thread where the messages were marked as read
            actor (`Thread`): User that marked the messages as read
        """

    def mark_unread(self, thread):
        """Notify the thread that the last messages have been marked as unread

        Args:
            thread (`Thread`): Thread to notify
        """

    def on_marked_unread(self, thread, actor):
        """Called when the thread is notified that messages have been unread

        Args:
            thread (`Thread`): Thread where the messages were marked as unread
            actor (`Thread`): User that marked the messages as unread
        """
