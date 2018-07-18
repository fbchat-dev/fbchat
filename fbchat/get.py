# -*- coding: UTF-8 -*-

from __future__ import unicode_literals
from .base import Base


class Get(Base):
    """Enables retrieving information about threads and messages"""

    def get_threads(self, limit=None):
        """Retrieve the threads that the client is currently chatting with

        If ``limit`` is ``None``, the result will be a generator, otherwise the
        result will be a list with maximum length of ``limit``

        Args:
            limit (int): Max. number of threads to retrieve

        Return:
            List of `Thread` objects or a generator yielding `Thread` objects
        """

    def get_archived_threads(self, limit=None):
        """Retrieve the client's archived threads

        ``limit`` and return values behave as in `get_messages`
        """

    def get_filtered_threads(self, limit=None):
        """Retrieve the client's filtered threads

        ``limit`` and return values behave as in `get_messages`
        """

    def get_unread_threads(self, limit=None):
        """Retrieve the client's unread threads

        ``limit`` and return values behave as in `get_messages`
        """

    def get_friends(self, limit=None):
        """Retrieve the users that the client is friends with

        ``limit`` and return values behave as in `get_messages`
        """


    def get_threads_from_ids(self, *thread_ids):
        """Retrieve threads based on their IDs

        If ``thread_ids`` contains a single iterable, then a generator yielding
        the threads is returned.

        If ``thread_ids`` is a single value or multiple values, then a list
        containing the threads is returned.

        Args:
            *thread_ids: One or more thread IDs to query

        Return:
            `Thread` objects, in the order and format their IDs were supplied
        """

    def get_messages_from_ids(self, *message_ids):
        """Retrieve messages based on their IDs

        If ``message_ids`` contains a single iterable, then a generator
        yielding the messages is returned.

        If ``message_ids`` is a single value or multiple values, then a list
        containing the messages is returned.

        Args:
            *message_ids: One or more message IDs to query

        Return:
            `Message` objects, in the order and format their IDs were supplied
        """


    def get_messages(self, thread, limit=None):
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

    def get_messages_before(self, message, limit=None):
        """Retrieve messages *before* a specific message

        ``limit`` and return values behave as in `get_messages`

        Args:
            message (`Message`): A message, indicating from which point to
                retrieve messages
        """

    def get_messages_after(self, message, limit=None):
        """Retrieve messages *after* a specific message

        ``limit`` and return values behave as in `get_messages`

        Args:
            message (`Message`): A message, indicating from which point to
                retrieve messages
        """


    def get_thread_images(self, thread, limit=None):
        """Retrieve sent images in a thread

        Like in `get_threads`, if ``limit`` is ``None``, the result will be a
        generator, otherwise the result will be a list with maximum length of
        ``limit``

        Args:
            thread (`Thread`): Thread to fetch images from
            limit (int): Max. number of images to retrieve

        Return:
            List of `ImageAttachment` objects or a generator yielding
            `ImageAttachment` objects
        """

    def get_thread_files(self, thread, limit=None):
        """Retrieve sent files in a thread

        ``limit`` and return values behave as in `get_messages`

        Args:
            thread (`Thread`): Thread to fetch files from

        Return:
            List of `FileAttachment` objects or a generator yielding
            `FileAttachment` objects
        """

    def get_url(self, attachment):
        """Fetch an url from an attachment, where you can download the original

        Args:
            attachment (`Attachment`): The attachment to be fetched

        Return:
            An url where you can download the original attachment
        """
