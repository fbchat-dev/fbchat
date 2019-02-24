# -*- coding: UTF-8 -*-
from __future__ import unicode_literals


class FBchatException(Exception):
    """Custom exception thrown by fbchat. All exceptions in the fbchat module inherits this"""


class FBchatFacebookError(FBchatException):
    #: The error code that Facebook returned
    fb_error_code = None
    #: The error message that Facebook returned (In the user's own language)
    fb_error_message = None
    #: The status code that was sent in the http response (eg. 404) (Usually only set if not successful, aka. not 200)
    request_status_code = None

    def __init__(
        self,
        message,
        fb_error_code=None,
        fb_error_message=None,
        request_status_code=None,
    ):
        super(FBchatFacebookError, self).__init__(message)
        """Thrown by fbchat when Facebook returns an error"""
        self.fb_error_code = str(fb_error_code)
        self.fb_error_message = fb_error_message
        self.request_status_code = request_status_code


class FBchatUserError(FBchatException):
    """Thrown by fbchat when wrong values are entered"""
