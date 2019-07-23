# -*- coding: UTF-8 -*-
from __future__ import unicode_literals

import attr
import json
from ._core import Enum


class GuestStatus(Enum):
    INVITED = 1
    GOING = 2
    DECLINED = 3


@attr.s(cmp=False)
class Plan(object):
    """Represents a plan."""

    #: ID of the plan
    uid = attr.ib(None, init=False)
    #: Plan time (timestamp), only precise down to the minute
    time = attr.ib(converter=int)
    #: Plan title
    title = attr.ib()
    #: Plan location name
    location = attr.ib(None, converter=lambda x: x or "")
    #: Plan location ID
    location_id = attr.ib(None, converter=lambda x: x or "")
    #: ID of the plan creator
    author_id = attr.ib(None, init=False)
    #: Dictionary of `User` IDs mapped to their `GuestStatus`
    guests = attr.ib(None, init=False)

    @property
    def going(self):
        """List of the `User` IDs who will take part in the plan."""
        return [
            id_
            for id_, status in (self.guests or {}).items()
            if status is GuestStatus.GOING
        ]

    @property
    def declined(self):
        """List of the `User` IDs who won't take part in the plan."""
        return [
            id_
            for id_, status in (self.guests or {}).items()
            if status is GuestStatus.DECLINED
        ]

    @property
    def invited(self):
        """List of the `User` IDs who are invited to the plan."""
        return [
            id_
            for id_, status in (self.guests or {}).items()
            if status is GuestStatus.INVITED
        ]

    @classmethod
    def _from_pull(cls, data):
        rtn = cls(
            time=data.get("event_time"),
            title=data.get("event_title"),
            location=data.get("event_location_name"),
            location_id=data.get("event_location_id"),
        )
        rtn.uid = data.get("event_id")
        rtn.author_id = data.get("event_creator_id")
        rtn.guests = {
            x["node"]["id"]: GuestStatus[x["guest_list_state"]]
            for x in json.loads(data["guest_state_list"])
        }
        return rtn

    @classmethod
    def _from_fetch(cls, data):
        rtn = cls(
            time=data.get("event_time"),
            title=data.get("title"),
            location=data.get("location_name"),
            location_id=str(data["location_id"]) if data.get("location_id") else None,
        )
        rtn.uid = data.get("oid")
        rtn.author_id = data.get("creator_id")
        rtn.guests = {id_: GuestStatus[s] for id_, s in data["event_members"].items()}
        return rtn

    @classmethod
    def _from_graphql(cls, data):
        rtn = cls(
            time=data.get("time"),
            title=data.get("event_title"),
            location=data.get("location_name"),
        )
        rtn.uid = data.get("id")
        rtn.author_id = data["lightweight_event_creator"].get("id")
        rtn.guests = {
            x["node"]["id"]: GuestStatus[x["guest_list_state"]]
            for x in data["event_reminder_members"]["edges"]
        }
        return rtn
