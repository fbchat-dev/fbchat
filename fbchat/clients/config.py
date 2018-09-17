# -*- coding: UTF-8 -*-

from __future__ import unicode_literals

from .cache import CacherClient


__all__ = ("ThreadConfigurerClient",)


class ThreadConfigurerClient(CacherClient):
    """Enables the client to configure threads"""

    def archive(self, thread):
        """Archive a thread

        Args:
            thread (`Thread`): Thread to archive
        """


    def ignore(self, thread):
        """Ignore a thread

        Args:
            thread (`Thread`): Thread to ignore
        """

    def unignore(self, thread):
        """Unignore a thread

        Args:
            thread (`Thread`): Thread to stop ignoring
        """


    def mute(self, thread, time=None):
        """Mute a thread for a specific amount of time

        If ``time`` is ``None``, the thread will be muted indefinitely

        Args:
            thread (`Thread`): Thread to mute
            time (float): Amount of time to mute the thread, in seconds
        """

    def unmute(self, thread):
        """Unmute a thread

        Args:
            thread (`Thread`): Thread to unmute
        """


    def mute_reactions(self, thread):
        """Mute reactions in a thread

        Args:
            thread (`Thread`): Thread to mute reactions in
        """

    def unmute_reactions(self, thread):
        """Unmute reactions in a thread

        Args:
            thread (`Thread`): Thread to unmute reactions in
        """


    def mute_mentions(self, thread):
        """Mute mentions in a thread

        Args:
            thread (`Thread`): Thread to mute mentions in
        """

    def unmute_mentions(self, thread):
        """Unmute mentions in a thread

        Args:
            thread (`Thread`): Thread to unmute mentions in
        """
