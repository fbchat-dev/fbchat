import attr
import requests

from typing import Any, Optional

# Not frozen, since that doesn't work in PyPy
@attr.s(slots=True, auto_exc=True)
class FacebookError(Exception):
    """Base class for all custom exceptions raised by ``fbchat``.

    All exceptions in the module inherit this.
    """

    #: A message describing the error
    message = attr.ib(type=str)


@attr.s(slots=True, auto_exc=True)
class HTTPError(FacebookError):
    """Base class for errors with the HTTP(s) connection to Facebook."""

    #: The returned HTTP status code, if relevant
    status_code = attr.ib(None, type=Optional[int])

    def __str__(self):
        if not self.status_code:
            return self.message
        return "Got {} response: {}".format(self.status_code, self.message)


@attr.s(slots=True, auto_exc=True)
class ParseError(FacebookError):
    """Raised when we fail parsing a response from Facebook.

    This may contain sensitive data, so should not be logged to file.
    """

    data = attr.ib(type=Any)
    """The data that triggered the error.

    The format of this cannot be relied on, it's only for debugging purposes.
    """

    def __str__(self):
        msg = "{}. Please report this, along with the data below!\n{}"
        return msg.format(self.message, self.data)


@attr.s(slots=True, auto_exc=True)
class NotLoggedIn(FacebookError):
    """Raised by Facebook if the client has been logged out."""


@attr.s(slots=True, auto_exc=True)
class ExternalError(FacebookError):
    """Base class for errors that Facebook return."""

    #: The error message that Facebook returned (Possibly in the user's own language)
    description = attr.ib(type=str)
    #: The error code that Facebook returned
    code = attr.ib(None, type=Optional[int])

    def __str__(self):
        if self.code:
            return "#{} {}: {}".format(self.code, self.message, self.description)
        return "{}: {}".format(self.message, self.description)


@attr.s(slots=True, auto_exc=True)
class GraphQLError(ExternalError):
    """Raised by Facebook if there was an error in the GraphQL query."""

    # TODO: Handle multiple errors

    #: Query debug information
    debug_info = attr.ib(None, type=Optional[str])

    def __str__(self):
        if self.debug_info:
            return "{}, {}".format(super().__str__(), self.debug_info)
        return super().__str__()


@attr.s(slots=True, auto_exc=True)
class InvalidParameters(ExternalError):
    """Raised by Facebook if:

    - Some function supplied invalid parameters.
    - Some content is not found.
    - Some content is no longer available.
    """


@attr.s(slots=True, auto_exc=True)
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
        raise NotLoggedIn(j["errorSummary"])
    elif code == 1357004:
        error_cls = PleaseRefresh
    elif code in (1357031, 1545010, 1545003):
        error_cls = InvalidParameters
    else:
        error_cls = ExternalError
    raise error_cls(j["errorSummary"], description=j["errorDescription"], code=code)


def handle_graphql_errors(j):
    errors = []
    if j.get("error"):
        errors = [j["error"]]
    if "errors" in j:
        errors = j["errors"]
    if errors:
        error = errors[0]  # TODO: Handle multiple errors
        # TODO: Use `severity`
        raise GraphQLError(
            # TODO: What data is always available?
            message=error.get("summary", "Unknown error"),
            description=error.get("message") or error.get("description") or "",
            code=error.get("code"),
            debug_info=error.get("debug_info"),
        )


def handle_http_error(code):
    if code == 404:
        raise HTTPError(
            "This might be because you provided an invalid id"
            + " (Facebook usually require integer ids)",
            status_code=code,
        )
    if code == 500:
        raise HTTPError(
            "There is probably an error on the endpoint, or it might be rate limited",
            status_code=code,
        )
    if 400 <= code < 600:
        raise HTTPError("Failed sending request", status_code=code)


def handle_requests_error(e):
    if isinstance(e, requests.ConnectionError):
        raise HTTPError("Connection error") from e
    if isinstance(e, requests.HTTPError):
        pass  # Raised when using .raise_for_status, so should never happen
    if isinstance(e, requests.URLRequired):
        pass  # Should never happen, we always prove valid URLs
    if isinstance(e, requests.TooManyRedirects):
        pass  # TODO: Consider using allow_redirects=False to prevent this
    if isinstance(e, requests.Timeout):
        pass  # Should never happen, we don't set timeouts

    raise HTTPError("Requests error") from e
