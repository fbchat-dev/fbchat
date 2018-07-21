# -*- coding: UTF-8 -*-

from __future__ import unicode_literals
from .listener import Listener


class MessageManagement(Listener):
    """Enables the client to manage previous messages"""

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
