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


@pytest.mark.parametrize("exception,code,summary,description", ERROR_DATA)
def test_handle_payload_error(exception, code, summary, description):
    data = {"error": code, "errorSummary": summary, "errorDescription": description}
    with pytest.raises(exception, match=r"#\d+ .+:"):
        handle_payload_error(data)


def test_handle_not_logged_in_error():
    data = {
        "error": 1357001,
        "errorSummary": "Not logged in",
        "errorDescription": "Please log in to continue.",
    }
    with pytest.raises(NotLoggedIn, match="Not logged in"):
        handle_payload_error(data)


def test_handle_payload_error_no_error():
    assert handle_payload_error({}) is None
    assert handle_payload_error({"payload": {"abc": ["Something", "else"]}}) is None


def test_handle_graphql_crash():
    error = {
        "allow_user_retry": False,
        "api_error_code": -1,
        "code": 1675030,
        "debug_info": None,
        "description": "Error performing query.",
        "fbtrace_id": "ABCDEFG",
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
    with pytest.raises(
        GraphQLError, match="#1675030 Query error: Errors while executing"
    ):
        handle_graphql_errors({"data": {"message_thread": None}, "errors": [error]})


def test_handle_graphql_invalid_values():
    error = {
        "message": (
            'Invalid values provided for variables of operation "MessengerThreadlist":'
            ' Value ""as"" cannot be used for variable "$limit": Expected an integer'
            ' value, got "as".'
        ),
        "severity": "CRITICAL",
        "code": 1675012,
        "api_error_code": None,
        "summary": "Your request couldn't be processed",
        "description": (
            "There was a problem with this request."
            " We're working on getting it fixed as soon as we can."
        ),
        "is_silent": False,
        "is_transient": False,
        "requires_reauth": False,
        "allow_user_retry": False,
        "debug_info": None,
        "query_path": None,
        "fbtrace_id": "ABCDEFG",
        "www_request_id": "AABBCCDDEEFFGG",
    }
    msg = "#1675012 Your request couldn't be processed: Invalid values"
    with pytest.raises(GraphQLError, match=msg):
        handle_graphql_errors({"errors": [error]})


def test_handle_graphql_no_message():
    error = {
        "code": 1675012,
        "api_error_code": None,
        "summary": "Your request couldn't be processed",
        "description": (
            "There was a problem with this request."
            " We're working on getting it fixed as soon as we can."
        ),
        "is_silent": False,
        "is_transient": False,
        "requires_reauth": False,
        "allow_user_retry": False,
        "debug_info": None,
        "query_path": None,
        "fbtrace_id": "ABCDEFG",
        "www_request_id": "AABBCCDDEEFFGG",
        "sentry_block_user_info": None,
        "help_center_id": None,
    }
    msg = "#1675012 Your request couldn't be processed: "
    with pytest.raises(GraphQLError, match=msg):
        handle_graphql_errors({"errors": [error]})


def test_handle_graphql_no_summary():
    error = {
        "message": (
            'Errors while executing operation "MessengerViewerContactMethods":'
            " At Query.viewer:Viewer.all_emails: Field implementation threw an"
            " exception. Check your server logs for more information."
        ),
        "severity": "ERROR",
        "path": ["viewer", "all_emails"],
    }
    with pytest.raises(GraphQLError, match="Unknown error: Errors while executing"):
        handle_graphql_errors(
            {"data": {"viewer": {"user": None, "all_emails": []}}, "errors": [error]}
        )


def test_handle_graphql_syntax_error():
    error = {
        "code": 1675001,
        "api_error_code": None,
        "summary": "Query Syntax Error",
        "description": "Syntax error.",
        "is_silent": True,
        "is_transient": False,
        "requires_reauth": False,
        "allow_user_retry": False,
        "debug_info": 'Unexpected ">" at character 328: Expected ")".',
        "query_path": None,
        "fbtrace_id": "ABCDEFG",
        "www_request_id": "AABBCCDDEEFFGG",
        "sentry_block_user_info": None,
        "help_center_id": None,
    }
    msg = "#1675001 Query Syntax Error: "
    with pytest.raises(GraphQLError, match=msg):
        handle_graphql_errors({"response": None, "error": error})


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
