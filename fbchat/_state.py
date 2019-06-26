# -*- coding: UTF-8 -*-
from __future__ import unicode_literals

import attr
import bs4
import re
import requests

from . import _util

FB_DTSG_REGEX = re.compile(r'name="fb_dtsg" value="(.*?)"')


@attr.s(slots=True, kw_only=True)
class State(object):
    """Stores and manages state required for most Facebook requests."""

    _session = attr.ib(factory=requests.session)
    fb_dtsg = attr.ib(None)
    _revision = attr.ib(None)
    _counter = attr.ib(0)
    _logout_h = attr.ib(None)

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
    def from_base_request(cls, session, content):
        soup = bs4.BeautifulSoup(content, "html.parser")

        fb_dtsg_element = soup.find("input", {"name": "fb_dtsg"})
        if fb_dtsg_element:
            fb_dtsg = fb_dtsg_element["value"]
        else:
            # Fall back to searching with a regex
            fb_dtsg = FB_DTSG_REGEX.search(content).group(1)

        revision = int(content.split('"client_revision":', 1)[1].split(",", 1)[0])

        logout_h_element = soup.find("input", {"name": "h"})
        logout_h = logout_h_element["value"] if logout_h_element else None

        return cls(
            session=session, fb_dtsg=fb_dtsg, revision=revision, logout_h=logout_h
        )
