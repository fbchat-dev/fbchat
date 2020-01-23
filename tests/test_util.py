import pytest
import fbchat
import datetime
from fbchat._util import (
    strip_json_cruft,
    parse_json,
    get_jsmods_require,
    mimetype_to_key,
    get_url_parameter,
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
    with pytest.raises(fbchat.ParseError, match="No JSON object found"):
        strip_json_cruft("No JSON object here!")


def test_parse_json():
    assert parse_json('{"a":"b"}') == {"a": "b"}


def test_parse_json_invalid():
    with pytest.raises(fbchat.ParseError, match="Error while parsing JSON"):
        parse_json("No JSON object here!")


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
    assert get_url_parameter("http://example.com", "a") is None


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
