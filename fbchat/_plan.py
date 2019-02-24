# -*- coding: UTF-8 -*-
from __future__ import unicode_literals


class Plan(object):
    #: ID of the plan
    uid = None
    #: Plan time (unix time stamp), only precise down to the minute
    time = None
    #: Plan title
    title = None
    #: Plan location name
    location = None
    #: Plan location ID
    location_id = None
    #: ID of the plan creator
    author_id = None
    #: List of the people IDs who will take part in the plan
    going = None
    #: List of the people IDs who won't take part in the plan
    declined = None
    #: List of the people IDs who are invited to the plan
    invited = None

    def __init__(self, time, title, location=None, location_id=None):
        """Represents a plan"""
        self.time = int(time)
        self.title = title
        self.location = location or ""
        self.location_id = location_id or ""
        self.author_id = None
        self.going = []
        self.declined = []
        self.invited = []

    def __repr__(self):
        return self.__unicode__()

    def __unicode__(self):
        return "<Plan ({}): {} time={}, location={}, location_id={}>".format(
            self.uid,
            repr(self.title),
            self.time,
            repr(self.location),
            repr(self.location_id),
        )
