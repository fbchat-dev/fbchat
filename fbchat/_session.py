import attr
import bs4
import re
import requests
import random
import urllib.parse

from ._core import log, kw_only
from . import _graphql, _util, _exception

FB_DTSG_REGEX = re.compile(r'name="fb_dtsg" value="(.*?)"')


def get_user_id(session):
    # TODO: Optimize this `.get_dict()` call!
    cookies = session.cookies.get_dict()
    rtn = cookies.get("c_user")
    if rtn is None:
        raise _exception.ParseError("Could not find user id", data=cookies)
    return str(rtn)


def find_input_fields(html):
    return bs4.BeautifulSoup(html, "html.parser", parse_only=bs4.SoupStrainer("input"))


def session_factory():
    session = requests.session()
    session.headers["Referer"] = "https://www.facebook.com"
    # TODO: Deprecate setting the user agent manually
    session.headers["User-Agent"] = random.choice(_util.USER_AGENTS)
    return session


def client_id_factory():
    return hex(int(random.random() * 2 ** 31))[2:]


def is_home(url):
    parts = urllib.parse.urlparse(url)
    # Check the urls `/home.php` and `/`
    return "home" in parts.path or "/" == parts.path


def _2fa_helper(session, code, r):
    soup = find_input_fields(r.text)
    data = dict()

    url = "https://m.facebook.com/login/checkpoint/"

    data["approvals_code"] = code
    data["fb_dtsg"] = soup.find("input", {"name": "fb_dtsg"})["value"]
    data["nh"] = soup.find("input", {"name": "nh"})["value"]
    data["submit[Submit Code]"] = "Submit Code"
    data["codes_submitted"] = 0
    log.info("Submitting 2FA code.")

    r = session.post(url, data=data)

    if is_home(r.url):
        return r

    del data["approvals_code"]
    del data["submit[Submit Code]"]
    del data["codes_submitted"]

    data["name_action_selected"] = "save_device"
    data["submit[Continue]"] = "Continue"
    log.info("Saving browser.")
    # At this stage, we have dtsg, nh, name_action_selected, submit[Continue]
    r = session.post(url, data=data)

    if is_home(r.url):
        return r

    del data["name_action_selected"]
    log.info("Starting Facebook checkup flow.")
    # At this stage, we have dtsg, nh, submit[Continue]
    r = session.post(url, data=data)

    if is_home(r.url):
        return r

    del data["submit[Continue]"]
    data["submit[This was me]"] = "This Was Me"
    log.info("Verifying login attempt.")
    # At this stage, we have dtsg, nh, submit[This was me]
    r = session.post(url, data=data)

    if is_home(r.url):
        return r

    del data["submit[This was me]"]
    data["submit[Continue]"] = "Continue"
    data["name_action_selected"] = "save_device"
    log.info("Saving device again.")
    # At this stage, we have dtsg, nh, submit[Continue], name_action_selected
    r = session.post(url, data=data)
    return r


def get_error_data(html, url):
    """Get error code and message from a request."""
    try:
        code = _util.get_url_parameter(url, "e")
    except IndexError:
        code = None

    soup = bs4.BeautifulSoup(
        html, "html.parser", parse_only=bs4.SoupStrainer("div", id="login_error"),
    )
    return code, soup.get_text() or None


