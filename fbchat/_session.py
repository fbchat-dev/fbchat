import attr
import datetime
import requests
import random
import re
import json

# TODO: Only import when required
# Or maybe just replace usage with `html.parser`?
import bs4

from ._common import log, kw_only
from . import _graphql, _util, _exception

from typing import Optional, Mapping, Callable, Any


SERVER_JS_DEFINE_REGEX = re.compile(
    r'require(?:\("ServerJS"\).{,100}\.handle\({.*"define":)|(?:\("ServerJSDefine"\)\)?\.handleDefines\()'
)
SERVER_JS_DEFINE_JSON_DECODER = json.JSONDecoder()


def parse_server_js_define(html: str) -> Mapping[str, Any]:
    """Parse ``ServerJSDefine`` entries from a HTML document."""
    # Find points where we should start parsing
    define_splits = SERVER_JS_DEFINE_REGEX.split(html)

    # TODO: Extract jsmods "require" and "define" from `bigPipe.onPageletArrive`?

    # Skip leading entry
    _, *define_splits = define_splits

    rtn = []
    if not define_splits:
        raise _exception.ParseError("Could not find any ServerJSDefine", data=html)
    if len(define_splits) < 2:
        raise _exception.ParseError("Could not find enough ServerJSDefine", data=html)
    if len(define_splits) > 2:
        raise _exception.ParseError("Found too many ServerJSDefine", data=define_splits)
    # Parse entries (should be two)
    for entry in define_splits:
        try:
            parsed, _ = SERVER_JS_DEFINE_JSON_DECODER.raw_decode(entry, idx=0)
        except json.JSONDecodeError as e:
            raise _exception.ParseError("Invalid ServerJSDefine", data=entry) from e
        if not isinstance(parsed, list):
            raise _exception.ParseError("Invalid ServerJSDefine", data=parsed)
        rtn.extend(parsed)

    # Convert to a dict
    return _util.get_jsmods_define(rtn)


def base36encode(number: int) -> str:
    """Convert from Base10 to Base36."""
    # Taken from https://en.wikipedia.org/wiki/Base36#Python_implementation
    chars = "0123456789abcdefghijklmnopqrstuvwxyz"

    sign = "-" if number < 0 else ""
    number = abs(number)
    result = ""

    while number > 0:
        number, remainder = divmod(number, 36)
        result = chars[remainder] + result

    return sign + result


def prefix_url(url: str) -> str:
    if url.startswith("/"):
        return "https://www.messenger.com" + url
    return url


def generate_message_id(now: datetime.datetime, client_id: str) -> str:
    k = _util.datetime_to_millis(now)
    l = int(random.random() * 4294967295)
    return "<{}:{}-{}@mail.projektitan.com>".format(k, l, client_id)


def get_user_id(session: requests.Session) -> str:
    # TODO: Optimize this `.get_dict()` call!
    cookies = session.cookies.get_dict()
    rtn = cookies.get("c_user")
    if rtn is None:
        raise _exception.ParseError("Could not find user id", data=cookies)
    return str(rtn)


def session_factory() -> requests.Session:
    from . import __version__

    session = requests.session()
    session.headers["Referer"] = "https://www.messenger.com/"
    # We won't try to set a fake user agent to mask our presence!
    # Facebook allows us access anyhow, and it makes our motives clearer:
    # We're not trying to cheat Facebook, we simply want to access their service
    session.headers["User-Agent"] = "fbchat/{}".format(__version__)
    return session


def client_id_factory() -> str:
    return hex(int(random.random() * 2 ** 31))[2:]


def find_form_request(html: str):
    soup = bs4.BeautifulSoup(html, "html.parser", parse_only=bs4.SoupStrainer("form"))

    form = soup.form
    if not form:
        raise _exception.ParseError("Could not find form to submit", data=html)

    url = form.get("action")
    if not url:
        raise _exception.ParseError("Could not find url to submit to", data=form)

    # From what I've seen, it'll always do this!
    if url.startswith("/"):
        url = "https://www.facebook.com" + url

    # It's okay to set missing values to something crap, the values are localized, and
    # hence are not available in the raw HTML
    data = {
        x["name"]: x.get("value", "[missing]")
        for x in form.find_all(["input", "button"])
    }
    return url, data


