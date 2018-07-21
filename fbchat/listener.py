# -*- coding: UTF-8 -*-

from __future__ import unicode_literals

from .base import Base


class Listener(Base):
    """Enables basic listening"""

    def listen(self):
        """Start listening for incoming messages or events

        When this method recieves a message/an event, it will parse the
        message/event, and call the corresponding `on_` method
        """

    def stop_listen(self):
        """Stop the event listener"""


    def init_listener(self):
        """Prepare the event listener.

        This method is useful if you want to control the listener from an
        external event loop
        """

    def step_listener(self):
        """Do one cycle of the listening loop.

        This method is useful if you want to control the listener from an
        external event loop
        """

    def clean_listener(self):
        """Cleanup the event listener.

        This method is useful if you want to control the listener from an
        external event loop
        """


    def on_error(self, exception, msg):
        """Called when an error was encountered while listening

        Args:
            exception (Exception): The exception that was encountered
            msg (dict): Dictionary containing the full json data recieved
        """

    def on_unknown(self, msg):
        """Called when some unknown data was recieved while listening

        Useful for debugging, and figuring out missing features

        Args:
            msg (dict): Dictionary containing the full json data recieved
        """

    def on_raw(self, msg):
        """Called when data is recieved while listening

        This method is overwritten by other classes, to parse the relevant data

        Args:
            msg (dict): Dictionary containing the full json data recieved
        """