@attr.s(slots=True, kw_only=kw_only, repr=False)
class Session:
    """Stores and manages state required for most Facebook requests.

    This is the main class, which is used to login to Facebook.
    """

    _user_id = attr.ib()
    _fb_dtsg = attr.ib()
    _revision = attr.ib()
    _session = attr.ib(factory=session_factory)
    _counter = attr.ib(0)
    _client_id = attr.ib(factory=client_id_factory)
    _logout_h = attr.ib(None)

    @property
    def user_id(self):
        """The logged in user's ID."""
        return self._user_id

    def __repr__(self):
        # An alternative repr, to illustrate that you can't create the class directly
        return "<fbchat.Session user_id={}>".format(self._user_id)

    def _get_params(self):
        self._counter += 1  # TODO: Make this operation atomic / thread-safe
        return {
            "__a": 1,
            "__req": _util.str_base(self._counter, 36),
            "__rev": self._revision,
            "fb_dtsg": self._fb_dtsg,
        }

    @classmethod
    def login(cls, email, password, on_2fa_callback=None):
        """Login the user, using ``email`` and ``password``.

        Args:
            email: Facebook ``email`` or ``id`` or ``phone number``
            password: Facebook account password
            on_2fa_callback: Function that will be called, in case a 2FA code is needed.
                This should return the requested 2FA code.
        """
        session = session_factory()

        try:
            r = session.get("https://m.facebook.com/")
        except requests.RequestException as e:
            _exception.handle_requests_error(e)
        soup = find_input_fields(r.text)

        data = dict(
            (elem["name"], elem["value"])
            for elem in soup
            if elem.has_attr("value") and elem.has_attr("name")
        )
        data["email"] = email
        data["pass"] = password
        data["login"] = "Log In"

        try:
            url = "https://m.facebook.com/login.php?login_attempt=1"
            r = session.post(url, data=data)
        except requests.RequestException as e:
            _exception.handle_requests_error(e)

        # Usually, 'Checkpoint' will refer to 2FA
        if "checkpoint" in r.url and ('id="approvals_code"' in r.text.lower()):
            if not on_2fa_callback:
                raise ValueError(
                    "2FA code required, please add `on_2fa_callback` to .login"
                )
            code = on_2fa_callback()
            try:
                r = _2fa_helper(session, code, r)
            except requests.RequestException as e:
                _exception.handle_requests_error(e)

        # Sometimes Facebook tries to show the user a "Save Device" dialog
        if "save-device" in r.url:
            try:
                r = session.get("https://m.facebook.com/login/save-device/cancel/")
            except requests.RequestException as e:
                _exception.handle_requests_error(e)

        if is_home(r.url):
            return cls._from_session(session=session)
        else:
            code, msg = get_error_data(r.text, r.url)
            raise _exception.ExternalError(
                "Login failed at url {!r}".format(r.url), msg, code=code
            )

    def is_logged_in(self):
        """Send a request to Facebook to check the login status.

        Returns:
            bool: Whether the user is still logged in
        """
        # Send a request to the login url, to see if we're directed to the home page
        url = "https://m.facebook.com/login.php?login_attempt=1"
        try:
            r = self._session.get(url, allow_redirects=False)
        except requests.RequestException as e:
            _exception.handle_requests_error(e)
        return "Location" in r.headers and is_home(r.headers["Location"])

    def logout(self):
        """Safely log out the user.

        The session object must not be used after this action has been performed!
        """
        logout_h = self._logout_h
        if not logout_h:
            url = _util.prefix_url("/bluebar/modern_settings_menu/")
            try:
                h_r = self._session.post(url, data={"pmid": "4"})
            except requests.RequestException as e:
                _exception.handle_requests_error(e)
            logout_h = re.search(r'name=\\"h\\" value=\\"(.*?)\\"', h_r.text).group(1)

        url = _util.prefix_url("/logout.php")
        try:
            r = self._session.get(url, params={"ref": "mb", "h": logout_h})
        except requests.RequestException as e:
            _exception.handle_requests_error(e)
        _exception.handle_http_error(r.status_code)

    @classmethod
    def _from_session(cls, session):
        # TODO: Automatically set user_id when the cookie changes in the session
        user_id = get_user_id(session)

        try:
            r = session.get(_util.prefix_url("/"))
        except requests.RequestException as e:
            _exception.handle_requests_error(e)

        soup = find_input_fields(r.text)

        fb_dtsg_element = soup.find("input", {"name": "fb_dtsg"})
        if fb_dtsg_element:
            fb_dtsg = fb_dtsg_element["value"]
        else:
            # Fall back to searching with a regex
            res = FB_DTSG_REGEX.search(r.text)
            if not res:
                raise ValueError("Failed loading session, could not find fb_dtsg")
            fb_dtsg = res.group(1)

        revision = int(r.text.split('"client_revision":', 1)[1].split(",", 1)[0])

        logout_h_element = soup.find("input", {"name": "h"})
        logout_h = logout_h_element["value"] if logout_h_element else None

        return cls(
            user_id=user_id,
            fb_dtsg=fb_dtsg,
            revision=revision,
            session=session,
            logout_h=logout_h,
        )

    def get_cookies(self):
        """Retrieve session cookies, that can later be used in `from_cookies`.

        Returns:
            dict: A dictionary containing session cookies
        """
        return self._session.cookies.get_dict()

    @classmethod
    def from_cookies(cls, cookies):
        """Load a session from session cookies.

        Args:
            cookies (dict): A dictionary containing session cookies
        """
        session = session_factory()
        session.cookies = requests.cookies.merge_cookies(session.cookies, cookies)
        return cls._from_session(session=session)

    def _get(self, url, params, error_retries=3):
        params.update(self._get_params())
        try:
            r = self._session.get(_util.prefix_url(url), params=params)
        except requests.RequestException as e:
            _exception.handle_requests_error(e)
        content = _util.check_request(r)
        return _util.to_json(content)

    def _post(self, url, data, files=None, as_graphql=False):
        data.update(self._get_params())
        try:
            r = self._session.post(_util.prefix_url(url), data=data, files=files)
        except requests.RequestException as e:
            _exception.handle_requests_error(e)
        content = _util.check_request(r)
        if as_graphql:
            return _graphql.response_to_json(content)
        else:
            return _util.to_json(content)

    def _payload_post(self, url, data, files=None):
        j = self._post(url, data, files=files)
        _exception.handle_payload_error(j)
        try:
            return j["payload"]
        except (KeyError, TypeError) as e:
            raise _exception.ParseError("Missing payload", data=j) from e

    def _graphql_requests(self, *queries):
        data = {
            "method": "GET",
            "response_format": "json",
            "queries": _graphql.queries_to_json(*queries),
        }
        return self._post("/api/graphqlbatch/", data, as_graphql=True)

    def _upload(self, files, voice_clip=False):
        """Upload files to Facebook.

        `files` should be a list of files that requests can upload, see
        `requests.request <https://docs.python-requests.org/en/master/api/#requests.request>`_.

        Return a list of tuples with a file's ID and mimetype.
        """
        file_dict = {"upload_{}".format(i): f for i, f in enumerate(files)}

        data = {"voice_clip": voice_clip}

        j = self._payload_post(
            "https://upload.facebook.com/ajax/mercury/upload.php", data, files=file_dict
        )

        if len(j["metadata"]) != len(files):
            raise _exception.ParseError("Some files could not be uploaded", data=j)

        return [
            (data[_util.mimetype_to_key(data["filetype"])], data["filetype"])
            for data in j["metadata"]
        ]

    def _do_send_request(self, data):
        offline_threading_id = _util.generate_offline_threading_id()
        data["client"] = "mercury"
        data["author"] = "fbid:{}".format(self._user_id)
        data["timestamp"] = _util.now()
        data["source"] = "source:chat:web"
        data["offline_threading_id"] = offline_threading_id
        data["message_id"] = offline_threading_id
        data["threading_id"] = _util.generate_message_id(self._client_id)
        data["ephemeral_ttl_mode:"] = "0"
        j = self._post("/messaging/send/", data)

        _exception.handle_payload_error(j)

        # update JS token if received in response
        fb_dtsg = _util.get_jsmods_require(j, 2)
        if fb_dtsg is not None:
            self._fb_dtsg = fb_dtsg

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
