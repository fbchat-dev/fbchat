import attr

# Not frozen, since that doesn't work in PyPy
attrs_exception = attr.s(slots=True, auto_exc=True)


@attrs_exception
class FBchatException(Exception):
    """Custom exception thrown by ``fbchat``.

    All exceptions in the module inherits this.
    """

    message = attr.ib()


@attrs_exception
class FBchatFacebookError(FBchatException):
    """Raised when Facebook returns an error."""

    #: The error code that Facebook returned
    fb_error_code = attr.ib(None)
    #: The error message that Facebook returned (In the user's own language)
    fb_error_message = attr.ib(None)
    #: The status code that was sent in the HTTP response (e.g. 404) (Usually only set if not successful, aka. not 200)
    request_status_code = attr.ib(None)


@attrs_exception
class FBchatInvalidParameters(FBchatFacebookError):
    """Raised by Facebook if:

    - Some function supplied invalid parameters.
    - Some content is not found.
    - Some content is no longer available.
    """


@attrs_exception
class FBchatNotLoggedIn(FBchatFacebookError):
    """Raised by Facebook if the client has been logged out."""

    fb_error_code = attr.ib("1357001")


@attrs_exception
class FBchatPleaseRefresh(FBchatFacebookError):
    """Raised by Facebook if the client has been inactive for too long.

    This error usually happens after 1-2 days of inactivity.
    """

    fb_error_code = attr.ib("1357004")
    fb_error_message = attr.ib("Please try closing and re-opening your browser window.")
