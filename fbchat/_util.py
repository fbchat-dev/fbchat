import datetime
import json
import time
import random
import contextlib
import mimetypes
import urllib.parse
import requests
from os import path

from ._core import log
from ._exception import (
    FBchatException,
    FBchatFacebookError,
    FBchatInvalidParameters,
    FBchatNotLoggedIn,
    FBchatPleaseRefresh,
)

#: Default list of user agents
USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.90 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_3) AppleWebKit/601.1.10 (KHTML, like Gecko) Version/8.0.5 Safari/601.1.10",
    "Mozilla/5.0 (Windows NT 6.3; WOW64; ; NCT50_AAP285C84A1328) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.90 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/22.0.1207.1 Safari/537.1",
    "Mozilla/5.0 (X11; CrOS i686 2268.111.0) AppleWebKit/536.11 (KHTML, like Gecko) Chrome/20.0.1132.57 Safari/536.11",
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.6 (KHTML, like Gecko) Chrome/20.0.1092.0 Safari/536.6",
]


def now():
    return int(time.time() * 1000)


def strip_json_cruft(text):
    """Removes `for(;;);` (and other cruft) that preceeds JSON responses."""
    try:
        return text[text.index("{") :]
    except ValueError:
        raise FBchatException("No JSON object found: {!r}".format(text))


def get_decoded_r(r):
    return get_decoded(r._content)


def get_decoded(content):
    return content.decode("utf-8")


def parse_json(content):
    try:
        return json.loads(content)
    except ValueError:
        raise FBchatFacebookError("Error while parsing JSON: {!r}".format(content))


def digit_to_char(digit):
    if digit < 10:
        return str(digit)
    return chr(ord("a") + digit - 10)


def str_base(number, base):
    if number < 0:
        return "-" + str_base(-number, base)
    (d, m) = divmod(number, base)
    if d > 0:
        return str_base(d, base) + digit_to_char(m)
    return digit_to_char(m)


def generate_message_id(client_id=None):
    k = now()
    l = int(random.random() * 4294967295)
    return "<{}:{}-{}@mail.projektitan.com>".format(k, l, client_id)


def get_signature_id():
    return hex(int(random.random() * 2147483648))


def generate_offline_threading_id():
    ret = now()
    value = int(random.random() * 4294967295)
    string = ("0000000000000000000000" + format(value, "b"))[-22:]
    msgs = format(ret, "b") + string
    return str(int(msgs, 2))


def handle_payload_error(j):
    if "error" not in j:
        return
    error = j["error"]
    if j["error"] == 1357001:
        error_cls = FBchatNotLoggedIn
    elif j["error"] == 1357004:
        error_cls = FBchatPleaseRefresh
    elif j["error"] in (1357031, 1545010, 1545003):
        error_cls = FBchatInvalidParameters
    else:
        error_cls = FBchatFacebookError
    # TODO: Use j["errorSummary"]
    # "errorDescription" is in the users own language!
    raise error_cls(
        "Error #{} when sending request: {}".format(error, j["errorDescription"]),
        fb_error_code=error,
        fb_error_message=j["errorDescription"],
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
        raise FBchatFacebookError(
            "GraphQL error #{}: {} / {!r}".format(
                error.get("code"), error.get("message"), error.get("debug_info")
            ),
            fb_error_code=error.get("code"),
            fb_error_message=error.get("message"),
        )


def check_request(r):
    check_http_code(r.status_code)
    content = get_decoded_r(r)
    check_content(content)
    return content


def check_http_code(code):
    msg = "Error when sending request: Got {} response.".format(code)
    if code == 404:
        raise FBchatFacebookError(
            msg + " This is either because you specified an invalid URL, or because"
            " you provided an invalid id (Facebook usually requires integer ids).",
            request_status_code=code,
        )
    if 400 <= code < 600:
        raise FBchatFacebookError(msg, request_status_code=code)


def check_content(content, as_json=True):
    if content is None or len(content) == 0:
        raise FBchatFacebookError("Error when sending request: Got empty response")


def to_json(content):
    content = strip_json_cruft(content)
    j = parse_json(content)
    log.debug(j)
    return j


def get_jsmods_require(j, index):
    if j.get("jsmods") and j["jsmods"].get("require"):
        try:
            return j["jsmods"]["require"][0][index][0]
        except (KeyError, IndexError) as e:
            log.warning(
                "Error when getting jsmods_require: "
                "{}. Facebook might have changed protocol".format(j)
            )
    return None


def require_list(list_):
    if isinstance(list_, list):
        return set(list_)
    else:
        return set([list_])


def mimetype_to_key(mimetype):
    if not mimetype:
        return "file_id"
    if mimetype == "image/gif":
        return "gif_id"
    x = mimetype.split("/")
    if x[0] in ["video", "image", "audio"]:
        return "%s_id" % x[0]
    return "file_id"


def get_files_from_urls(file_urls):
    files = []
    for file_url in file_urls:
        r = requests.get(file_url)
        # We could possibly use r.headers.get('Content-Disposition'), see
        # https://stackoverflow.com/a/37060758
        file_name = path.basename(file_url).split("?")[0].split("#")[0]
        files.append(
            (
                file_name,
                r.content,
                r.headers.get("Content-Type") or mimetypes.guess_type(file_name)[0],
            )
        )
    return files


@contextlib.contextmanager
def get_files_from_paths(filenames):
    files = []
    for filename in filenames:
        files.append(
            (
                path.basename(filename),
                open(filename, "rb"),
                mimetypes.guess_type(filename)[0],
            )
        )
    yield files
    for fn, fp, ft in files:
        fp.close()


def get_url_parameters(url, *args):
    params = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
    return [params[arg][0] for arg in args if params.get(arg)]


def get_url_parameter(url, param):
    return get_url_parameters(url, param)[0]


def prefix_url(url):
    if url.startswith("/"):
        return "https://www.facebook.com" + url
    return url


def seconds_to_datetime(timestamp_in_seconds):
    """Convert an UTC timestamp to a timezone-aware datetime object."""
    # `.utcfromtimestamp` will return a "naive" datetime object, which is why we use the
    # following:
    return datetime.datetime.fromtimestamp(
        timestamp_in_seconds, tz=datetime.timezone.utc
    )


def millis_to_datetime(timestamp_in_milliseconds):
    """Convert an UTC timestamp, in milliseconds, to a timezone-aware datetime."""
    return seconds_to_datetime(timestamp_in_milliseconds / 1000)


def datetime_to_seconds(dt):
    """Convert a datetime to an UTC timestamp.

    Naive datetime objects are presumed to represent time in the system timezone.

    The returned seconds will be rounded to the nearest whole number.
    """
    # We could've implemented some fancy "convert naive timezones to UTC" logic, but
    # it's not really worth the effort.
    return round(dt.timestamp())


def datetime_to_millis(dt):
    """Convert a datetime to an UTC timestamp, in milliseconds.

    Naive datetime objects are presumed to represent time in the system timezone.

    The returned milliseconds will be rounded to the nearest whole number.
    """
    return round(dt.timestamp() * 1000)


def seconds_to_timedelta(seconds):
    """Convert seconds to a timedelta."""
    return datetime.timedelta(seconds=seconds)


def millis_to_timedelta(milliseconds):
    """Convert a duration (in milliseconds) to a timedelta object."""
    return datetime.timedelta(milliseconds=milliseconds)


def timedelta_to_seconds(td):
    """Convert a timedelta to seconds.

    The returned seconds will be rounded to the nearest whole number.
    """
    return round(td.total_seconds())
