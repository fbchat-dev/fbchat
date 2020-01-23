import sys
import attr
import logging

log = logging.getLogger("fbchat")

# Enable kw_only if the python version supports it
kw_only = sys.version_info[:2] > (3, 5)

#: Default attrs settings for classes
attrs_default = attr.s(frozen=True, slots=True, kw_only=kw_only)
