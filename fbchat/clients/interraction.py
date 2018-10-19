# -*- coding: UTF-8 -*-

from __future__ import unicode_literals

from .listen import ListenerClient
from ..models import Action


__all__ = ("ThreadInterracterClient",)


class ThreadInterracterClient(ListenerClient):
    """Enables the client to interract with threads and listen on those events"""

    def on_event(self, event):
        if isinstance(event, Action):
            self.on_action(event)
        super(ThreadInterracterClient, self).on_event(event)

    def on_action(self, action):
        """Called when someone executes an action

        Args:
            action (`Action`): Action that was executed
        """

    def set_reaction(self, message, reaction=None):
        """React to a message

        If ``reaction`` is ``None``, the reaction will be removed

        Args:
            message (`Message`): Message to react to
            reaction: Reaction emoji to use. Can be one of 😍, 😆, 😮, 😢,
                😠, 👍, 👎 or ``None``
        """

    def on_reaction_set(self, message, actor, old_reaction):
        """Called when somebody reacts to/changes their reaction to a message

        Args:
            message (`Message`): Message that was reacted to
            actor (`Thread`): Person that caused the action
            old_reaction: Previous reaction emoji
        """

    def remove_message(self, message):
        """Remove/delete a message

        Warning:
            Facebook only deletes messages for the user that is deleting them.
            This means that others will still be able to view the message.

            Furthermore, this deletes the message without any further warning.
            Use with caution!

        Args:
            message (`Message`): Message to delete
        """

    def set_image(self, group, image=None):
        """Set a group's image

        Args:
            group (`Group`): Group whose image to change
            image: Path to image that will be uploaded and used as the new image
        """

    def on_image_set(self, group, actor, old_image):
        """Called when a group's image is set

        Args:
            group (`Group`): Group whose image was changed
            actor (`User`): Person that set the image
            old_image (`Image`): The previous image
        """

    def set_title(self, group, title=None):
        """Set a group's title

        If ``title`` is ``None``, then the title is removed

        Args:
            group (`Group`): Group whose title to change
            title: New title
        """

    def on_title_set(self, group, actor, old_title):
        """Called when a group's title is set

        Args:
            group (`Group`): Group whose title was changed
            actor (`User` or `Page`): Person that set the title
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
            actor (`User` or `Page`): Person that set the nickname
            subject (`User` or `Page`): Person whose nickname was changed
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
            actor (`User` or `Page`): Person that set the colour
            old_colour (`Colour`): The previous colour
        """

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
            actor (`User` or `Page`): Person that set the emoji
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
