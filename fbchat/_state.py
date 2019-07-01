# -*- coding: UTF-8 -*-
from __future__ import unicode_literals

import attr

from . import _util


@attr.s(slots=True, kw_only=True)
class State(object):
    """Stores and manages state required for most Facebook requests."""

    fb_dtsg = attr.ib(None)
    _revision = attr.ib(None)

    def get_params(self):
        if self.fb_dtsg is None:
            return {}
        return {
            "__a": 1,
            "__rev": self._revision,
            "fb_dtsg": self.fb_dtsg,
        }