def two_factor_helper(session: requests.Session, r, on_2fa_callback):
    url, data = find_form_request(r.content.decode("utf-8"))

    # You don't have to type a code if your device is already saved
    # Repeats if you get the code wrong
    while "approvals_code" in data:
        data["approvals_code"] = on_2fa_callback()
        log.info("Submitting 2FA code")
        r = session.post(url, data=data, allow_redirects=False)
        log.debug("2FA location: %s", r.headers.get("Location"))
        url, data = find_form_request(r.content.decode("utf-8"))

    # TODO: Can be missing if checkup flow was done on another device in the meantime?
    if "name_action_selected" in data:
        data["name_action_selected"] = "save_device"
        log.info("Saving browser")
        r = session.post(url, data=data, allow_redirects=False)
        log.debug("2FA location: %s", r.headers.get("Location"))
        url = r.headers.get("Location")
        if url and url.startswith("https://www.messenger.com/login/auth_token/"):
            return url
        url, data = find_form_request(r.content.decode("utf-8"))

    log.info("Starting Facebook checkup flow")
    r = session.post(url, data=data, allow_redirects=False)
    log.debug("2FA location: %s", r.headers.get("Location"))

    url, data = find_form_request(r.content.decode("utf-8"))
    if "verification_method" in data:
        raise _exception.NotLoggedIn(
            "Your account is locked, and you need to log in using a browser, and verify it there!"
        )
    if "submit[This was me]" not in data or "submit[This wasn't me]" not in data:
        raise _exception.ParseError("Could not fill out form properly (2)", data=data)
    data["submit[This was me]"] = "[any value]"
    del data["submit[This wasn't me]"]
    log.info("Verifying login attempt")
    r = session.post(url, data=data, allow_redirects=False)
    log.debug("2FA location: %s", r.headers.get("Location"))

    url, data = find_form_request(r.content.decode("utf-8"))
    if "name_action_selected" not in data:
        raise _exception.ParseError("Could not fill out form properly (3)", data=data)
    data["name_action_selected"] = "save_device"
    log.info("Saving device again")
    r = session.post(url, data=data, allow_redirects=False)
    log.debug("2FA location: %s", r.headers.get("Location"))
    return r.headers.get("Location")


def get_error_data(html: str) -> Optional[str]:
    """Get error message from a request."""
    soup = bs4.BeautifulSoup(
        html, "html.parser", parse_only=bs4.SoupStrainer("form", id="login_form")
    )
    # Attempt to extract and format the error string
    # The error message is in the user's own language!
    return " ".join(list(soup.stripped_strings)[1:3]) or None


def get_fb_dtsg(define) -> Optional[str]:
    if "DTSGInitData" in define:
        return define["DTSGInitData"]["token"]
    elif "DTSGInitialData" in define:
        return define["DTSGInitialData"]["token"]
    return None


