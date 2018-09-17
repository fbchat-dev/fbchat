# -*- coding: UTF-8 -*-

from __future__ import unicode_literals
from .core import CoreClient


class FetcherClient(CoreClient):
    """Enables retrieving information about threads and messages"""

    def fetch_messages(self, thread, limit=None, message=None, before=None, after=None):
        """Retrieve messages from a thread, starting from the newest

        Like in `get_threads`, if ``limit`` is ``None``, the result will be a
        generator, otherwise the result will be a list with maximum length of
        ``limit``

        Args:
            thread (`Thread`): Thread to retrieve messages from
            limit (int): Max. number of messages to retrieve

        Return:
            List of `Message` objects or a generator yielding `Message` objects
        """

    def fetch_messages_from_ids(self, message_ids):
        """Fetch messages based on their IDs

        Args:
            message_ids (iter): Message IDs to fetch

        Return:
            A generator yielding `Message`\s, in the order and format their IDs were supplied
        """
