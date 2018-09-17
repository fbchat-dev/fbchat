# -*- coding: UTF-8 -*-

from __future__ import unicode_literals
from .fetch import FetcherClient


class GetterClient(FetcherClient):
    """Enables retrieving information about threads and messages"""

    def get_threads(self, limit=None):
        """Retrieve the threads that the client is currently chatting with

        Args:
            limit (int): Max. number of threads to retrieve

        Return:
            A generator yielding `Thread`\s
        """

    def get_archived_threads(self, limit=None):
        """Retrieve the client's archived threads

        Args:
            limit (int): Max. number of threads to retrieve

        Return:
            A generator yielding `Thread`\s
        """

    def get_filtered_threads(self, limit=None):
        """Retrieve the client's filtered threads

        Args:
            limit (int): Max. number of threads to retrieve

        Return:
            A generator yielding `Thread`\s
        """

    def get_unread_threads(self, limit=None):
        """Retrieve the client's unread threads

        Args:
            limit (int): Max. number of threads to retrieve

        Return:
            A generator yielding `Thread`\s
        """

    def get_friends(self, limit=None):
        """Retrieve the users that the client is friends with

        Args:
            limit (int): Max. number of users to retrieve

        Return:
            A generator yielding `User`\s
        """


    def get_threads_from_ids(self, thread_ids):
        """Retrieve threads based on their IDs

        Args:
            thread_ids (iter): Thread IDs to query

        Return:
            A generator yielding `Thread`\s, in the order and format their IDs were supplied
        """


    def get_events(self, thread, limit=None):
        """Retrieve events in a thread, starting from the newest

        Args:
            thread (`Thread`): Thread to retrieve events from
            limit (int): Max. number of events to retrieve

        Return:
            A generator yielding `Event`\s
        """

    def get_events_before(self, event, limit=None):
        """Retrieve events *before* a specific event

        Args:
            event (`Event`): A event, indicating from which point to retrieve events
            limit (int): Max. number of events to retrieve

        Return:
            A generator yielding `Event`\s
        """

    def get_events_after(self, event, limit=None):
        """Retrieve events *after* a specific event

        Args:
            event (`Event`): An event, indicating from which point to retrieve events
            limit (int): Max. number of events to retrieve

        Return:
            A generator yielding `Event`\s
        """

    '''
    def get_thread_images(self, thread, limit=None):
        """Retrieve sent images in a thread

        Args:
            thread (`Thread`): Thread to fetch images from
            limit (int): Max. number of images to retrieve

        Return:
            A generator yielding `Image`\s
        """
    '''

    def get_thread_files(self, thread, limit=None):
        """Retrieve sent files in a thread

        ``limit`` and return values behave as in `get_messages`

        Args:
            thread (`Thread`): Thread to fetch files from

        Return:
            A generator yielding `File`\s
        """

    def get_url(self, attachment):
        """Retrieve a url from an attachment / a file, where you can download the original

        Args:
            attachment (`File`): The attachment / file to be fetched

        Return:
            An url where you can download the original attachment
        """
