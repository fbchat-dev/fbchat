import pytest
import requests
from fbchat import (
    FacebookError,
    HTTPError,
    ParseError,
    ExternalError,
    GraphQLError,
    InvalidParameters,
    NotLoggedIn,
    PleaseRefresh,
)
from fbchat._exception import (
    handle_payload_error,
    handle_graphql_errors,
    handle_http_error,
    handle_requests_error,
)


ERROR_DATA = [
    (NotLoggedIn, 1357001, "Not logged in", "Please log in to continue."),
    (
        PleaseRefresh,
        1357004,
        "Sorry, something went wrong",
        "Please try closing and re-opening your browser window.",
    ),
    (
        InvalidParameters,
        1357031,
        "This content is no longer available",
        (
            "The content you requested cannot be displayed at the moment. It may be"
            " temporarily unavailable, the link you clicked on may have expired or you"
            " may not have permission to view this page."
        ),
    ),
    (
        InvalidParameters,
        1545010,
        "Messages Unavailable",
        (
            "Sorry, messages are temporarily unavailable."
            " Please try again in a few minutes."
        ),
    ),
    (
        ExternalError,
        1545026,
        "Unable to Attach File",
        (
            "The type of file you're trying to attach isn't allowed."
            " Please try again with a different format."
        ),
    ),
    (InvalidParameters, 1545003, "Invalid action", "You cannot perform that action."),
    (
        ExternalError,
        1545012,
        "Temporary Failure",
        "There was a temporary error, please try again.",
    ),
]


@pytest.mark.parametrize("exception,code,description,summary", ERROR_DATA)
def test_handle_payload_error(exception, code, summary, description):
    data = {"error": code, "errorSummary": summary, "errorDescription": description}
    with pytest.raises(exception, match=r"#\d+: Error sending request"):
        handle_payload_error(data)


def test_handle_payload_error_no_error():
    assert handle_payload_error({}) is None
    assert handle_payload_error({"payload": {"abc": ["Something", "else"]}}) is None


def test_handle_graphql_errors():
    error = {
        "allow_user_retry": False,
        "api_error_code": -1,
        "code": 1675030,
        "debug_info": None,
        "description": "Error performing query.",
        "fbtrace_id": "CLkuLR752sB",
        "is_silent": False,
        "is_transient": False,
        "message": (
            'Errors while executing operation "MessengerThreadSharedLinks":'
            " At Query.message_thread: Field implementation threw an exception."
            " Check your server logs for more information."
        ),
        "path": ["message_thread"],
        "query_path": None,
        "requires_reauth": False,
        "severity": "CRITICAL",
        "summary": "Query error",
    }
    with pytest.raises(GraphQLError, match="#1675030: Errors while executing"):
        handle_graphql_errors({"data": {"message_thread": None}, "errors": [error]})


def test_handle_graphql_errors_singular_error_key():
    with pytest.raises(GraphQLError, match="#123"):
        handle_graphql_errors({"error": {"code": 123}})


def test_handle_graphql_errors_no_error():
    assert handle_graphql_errors({"data": {"message_thread": None}}) is None


def test_handle_http_error():
    with pytest.raises(HTTPError):
        handle_http_error(400)
    with pytest.raises(HTTPError):
        handle_http_error(500)


def test_handle_http_error_404_handling():
    with pytest.raises(HTTPError, match="invalid id"):
        handle_http_error(404)


def test_handle_http_error_no_error():
    assert handle_http_error(200) is None
    assert handle_http_error(302) is None


def test_handle_requests_error():
    with pytest.raises(HTTPError, match="Connection error"):
        handle_requests_error(requests.ConnectionError())
    with pytest.raises(HTTPError, match="Requests error"):
        handle_requests_error(requests.RequestException())
