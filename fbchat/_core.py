# -*- coding: UTF-8 -*-
from __future__ import unicode_literals

import logging
import aenum

log = logging.getLogger("client")


class Enum(aenum.Enum):
    """Used internally by ``fbchat`` to support enumerations"""

    def __repr__(self):
        # For documentation:
        return "{}.{}".format(type(self).__name__, self.name)

    @classmethod
    def _extend_if_invalid(cls, value):
        try:
            return cls(value)
        except ValueError:
            log.warning(
                "Failed parsing {.__name__}({!r}). Extending enum.".format(cls, value)
            )
            aenum.extend_enum(cls, "UNKNOWN_{}".format(value).upper(), value)
            return cls(value)
