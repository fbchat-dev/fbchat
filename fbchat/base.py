# -*- coding: UTF-8 -*-

from __future__ import unicode_literals
from .models import User


class Base(User):
    """Base Facebook client"""

    def __init__(self, email, password, session=None, user_agent=None,
                 max_tries=5):
        """Initialize and login the Facebook client

        Args:
            email: Facebook `email`, `id` or `phone number`
            password: Facebook account password
            session (dict): Previous session to attempt to load
            user_agent: Custom user agent to use when sending requests. If
                ``None``, the user agent will be chosen randomly
            max_tries (int): Maximum number of times to try logging in
        """

    def logout(self):
        """Properly log out the client, invalidating the session

        Warning:
            Using the client after this method is called results in undefined
            behaviour
        """

    def is_logged_in(self):
        """Check the login status

        Return:
            Whether the client is still logged in
        """

    def on_2fa(self):
        """Will be called when a two-factor authentication code is needed

        By default, this will call ``input``, and wait for the authentication
        code

        Return:
            The expected return is a two-factor authentication code, or
            ``None`` if not available
        """

    def get_session(self):
        """Retrieve session

        The session can then be serialised, stored, and reused the next time
        the client wants to log in

        Return:
            A dict containing the session
        """

    def set_session(self, session):
        """Validate session and load it into the client

        Args:
            session (dict): A dictionay containing the session
        """
