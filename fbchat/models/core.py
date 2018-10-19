# -*- coding: UTF-8 -*-

import attr

from typing import Dict, Any, TypeVar


__all__ = ("ID", "Dimension", "FacebookError")


JSON = Dict[str, Any]


class ID(int):
    pass


@attr.s(slots=True, frozen=True)
class Dimension:
    """Represents the width and height of an object"""

    #: Width of the object
    width = attr.ib(type=int, converter=int)
    #: Height of the object
    height = attr.ib(type=int, converter=int)

    @classmethod
    def from_dict(cls, items: JSON):
        return cls(items["width"], items["height"])


@attr.s(slots=True, str=True)
class FacebookError(Exception):
    """Thrown when Facebook returns an error"""

    #: The error code that Facebook returned
    fb_error_code = attr.ib(type=int, converter=int)
    #: A localized error message that Facebook returned
    fb_error_message = attr.ib(type=str)
