# -*- coding: UTF-8 -*-
from __future__ import unicode_literals

import attr
import bs4
import re
import requests
import random

from . import _util, _exception

FB_DTSG_REGEX = re.compile(r'name="fb_dtsg" value="(.*?)"')


def session_factory(user_agent=None):
    session = requests.session()
    session.headers["Referer"] = "https://www.facebook.com"
    # TODO: Deprecate setting the user agent manually
    session.headers["User-Agent"] = user_agent or random.choice(_util.USER_AGENTS)
    return session


def _2fa_helper(session, code, r):
    soup = bs4.BeautifulSoup(r.text, "html.parser")
    data = dict()

    url = "https://m.facebook.com/login/checkpoint/"

    data["approvals_code"] = code
    data["fb_dtsg"] = soup.find("input", {"name": "fb_dtsg"})["value"]
    data["nh"] = soup.find("input", {"name": "nh"})["value"]
    data["submit[Submit Code]"] = "Submit Code"
    data["codes_submitted"] = 0
    _util.log.info("Submitting 2FA code.")

    r = session.post(url, data=data)

    if "home" in r.url:
        return r

    del data["approvals_code"]
    del data["submit[Submit Code]"]
    del data["codes_submitted"]

    data["name_action_selected"] = "save_device"
    data["submit[Continue]"] = "Continue"
    _util.log.info("Saving browser.")
    # At this stage, we have dtsg, nh, name_action_selected, submit[Continue]
    r = session.post(url, data=data)

    if "home" in r.url:
        return r

    del data["name_action_selected"]
    _util.log.info("Starting Facebook checkup flow.")
    # At this stage, we have dtsg, nh, submit[Continue]
    r = session.post(url, data=data)

    if "home" in r.url:
        return r

    del data["submit[Continue]"]
    data["submit[This was me]"] = "This Was Me"
    _util.log.info("Verifying login attempt.")
    # At this stage, we have dtsg, nh, submit[This was me]
    r = session.post(url, data=data)

    if "home" in r.url:
        return r

    del data["submit[This was me]"]
    data["submit[Continue]"] = "Continue"
    data["name_action_selected"] = "save_device"
    _util.log.info("Saving device again.")
    # At this stage, we have dtsg, nh, submit[Continue], name_action_selected
    r = session.post(url, data=data)
    return r


@attr.s(slots=True, kw_only=True)
class State(object):
    """Stores and manages state required for most Facebook requests."""

    _session = attr.ib(factory=session_factory)
    fb_dtsg = attr.ib(None)
    _revision = attr.ib(None)
    _counter = attr.ib(0)
    _logout_h = attr.ib(None)

    def get_user_id(self):
        rtn = self.get_cookies().get("c_user")
        if rtn is None:
            return None
        return str(rtn)

    @property
    def logout_h(self):
        return self._logout_h

    def get_params(self):
        if self.fb_dtsg is None:
            return {}
        self._counter += 1  # TODO: Make this operation atomic / thread-safe
        return {
            "__a": 1,
            "__req": _util.str_base(self._counter, 36),
            "__rev": self._revision,
            "fb_dtsg": self.fb_dtsg,
        }

    @classmethod
    def login(cls, email, password, user_agent=None):
        session = session_factory(user_agent=user_agent)

        soup = bs4.BeautifulSoup(
            session.get("https://m.facebook.com/").text, "html.parser"
        )
        data = dict(
            (elem["name"], elem["value"])
            for elem in soup.findAll("input")
            if elem.has_attr("value") and elem.has_attr("name")
        )
        data["email"] = email
        data["pass"] = password
        data["login"] = "Log In"

        r = session.post("https://m.facebook.com/login.php?login_attempt=1", data=data)

        # Usually, 'Checkpoint' will refer to 2FA
        if "checkpoint" in r.url and ('id="approvals_code"' in r.text.lower()):
            code = on_2fa_callback()
            r = _2fa_helper(session, code, r)

        # Sometimes Facebook tries to show the user a "Save Device" dialog
        if "save-device" in r.url:
            r = session.get("https://m.facebook.com/login/save-device/cancel/")

        if "home" in r.url:
            return cls.from_session(session=session)
        else:
            raise _exception.FBchatUserError(
                "Login failed. Check email/password. "
                "(Failed on url: {})".format(r.url)
            )

    @classmethod
    def from_session(cls, session):
        r = session.get(_util.prefix_url("/"))

        soup = bs4.BeautifulSoup(r.text, "html.parser")

        fb_dtsg_element = soup.find("input", {"name": "fb_dtsg"})
        if fb_dtsg_element:
            fb_dtsg = fb_dtsg_element["value"]
        else:
            # Fall back to searching with a regex
            fb_dtsg = FB_DTSG_REGEX.search(r.text).group(1)

        revision = int(r.text.split('"client_revision":', 1)[1].split(",", 1)[0])

        logout_h_element = soup.find("input", {"name": "h"})
        logout_h = logout_h_element["value"] if logout_h_element else None

        return cls(
            session=session, fb_dtsg=fb_dtsg, revision=revision, logout_h=logout_h
        )

    def get_cookies(self):
        return self._session.cookies.get_dict()

    @classmethod
    def from_cookies(cls, cookies, user_agent=None):
        session = session_factory(user_agent=user_agent)
        session.cookies = requests.cookies.merge_cookies(session.cookies, cookies)
        return cls.from_session(session=session)

    @classmethod
    def with_user_agent(cls, user_agent=None, **kwargs):
        return cls(session=session_factory(user_agent=user_agent), **kwargs)