@attr.s(slots=True, kw_only=kw_only, repr=False, eq=False)
class Session:
    """Stores and manages state required for most Facebook requests.

    This is the main class, which is used to login to Facebook.
    """

    _user_id = attr.ib(type=str)
    _fb_dtsg = attr.ib(type=str)
    _revision = attr.ib(type=int)
    _session = attr.ib(factory=session_factory, type=requests.Session)
    _counter = attr.ib(0, type=int)
    _client_id = attr.ib(factory=client_id_factory, type=str)

    @property
    def user(self):
        """The logged in user."""
        from . import _threads

        # TODO: Consider caching the result

        return _threads.User(session=self, id=self._user_id)

    def __repr__(self) -> str:
        # An alternative repr, to illustrate that you can't create the class directly
        return "<fbchat.Session user_id={}>".format(self._user_id)

    def _get_params(self):
        self._counter += 1  # TODO: Make this operation atomic / thread-safe
        return {
            "__a": 1,
            "__req": base36encode(self._counter),
            "__rev": self._revision,
            "fb_dtsg": self._fb_dtsg,
        }

    # TODO: Add ability to load previous cookies in here, to avoid 2fa flow
    @classmethod
    def login(
        cls, email: str, password: str, on_2fa_callback: Callable[[], int] = None
    ):
        """Login the user, using ``email`` and ``password``.

        Args:
            email: Facebook ``email``, ``id`` or ``phone number``
            password: Facebook account password
            on_2fa_callback: Function that will be called, in case a two factor
                authentication code is needed. This should return the requested code.

                Tested using SMS and authentication applications. If you have both
                enabled, you might not receive an SMS code, and you'll have to use the
                authentication application.

                Note: Facebook limits the amount of codes they will give you, so if you
                don't receive a code, be patient, and try again later!

        Example:
            >>> import fbchat
            >>> import getpass
            >>> session = fbchat.Session.login(
            ...     input("Email: "),
            ...     getpass.getpass(),
            ...     on_2fa_callback=lambda: input("2FA Code: ")
            ... )
            Email: abc@gmail.com
            Password: ****
            2FA Code: 123456
            >>> session.user.id
            "1234"
        """
        session = session_factory()

        data = {
            # "jazoest": "2754",
            # "lsd": "AVqqqRUa",
            "initial_request_id": "x",  # any, just has to be present
            # "timezone": "-120",
            # "lgndim": "eyJ3IjoxNDQwLCJoIjo5MDAsImF3IjoxNDQwLCJhaCI6ODc3LCJjIjoyNH0=",
            # "lgnrnd": "044039_RGm9",
            "lgnjs": "n",
            "email": email,
            "pass": password,
            "login": "1",
            "persistent": "1",  # Changes the cookie type to have a long "expires"
            "default_persistent": "0",
        }

        try:
            # Should hit a redirect to https://www.messenger.com/
            # If this does happen, the session is logged in!
            r = session.post(
                "https://www.messenger.com/login/password/",
                data=data,
                allow_redirects=False,
            )
        except requests.RequestException as e:
            _exception.handle_requests_error(e)
        _exception.handle_http_error(r.status_code)

        url = r.headers.get("Location")

        # We weren't redirected, hence the email or password was wrong
        if not url:
            error = get_error_data(r.content.decode("utf-8"))
            raise _exception.NotLoggedIn(error)

        if "checkpoint" in url:
            if not on_2fa_callback:
                raise _exception.NotLoggedIn(
                    "2FA code required! Please supply `on_2fa_callback` to .login"
                )
            # Get a facebook.com/checkpoint/start url that handles the 2FA flow
            # This probably works differently for Messenger-only accounts
            url = _util.get_url_parameter(url, "next")
            if not url.startswith("https://www.facebook.com/checkpoint/start/"):
                raise _exception.ParseError("Failed 2fa flow (1)", data=url)

            r = session.get(url, allow_redirects=False)
            url = r.headers.get("Location")
            if not url or not url.startswith("https://www.facebook.com/checkpoint/"):
                raise _exception.ParseError("Failed 2fa flow (2)", data=url)

            r = session.get(url, allow_redirects=False)
            url = two_factor_helper(session, r, on_2fa_callback)

            if not url.startswith("https://www.messenger.com/login/auth_token/"):
                raise _exception.ParseError("Failed 2fa flow (3)", data=url)

            r = session.get(url, allow_redirects=False)
            url = r.headers.get("Location")

        if url != "https://www.messenger.com/":
            error = get_error_data(r.content.decode("utf-8"))
            raise _exception.NotLoggedIn("Failed logging in: {}, {}".format(url, error))

        try:
            return cls._from_session(session=session)
        except _exception.NotLoggedIn as e:
            raise _exception.ParseError("Failed loading session", data=r) from e

    def is_logged_in(self) -> bool:
        """Send a request to Facebook to check the login status.

        Returns:
            Whether the user is still logged in

        Example:
            >>> assert session.is_logged_in()
        """
        # Send a request to the login url, to see if we're directed to the home page
        try:
            r = self._session.get(prefix_url("/login/"), allow_redirects=False)
        except requests.RequestException as e:
            _exception.handle_requests_error(e)
        _exception.handle_http_error(r.status_code)
        return "https://www.messenger.com/" == r.headers.get("Location")

    def logout(self) -> None:
        """Safely log out the user.

        The session object must not be used after this action has been performed!

        Example:
            >>> session.logout()
        """
        data = {"fb_dtsg": self._fb_dtsg}
        try:
            r = self._session.post(
                prefix_url("/logout/"), data=data, allow_redirects=False
            )
        except requests.RequestException as e:
            _exception.handle_requests_error(e)
        _exception.handle_http_error(r.status_code)

        if "Location" not in r.headers:
            raise _exception.FacebookError("Failed logging out, was not redirected!")
        if "https://www.messenger.com/login/" != r.headers["Location"]:
            raise _exception.FacebookError(
                "Failed logging out, got bad redirect: {}".format(r.headers["Location"])
            )

    @classmethod
    def _from_session(cls, session):
        # TODO: Automatically set user_id when the cookie changes in the session
        user_id = get_user_id(session)

        # Make a request to the main page to retrieve ServerJSDefine entries
        try:
            r = session.get(prefix_url("/"), allow_redirects=False)
        except requests.RequestException as e:
            _exception.handle_requests_error(e)
        _exception.handle_http_error(r.status_code)

        define = parse_server_js_define(r.content.decode("utf-8"))

        fb_dtsg = get_fb_dtsg(define)
        if fb_dtsg is None:
            raise _exception.ParseError("Could not find fb_dtsg", data=define)
        if not fb_dtsg:
            # Happens when the client is not actually logged in
            raise _exception.NotLoggedIn(
                "Found empty fb_dtsg, the session was probably invalid."
            )

        try:
            revision = int(define["SiteData"]["client_revision"])
        except TypeError:
            raise _exception.ParseError("Could not find client revision", data=define)

        return cls(user_id=user_id, fb_dtsg=fb_dtsg, revision=revision, session=session)

    def get_cookies(self) -> Mapping[str, str]:
        """Retrieve session cookies, that can later be used in `from_cookies`.

        Returns:
            A dictionary containing session cookies

        Example:
            >>> cookies = session.get_cookies()
        """
        return self._session.cookies.get_dict()

    @classmethod
    def from_cookies(cls, cookies: Mapping[str, str]):
        """Load a session from session cookies.

        Args:
            cookies: A dictionary containing session cookies

        Example:
            >>> cookies = session.get_cookies()
            >>> # Store cookies somewhere, and then subsequently
            >>> session = fbchat.Session.from_cookies(cookies)
        """
        session = session_factory()
        session.cookies = requests.cookies.merge_cookies(session.cookies, cookies)
        return cls._from_session(session=session)

    def _post(self, url, data, files=None, as_graphql=False):
        data.update(self._get_params())
        try:
            r = self._session.post(prefix_url(url), data=data, files=files)
        except requests.RequestException as e:
            _exception.handle_requests_error(e)
        # Facebook's encoding is always UTF-8
        r.encoding = "utf-8"
        _exception.handle_http_error(r.status_code)
        if r.text is None or len(r.text) == 0:
            raise _exception.HTTPError("Error when sending request: Got empty response")
        if as_graphql:
            return _graphql.response_to_json(r.text)
        else:
            text = _util.strip_json_cruft(r.text)
            j = _util.parse_json(text)
            log.debug(j)
            return j

    def _payload_post(self, url, data, files=None):
        j = self._post(url, data, files=files)
        _exception.handle_payload_error(j)

        # update fb_dtsg token if received in response
        if "jsmods" in j:
            define = _util.get_jsmods_define(j["jsmods"]["define"])
            fb_dtsg = get_fb_dtsg(define)
            if fb_dtsg:
                self._fb_dtsg = fb_dtsg

        try:
            return j["payload"]
        except (KeyError, TypeError) as e:
            raise _exception.ParseError("Missing payload", data=j) from e

    def _graphql_requests(self, *queries):
        # TODO: Explain usage of GraphQL, probably in the docs
        # Perhaps provide this API as public?
        data = {
            "method": "GET",
            "response_format": "json",
            "queries": _graphql.queries_to_json(*queries),
        }
        return self._post("/api/graphqlbatch/", data, as_graphql=True)

    def _do_send_request(self, data):
        now = datetime.datetime.utcnow()
        offline_threading_id = _util.generate_offline_threading_id()
        data["client"] = "mercury"
        data["author"] = "fbid:{}".format(self._user_id)
        data["timestamp"] = _util.datetime_to_millis(now)
        data["source"] = "source:chat:web"
        data["offline_threading_id"] = offline_threading_id
        data["message_id"] = offline_threading_id
        data["threading_id"] = generate_message_id(now, self._client_id)
        data["ephemeral_ttl_mode:"] = "0"
        j = self._post("/messaging/send/", data)

        _exception.handle_payload_error(j)

        try:
            message_ids = [
                (action["message_id"], action["thread_fbid"])
                for action in j["payload"]["actions"]
                if "message_id" in action
            ]
            if len(message_ids) != 1:
                log.warning("Got multiple message ids' back: {}".format(message_ids))
            return message_ids[0]
        except (KeyError, IndexError, TypeError) as e:
            raise _exception.ParseError("No message IDs could be found", data=j) from e
