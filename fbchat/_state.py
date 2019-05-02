# -*- coding: UTF-8 -*-
from __future__ import unicode_literals

import attr

from . import _util


@attr.s(slots=True, kw_only=True)
class State(object):
    """Stores and manages state required for most Facebook requests."""

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
