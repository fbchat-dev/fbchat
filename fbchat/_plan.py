# -*- coding: UTF-8 -*-
from __future__ import unicode_literals

import attr


@attr.s(cmp=False)
class Plan(object):
    """Represents a plan"""

    #: ID of the plan
    uid = attr.ib(None, init=False)
    #: Plan time (unix time stamp), only precise down to the minute
    time = attr.ib(converter=int)
    #: Plan title
    title = attr.ib()
    #: Plan location name
    location = attr.ib(None, converter=lambda x: x or "")
    #: Plan location ID
    location_id = attr.ib(None, converter=lambda x: x or "")
    #: ID of the plan creator
    author_id = attr.ib(None, init=False)
    #: List of the people IDs who will take part in the plan
    going = attr.ib(factory=list, init=False)
    #: List of the people IDs who won't take part in the plan
    declined = attr.ib(factory=list, init=False)
    #: List of the people IDs who are invited to the plan
    invited = attr.ib(factory=list, init=False)
