# -*- coding: UTF-8 -*-
from __future__ import unicode_literals

import aenum


class Enum(aenum.Enum):
    """Used internally by fbchat to support enumerations"""

    def __repr__(self):
        # For documentation:
        return "{}.{}".format(type(self).__name__, self.name)
