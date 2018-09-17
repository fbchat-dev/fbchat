# -*- coding: UTF-8 -*-

from __future__ import unicode_literals
from .cache import CacherClient


__all__ = ("SearcherClient",)


class SearcherClient(CacherClient):
    """Enables fetching information about threads"""

    def search_for_thread(self, name, limit=None):
        """Search for and retrieve threads by their name

        If ``limit`` is ``None``, the result will be a generator, otherwise the
        result will be a list with maximum length of ``limit``

        Args:
            name: Name of the thread you want to search for
            limit (int): The max. amount of threads to retrieve

        Return:
            List of `Thread` objects or a generator yielding `Thread` objects,
            ordered by relevance
        """

    def search_for_group(self, name, limit=None):
        """Search for and retrieve groups by their name

        Arguments behave as in `search_for_thread`

        Return:
            List of `Group` objects or a generator yielding `Group` objects,
            ordered by relevance
        """

    def search_for_page(self, name, limit=None):
        """Search for and retrieve pages by their name

        Arguments behave as in `search_for_thread`

        Return:
            List of `Page` objects or a generator yielding `Page` objects,
            ordered by relevance
        """

    def search_for_user(self, name, limit=None):
        """Search for and retrieve users by their name

        Arguments behave as in `search_for_thread`

        Return:
            List of `User` objects or a generator yielding `User` objects,
            ordered by relevance
        """

    def search_for_messages(self, thread, text, limit=None):
        """Search for and retrieve messages in a thread by their text-contents

        If ``limit`` is ``None``, the result will be a generator, otherwise the
        result will be a list with maximum length of ``limit``

        Args:
            thread: Thread to search in
            text: Text-content to search for
            limit (int): The max. amount of messages to retrieve

        Return:
            List of `Message` objects or a generator yielding `Message`
            objects, ordered by relevance
        """
