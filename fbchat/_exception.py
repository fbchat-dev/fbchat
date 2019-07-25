# -*- coding: UTF-8 -*-
from __future__ import unicode_literals


class FBchatException(Exception):
    """Custom exception thrown by ``fbchat``.

    All exceptions in the ``fbchat`` module inherits this.
    """


class FBchatFacebookError(FBchatException):
    #: The error code that Facebook returned
    fb_error_code = None
    #: The error message that Facebook returned (In the user's own language)
    fb_error_message = None
    #: The status code that was sent in the HTTP response (e.g. 404) (Usually only set if not successful, aka. not 200)
    request_status_code = None

    def __init__(
        self,
        message,
        fb_error_code=None,
        fb_error_message=None,
        request_status_code=None,
    ):
        super(FBchatFacebookError, self).__init__(message)
        """Thrown by ``fbchat`` when Facebook returns an error"""
        self.fb_error_code = str(fb_error_code)
        self.fb_error_message = fb_error_message
        self.request_status_code = request_status_code


class FBchatInvalidParameters(FBchatFacebookError):
    """Raised by Facebook if:

    - Some function supplied invalid parameters.
    - Some content is not found.
    - Some content is no longer available.
    """


class FBchatNotLoggedIn(FBchatFacebookError):
    """Raised by Facebook if the client has been logged out."""

    fb_error_code = "1357001"


class FBchatPleaseRefresh(FBchatFacebookError):
    """Raised by Facebook if the client has been inactive for too long.

    This error usually happens after 1-2 days of inactivity.
    """

    fb_error_code = "1357004"
    fb_error_message = "Please try closing and re-opening your browser window."


class FBchatUserError(FBchatException):
    """Thrown by ``fbchat`` when wrong values are entered."""
