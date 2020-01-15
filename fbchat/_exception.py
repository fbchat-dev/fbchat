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
class GraphQLError(ExternalError):
    """Raised by Facebook if there was an error in the GraphQL query."""

    # TODO: Add `summary`, `severity` and `description`
    # TODO: Handle multiple errors


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


def handle_payload_error(j):
    if "error" not in j:
        return
    code = j["error"]
    if code == 1357001:
        error_cls = NotLoggedIn
    elif code == 1357004:
        error_cls = PleaseRefresh
    elif code in (1357031, 1545010, 1545003):
        error_cls = InvalidParameters
    else:
        error_cls = ExternalError
    # TODO: Use j["errorSummary"]
    # "errorDescription" is in the users own language!
    raise error_cls(
        "Error sending request: {}".format(j["errorDescription"]), code=code
    )


def handle_graphql_errors(j):
    errors = []
    if j.get("error"):
        errors = [j["error"]]
    if "errors" in j:
        errors = j["errors"]
    if errors:
        error = errors[0]  # TODO: Handle multiple errors
        # TODO: Use `summary`, `severity` and `description`
        raise GraphQLError(
            "GraphQL error: {} / {!r}".format(
                error.get("message"), error.get("debug_info")
            ),
            code=error.get("code"),
        )


def handle_http_error(code):
    msg = "Error when sending request: Got {} response.".format(code)
    if code == 404:
        raise HTTPError(
            msg + " This is either because you specified an invalid URL, or because"
            " you provided an invalid id (Facebook usually require integer ids)",
            status_code=code,
        )
    if 400 <= code < 600:
        raise HTTPError(msg, status_code=code)
