import pytest
import fbchat
import datetime
from fbchat._util import (
    strip_json_cruft,
    parse_json,
    str_base,
    generate_message_id,
    get_signature_id,
    handle_payload_error,
    handle_graphql_errors,
    check_http_code,
    get_jsmods_require,
    require_list,
    mimetype_to_key,
    get_url_parameter,
    prefix_url,
    seconds_to_datetime,
    millis_to_datetime,
    datetime_to_seconds,
    datetime_to_millis,
    seconds_to_timedelta,
    millis_to_timedelta,
    timedelta_to_seconds,
)


def test_strip_json_cruft():
    assert strip_json_cruft('for(;;);{"abc": "def"}') == '{"abc": "def"}'
    assert strip_json_cruft('{"abc": "def"}') == '{"abc": "def"}'


def test_strip_json_cruft_invalid():
    with pytest.raises(AttributeError):
        strip_json_cruft(None)
    with pytest.raises(fbchat.FBchatException, match="No JSON object found"):
        strip_json_cruft("No JSON object here!")


def test_parse_json():
    assert parse_json('{"a":"b"}') == {"a": "b"}


def test_parse_json_invalid():
    with pytest.raises(fbchat.FBchatFacebookError, match="Error while parsing JSON"):
        parse_json("No JSON object here!")


@pytest.mark.parametrize(
    "number,base,expected",
    [
        (123, 10, "123"),
        (1, 36, "1"),
        (10, 36, "a"),
        (123, 36, "3f"),
        (1000, 36, "rs"),
        (123456789, 36, "21i3v9"),
    ],
)
def test_str_base(number, base, expected):
    assert str_base(number, base) == expected


def test_generate_message_id():
    # Returns random output, so hard to test more thoroughly
    generate_message_id("abc")


def test_get_signature_id():
    # Returns random output, so hard to test more thoroughly
    get_signature_id()


ERROR_DATA = [
    (
        fbchat._exception.FBchatNotLoggedIn,
        1357001,
        "Not logged in",
        "Please log in to continue.",
    ),
    (
        fbchat._exception.FBchatPleaseRefresh,
        1357004,
        "Sorry, something went wrong",
        "Please try closing and re-opening your browser window.",
    ),
    (
        fbchat._exception.FBchatInvalidParameters,
        1357031,
        "This content is no longer available",
        (
            "The content you requested cannot be displayed at the moment. It may be"
            " temporarily unavailable, the link you clicked on may have expired or you"
            " may not have permission to view this page."
        ),
    ),
    (
        fbchat._exception.FBchatInvalidParameters,
        1545010,
        "Messages Unavailable",
        (
            "Sorry, messages are temporarily unavailable."
            " Please try again in a few minutes."
        ),
    ),
    (
        fbchat.FBchatFacebookError,
        1545026,
        "Unable to Attach File",
        (
            "The type of file you're trying to attach isn't allowed."
            " Please try again with a different format."
        ),
    ),
    (
        fbchat._exception.FBchatInvalidParameters,
        1545003,
        "Invalid action",
        "You cannot perform that action.",
    ),
    (
        fbchat.FBchatFacebookError,
        1545012,
        "Temporary Failure",
        "There was a temporary error, please try again.",
    ),
]


@pytest.mark.parametrize("exception,code,description,summary", ERROR_DATA)
def test_handle_payload_error(exception, code, summary, description):
    data = {"error": code, "errorSummary": summary, "errorDescription": description}
    with pytest.raises(exception, match=r"Error #\d+ when sending request"):
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
    with pytest.raises(fbchat.FBchatFacebookError, match="GraphQL error"):
        handle_graphql_errors({"data": {"message_thread": None}, "errors": [error]})


def test_handle_graphql_errors_singular_error_key():
    with pytest.raises(fbchat.FBchatFacebookError, match="GraphQL error #123"):
        handle_graphql_errors({"error": {"code": 123}})


def test_handle_graphql_errors_no_error():
    assert handle_graphql_errors({"data": {"message_thread": None}}) is None


def test_check_http_code():
    with pytest.raises(fbchat.FBchatFacebookError):
        check_http_code(400)
    with pytest.raises(fbchat.FBchatFacebookError):
        check_http_code(500)


def test_check_http_code_404_handling():
    with pytest.raises(fbchat.FBchatFacebookError, match="invalid id"):
        check_http_code(404)


def test_check_http_code_no_error():
    assert check_http_code(200) is None
    assert check_http_code(302) is None


