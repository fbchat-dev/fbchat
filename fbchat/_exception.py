import attr

# Not frozen, since that doesn't work in PyPy
attrs_exception = attr.s(slots=True, auto_exc=True)


@attrs_exception
class FacebookError(Exception):
    """Base class for all custom exceptions raised by ``fbchat``.

    All exceptions in the module inherit this.
    """

    message = attr.ib(type=str)


@attrs_exception
class HTTPError(FacebookError):
    """Base class for errors with the HTTP(s) connection to Facebook."""

    status_code = attr.ib(None, type=int)


@attrs_exception
class ParseError(FacebookError):
    """Raised when we fail parsing a response from Facebook.

    This may contain sensitive data, so should not be logged to file.
    """

    data = attr.ib()
    """The data that triggered the error.

    The format of this cannot be relied on, it's only for debugging purposes.
    """

    def __str__(self):
        msg = "{}. Please report this, and the associated data: {}"
        return msg.format(self.message, self.data)


@attrs_exception
class ExternalError(FacebookError):
    """Base class for errors that Facebook return."""

    #: The error message that Facebook returned (In the user's own language)
    message = attr.ib(type=str)
    #: The error code that Facebook returned
    code = attr.ib(None, type=int)

    def __str__(self):
        if self.code:
            return "#{}: {}".format(self.code, self.message)
        return self.message


@attrs_exception
class InvalidParameters(ExternalError):
    """Raised by Facebook if:

    - Some function supplied invalid parameters.
    - Some content is not found.
    - Some content is no longer available.
    """


@attrs_exception
class NotLoggedIn(ExternalError):
    """Raised by Facebook if the client has been logged out."""

    code = attr.ib(1357001)


@attrs_exception
class PleaseRefresh(ExternalError):
    """Raised by Facebook if the client has been inactive for too long.

    This error usually happens after 1-2 days of inactivity.
    """

    code = attr.ib(1357004)
    message = attr.ib("Please try closing and re-opening your browser window.")
