# -*- coding: UTF-8 -*-

from __future__ import unicode_literals

import logging
import attr
import re

from requests import Session, Response
from random import choice
from bs4 import BeautifulSoup as bs
from six.moves.urllib_parse import urlparse, parse_qs
from six.moves import input

from .models import User, FacebookError

log = logging.getLogger(__name__)


BASE_URL = "https://www.facebook.com"
MOBILE_URL = "https://m.facebook.com"
LOGIN_URL = "https://m.facebook.com/login.php?login_attempt=1"


class FacebookResponse(Response):
    def json(self, **kwargs):
        try:
            self._content = self._content[self._content.index(b"{") :]
        except ValueError:
            raise ValueError("No JSON object found: {!r}".format(self.text))
        return super(FacebookResponse, self).json(**kwargs)


def class_rewrite_hook(r, *args, **kwargs):
    r.__class__ = FacebookResponse
    return r


class FacebookSession(Session):
    """TODO: Document this"""

    USER_AGENTS = [
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.90 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_3) AppleWebKit/601.1.10 (KHTML, like Gecko) Version/8.0.5 Safari/601.1.10",
        "Mozilla/5.0 (Windows NT 6.3; WOW64; ; NCT50_AAP285C84A1328) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.90 Safari/537.36",
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/22.0.1207.1 Safari/537.1",
        "Mozilla/5.0 (X11; CrOS i686 2268.111.0) AppleWebKit/536.11 (KHTML, like Gecko) Chrome/20.0.1132.57 Safari/536.11",
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.6 (KHTML, like Gecko) Chrome/20.0.1092.0 Safari/536.6",
    ]

    def __init__(self, user_agent):
        super(FacebookSession, self).__init__()

        self.hooks["response"].append(class_rewrite_hook)

        if not user_agent:
            user_agent = choice(self.USER_AGENTS)

        self.header = {
            # 'Content-Type' : 'application/x-www-form-urlencoded',
            "Referer": BASE_URL,
            "Origin": BASE_URL,
            "User-Agent": user_agent,
        }

    @property
    def fb_dtsg(self):
        return self.params["fb_dtsg"]

    @fb_dtsg.setter
    def fb_dtsg(self, value):
        self.params["fb_dtsg"] = value

    def request(self, method, url, include_payload=True, **kwargs):
        # '__req': str_base(self.req_counter, 36),
        if url.startswith("/"):
            url = BASE_URL + url
        return super(FacebookSession, self).request(method, url, **kwargs)

    """
    def _set_fb_dtsg(self, value):
        self.fb_dtsg = value
        self.params["ttstamp"] = "".join(ord(x) for x in value) + "2"
    """

    def set_fb_dtsg_html(self, html):
        soup = bs(html, "html.parser")

        elem = soup.find("input", {"name": "fb_dtsg"})
        if elem:
            self.fb_dtsg = elem.get("value")
        else:
            self.fb_dtsg = re.search(r'name="fb_dtsg" value="(.*?)"', html).group(1)

    def set_default_params(self):
        r = self.get(BASE_URL)

        self.params = {
            "__rev": re.search(r'"client_revision":(.*?),', r.text).group(1),
            "__user": self.cookies.get("c_user"),
            "__a": "1",
        }

        # self.req_counter = 1

        self.set_fb_dtsg_html(r.text)

    def get_cookies(self):
        return self.cookies.to_dict()

    @classmethod
    def from_cookies(cls, cookies):
        rtn = cls()
        rtn.cookies.update(cookies)
        return rtn

    '''
    def fix_facebook_error(self, error):
        """
        This fixes "Please try closing and re-opening your browser window" errors (1357004).
        This error usually happens after 1-2 days of inactivity
        """
        if error.fb_error_code == 1357004:
            log.warning("Got error #1357004. Resetting values, and resending request")
            log.debug(self.params)
            self.set_default_params()
            log.debug(self.params)
    '''


@attr.s(slots=True)
class BaseClient(object):
    """Base Facebook client"""

    #: The client's `requests` session
    session = attr.ib(type=FacebookSession)
    #: The client's corresponding `User` object
    user = attr.ib(init=False, type=User)

    def __attrs_post_init__(self):
        self.user = User(self.session.cookies.get("c_user"))

    def __repr__(self):
        return "{}(user.id={})".format(type(self).__name__, self.user.id)

    @classmethod
    def login(cls, email, password, user_agent=None):
        """Initialize and login the Facebook client

        Args:
            email: Facebook `email`, `id` or `phone number`
            password: Facebook account password
            user_agent: Custom user agent to use when sending requests.
                If ``None``, the user agent will be chosen randomly
        """

        session = FacebookSession(user_agent)

        soup = bs(session.get(MOBILE_URL).text, "html.parser")
        data = {
            elem["name"]: elem["value"]
            for elem in soup.find_all("input")
            if elem.has_attr("value") and elem.has_attr("name")
        }
        data["email"] = email
        data["pass"] = password
        data["login"] = "Log In"

        r = session.post(LOGIN_URL, data=data)

        """
        # Sometimes Facebook tries to show the user a "Save Device" dialog
        if 'save-device' in r.url:
            r = self.get("https://m.facebook.com/login/save-device/cancel/")
        """

        if "c_user" not in session.cookies:
            raise ValueError("Could not login, failed on: {}".format(r.url))

        session.set_default_params()

        return cls(session)

    @classmethod
    def from_session(cls, session_data):
        session = FacebookSession(session_data["user_agent"])

        session.cookies.update(session_data["cookies"])
        session.set_default_params()

        return cls(session)

    def get_session(self):
        """Retrieve session

        The session can then be serialised, stored, and reused the next time
        the client wants to log in

        Return:
            A dict containing the session
        """

        return {
            "cookies": self.session.cookies.get_dict(),
            "user_agent": self.session.header["User-Agent"],
        }

    def on_2fa(self):
        """Will be called when a two-factor authentication code is needed

        By default, this will call ``input``, and wait for the authentication
        code

        Return:
            The expected return is a two-factor authentication code, or
            ``None`` if unavailable
        """

        return input("Please supply a two-factor authentication code: ")

    def logout(self):
        """Properly log out the client, invalidating the session

        Warning:
            Using the client after this method is called results in undefined
            behaviour
        """

        r = self.session.post("/bluebar/modern_settings_menu/", data={"pmid": "4"})
        logout_h = re.search(r'name=\\"h\\" value=\\"(.*?)\\"', r.text).group(1)

        self.session.get("/logout.php", params={"ref": "mb", "h": logout_h})

    def is_logged_in(self):
        """Check the login status

        Return:
            Whether the client is still logged in
        """

        r = self.session.get(LOGIN_URL, allow_redirects=False)
        return "Location" in r.headers and "home" in r.headers["Location"]
