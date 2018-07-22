# -*- coding: UTF-8 -*-

from __future__ import unicode_literals

import logging

from requests import Session
from requests.cookies import cookiejar_from_dict
from random import choice, randint
from bs4 import BeautifulSoup as bs
from six.moves.urllib_parse import urlparse, parse_qs
from six.moves import input

from .models import User, FacebookError

log = logging.getLogger(__name__)


BASE_URL = "https://www.facebook.com"
MOBILE_URL = "https://www.facebook.com"
LOGIN_URL = "https://m.facebook.com/login.php?login_attempt=1"

#: Default list of user agents
USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.90 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_3) AppleWebKit/601.1.10 (KHTML, like Gecko) Version/8.0.5 Safari/601.1.10",
    "Mozilla/5.0 (Windows NT 6.3; WOW64; ; NCT50_AAP285C84A1328) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.90 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/22.0.1207.1 Safari/537.1",
    "Mozilla/5.0 (X11; CrOS i686 2268.111.0) AppleWebKit/536.11 (KHTML, like Gecko) Chrome/20.0.1132.57 Safari/536.11",
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.6 (KHTML, like Gecko) Chrome/20.0.1092.0 Safari/536.6"
]


class FacebookSession(Session):
    """"""

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


    def request(self, method, url, include_payload=True, **kwargs):
        return super(self, FacebookSession).request(method, url, **kwargs)


    def set_fb_dtsg(self, value):
        self.params['fb_dtsg'] = value
        self.params['ttstamp'] = ''.join(ord(x) for x in value) + '2'


    def set_fb_dtsg_html(self, r):
        soup = bs(r, 'html.parser')

        elem = soup.find('input', {'name': 'fb_dtsg'})
        if elem:
            self.params['fb_dtsg'] = elem.get('value')
        else:
            self.params['fb_dtsg'] = re.search(r'name="fb_dtsg" value="(.*?)"', r.text).group(1)


    def set_default_params(self):
        r = self.get(BASE_URL)

        self.params = {
            '__rev': re.search(r'"client_revision":(.*?),', r.text).group(1),
            '__user': self.cookies.get('c_user'),
            '__a': '1',
        }

        self.set_fb_dtsg_html(r)


class Base(User):
    """Base Facebook client"""

    def __init__(self, email, password, session=None, user_agent=None, max_tries=3):
        """Initialize and login the Facebook client

        Args:
            email: Facebook `email`, `id` or `phone number`
            password: Facebook account password
            session (dict): Previous session to attempt to load
            user_agent: Custom user agent to use when sending requests.
                If ``None``, the user agent will be chosen randomly
            max_tries (int): Maximum number of times to try logging in
        """

        #self.req_counter = 1
        #self.seq = "0"
        #self.client_id = hex(randint(2**31))[2:]

        if session:
            try:
                self.set_session(session)
                return
            except (ValueError, FacebookError):
                log.warning("Failed loading session", exc_info=True)

        if max_tries < 1:
            raise ValueError("`max_tries` should be at least one")

        if not email or not password:
            raise ValueError("`email` and `password` not set")

        if not user_agent:
            user_agent = choice(USER_AGENTS)

        self.s = FacebookSession()

        self.s.header = {
            # 'Content-Type' : 'application/x-www-form-urlencoded',
            'Referer' : BASE_URL,
            'Origin' : BASE_URL,
            'User-Agent' : user_agent,
        }

        self._do_login(email, password, max_tries)
        self._setup()


    def on_2fa(self):
        """Will be called when a two-factor authentication code is needed

        By default, this will call ``input``, and wait for the authentication
        code

        Return:
            The expected return is a two-factor authentication code, or
            ``None`` if unavailable
        """
        return input("Please supply a two-factor authentication code: ")


    def _login(self, email, password):
        soup = bs(self.s.get(MOBILE_URL).text, 'html.parser')
        data = {
            elem['name']: elem['value'] for elem in soup.findAll('input')
            if elem.has_attr('value') and elem.has_attr('name')
        }
        data['email'] = email
        data['pass'] = password
        data['login'] = 'Log In'

        r = self.s.post(LOGIN_URL, data=data)

        '''
        # Sometimes Facebook tries to show the user a "Save Device" dialog
        if 'save-device' in r.url:
            r = self.get("https://m.facebook.com/login/save-device/cancel/")
        '''

        if 'c_user' not in self.s.cookies:
            raise FacebookError("Could not login, failed on url: %s" % r.url)

    def _do_login(self, email, password, max_tries):
        for i in range(1, max_tries + 1):
            try:
                return self._login(email, password)
            except FacebookError as e:
                if i < max_tries:
                    log.warning("Attempt #%d failed, retrying", i, exc_info=True)
                else:
                    raise e

    def _setup(self):
        self.id = int(self.s.cookies.get('c_user'))
        self.s.set_default_params()


    def logout(self):
        """Properly log out the client, invalidating the session

        Warning:
            Using the client after this method is called results in undefined
            behaviour
        """

        if not hasattr(self, 'logout_h'):
            r = self.s.post("https://www.facebook.com/bluebar/modern_settings_menu/", data={'pmid': '4'})
            self.logout_h = re.search(r'name=\\"h\\" value=\\"(.*?)\\"', r.text).group(1)

        self.s.get("https://www.facebook.com/logout.php", params={
            'ref': 'mb',
            'h': self.logout_h
        })


    def is_logged_in(self):
        """Check the login status

        Return:
            Whether the client is still logged in
        """

        r = self.s.get(LOGIN_URL, allow_redirects=False)
        return 'Location' in r.headers and 'home' in r.headers['Location']


    def get_session(self):
        """Retrieve session

        The session can then be serialised, stored, and reused the next time
        the client wants to log in

        Return:
            A dict containing the session
        """
        return self.s.cookies.to_dict()

    def set_session(self, session):
        """Validate session and load it into the client

        Args:
            session (dict): A dictionay containing the session
        """

        if not session or 'c_user' not in session:
            raise ValueError('Invalid session: %s' % session)

        self.s.cookies = cookiejar_from_dict(session, self.s.cookies)
        self._setup()