def test_get_jsmods_require_get_image_url():
    data = {
        "__ar": 1,
        "payload": None,
        "jsmods": {
            "require": [
                [
                    "ServerRedirect",
                    "redirectPageTo",
                    [],
                    [
                        "https://scontent-arn2-1.xx.fbcdn.net/v/image.png&dl=1",
                        False,
                        False,
                    ],
                ],
                ["TuringClientSignalCollectionTrigger", ..., [], ...],
                ["TuringClientSignalCollectionTrigger", "retrieveSignals", [], ...],
                ["BanzaiODS"],
                ["BanzaiScuba"],
            ],
            "define": ...,
        },
        "js": ...,
        "css": ...,
        "bootloadable": ...,
        "resource_map": ...,
        "ixData": {},
        "bxData": {},
        "gkxData": ...,
        "qexData": {},
        "lid": "123",
    }
    url = "https://scontent-arn2-1.xx.fbcdn.net/v/image.png&dl=1"
    assert get_jsmods_require(data, 3) == url


def test_require_list():
    assert require_list([]) == set()
    assert require_list([1, 2, 2]) == {1, 2}
    assert require_list(1) == {1}
    assert require_list("abc") == {"abc"}


def test_mimetype_to_key():
    assert mimetype_to_key(None) == "file_id"
    assert mimetype_to_key("image/gif") == "gif_id"
    assert mimetype_to_key("video/mp4") == "video_id"
    assert mimetype_to_key("video/quicktime") == "video_id"
    assert mimetype_to_key("image/png") == "image_id"
    assert mimetype_to_key("image/jpeg") == "image_id"
    assert mimetype_to_key("audio/mpeg") == "audio_id"
    assert mimetype_to_key("application/json") == "file_id"


def test_get_url_parameter():
    assert get_url_parameter("http://example.com?a=b&c=d", "c") == "d"
    assert get_url_parameter("http://example.com?a=b&a=c", "a") == "b"
    with pytest.raises(IndexError):
        get_url_parameter("http://example.com", "a")


def test_prefix_url():
    assert prefix_url("/") == "https://www.facebook.com/"
    assert prefix_url("/abc") == "https://www.facebook.com/abc"
    assert prefix_url("abc") == "abc"
    assert prefix_url("https://m.facebook.com/abc") == "https://m.facebook.com/abc"


DT_0 = datetime.datetime(1970, 1, 1, 0, 0, tzinfo=datetime.timezone.utc)
DT = datetime.datetime(2018, 11, 16, 1, 51, 4, 162000, tzinfo=datetime.timezone.utc)
DT_NO_TIMEZONE = datetime.datetime(2018, 11, 16, 1, 51, 4, 162000)


def test_seconds_to_datetime():
    assert seconds_to_datetime(0) == DT_0
    assert seconds_to_datetime(1542333064.162) == DT
    assert seconds_to_datetime(1542333064.162) != DT_NO_TIMEZONE


def test_millis_to_datetime():
    assert millis_to_datetime(0) == DT_0
    assert millis_to_datetime(1542333064162) == DT
    assert millis_to_datetime(1542333064162) != DT_NO_TIMEZONE


def test_datetime_to_seconds():
    assert datetime_to_seconds(DT_0) == 0
    assert datetime_to_seconds(DT) == 1542333064  # Rounded
    datetime_to_seconds(DT_NO_TIMEZONE)  # Depends on system timezone


def test_datetime_to_millis():
    assert datetime_to_millis(DT_0) == 0
    assert datetime_to_millis(DT) == 1542333064162
    datetime_to_millis(DT_NO_TIMEZONE)  # Depends on system timezone


def test_seconds_to_timedelta():
    assert seconds_to_timedelta(0.001) == datetime.timedelta(microseconds=1000)
    assert seconds_to_timedelta(1) == datetime.timedelta(seconds=1)
    assert seconds_to_timedelta(3600) == datetime.timedelta(hours=1)
    assert seconds_to_timedelta(86400) == datetime.timedelta(days=1)


def test_millis_to_timedelta():
    assert millis_to_timedelta(1) == datetime.timedelta(microseconds=1000)
    assert millis_to_timedelta(1000) == datetime.timedelta(seconds=1)
    assert millis_to_timedelta(3600000) == datetime.timedelta(hours=1)
    assert millis_to_timedelta(86400000) == datetime.timedelta(days=1)


def test_timedelta_to_seconds():
    assert timedelta_to_seconds(datetime.timedelta(microseconds=1000)) == 0  # Rounded
    assert timedelta_to_seconds(datetime.timedelta(seconds=1)) == 1
    assert timedelta_to_seconds(datetime.timedelta(hours=1)) == 3600
    assert timedelta_to_seconds(datetime.timedelta(days=1)) == 86400
