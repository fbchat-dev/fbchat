import attr
import datetime
import enum
from .._common import attrs_default
from .. import _exception, _util, _session

from typing import Mapping, Sequence, Optional


class GuestStatus(enum.Enum):
    INVITED = 1
    GOING = 2
    DECLINED = 3


ACONTEXT = {
    "action_history": [
        {"surface": "messenger_chat_tab", "mechanism": "messenger_composer"}
    ]
}


@attrs_default
class Plan:
    """Base model for plans.

    Example:
        >>> plan = fbchat.Plan(session=session, id="1234")
    """

    #: The session to use when making requests.
    session = attr.ib(type=_session.Session)
    #: The plan's unique identifier.
    id = attr.ib(converter=str, type=str)

    def fetch(self) -> "PlanData":
        """Fetch fresh `PlanData` object.

        Example:
            >>> plan = plan.fetch()
            >>> plan.title
            "A plan"
        """
        data = {"event_reminder_id": self.id}
        j = self.session._payload_post("/ajax/eventreminder", data)
        return PlanData._from_fetch(self.session, j)

    @classmethod
    def _create(
        cls,
        thread,
        name: str,
        at: datetime.datetime,
        location_name: str = None,
        location_id: str = None,
    ):
        data = {
            "event_type": "EVENT",
            "event_time": _util.datetime_to_seconds(at),
            "title": name,
            "thread_id": thread.id,
            "location_id": location_id or "",
            "location_name": location_name or "",
            "acontext": ACONTEXT,
        }
        j = thread.session._payload_post("/ajax/eventreminder/create", data)
        if "error" in j:
            raise _exception.ExternalError("Failed creating plan", j["error"])

    def edit(
        self,
        name: str,
        at: datetime.datetime,
        location_name: str = None,
        location_id: str = None,
    ):
        """Edit the plan.

        # TODO: Arguments
        """
        data = {
            "event_reminder_id": self.id,
            "delete": "false",
            "date": _util.datetime_to_seconds(at),
            "location_name": location_name or "",
            "location_id": location_id or "",
            "title": name,
            "acontext": ACONTEXT,
        }
        j = self.session._payload_post("/ajax/eventreminder/submit", data)

    def delete(self):
        """Delete the plan.

        Example:
            >>> plan.delete()
        """
        data = {"event_reminder_id": self.id, "delete": "true", "acontext": ACONTEXT}
        j = self.session._payload_post("/ajax/eventreminder/submit", data)

    def _change_participation(self):
        data = {
            "event_reminder_id": self.id,
            "guest_state": "GOING" if take_part else "DECLINED",
            "acontext": ACONTEXT,
        }
        j = self.session._payload_post("/ajax/eventreminder/rsvp", data)

    def participate(self):
        """Set yourself as GOING/participating to the plan.

        Example:
            >>> plan.participate()
        """
        return self._change_participation(True)

    def decline(self):
        """Set yourself as having DECLINED the plan.

        Example:
            >>> plan.decline()
        """
        return self._change_participation(False)


@attrs_default
class PlanData(Plan):
    """Represents data about a plan."""

    #: Plan time, only precise down to the minute
    time = attr.ib(type=datetime.datetime)
    #: Plan title
    title = attr.ib(type=str)
    #: Plan location name
    location = attr.ib(None, converter=lambda x: x or "", type=Optional[str])
    #: Plan location ID
    location_id = attr.ib(None, converter=lambda x: x or "", type=Optional[str])
    #: ID of the plan creator
    author_id = attr.ib(None, type=Optional[str])
    #: `User` ids mapped to their `GuestStatus`
    guests = attr.ib(None, type=Optional[Mapping[str, GuestStatus]])

    @property
    def going(self) -> Sequence[str]:
        """List of the `User` IDs who will take part in the plan."""
        return [
            id_
            for id_, status in (self.guests or {}).items()
            if status is GuestStatus.GOING
        ]

    @property
    def declined(self) -> Sequence[str]:
        """List of the `User` IDs who won't take part in the plan."""
        return [
            id_
            for id_, status in (self.guests or {}).items()
            if status is GuestStatus.DECLINED
        ]

    @property
    def invited(self) -> Sequence[str]:
        """List of the `User` IDs who are invited to the plan."""
        return [
            id_
            for id_, status in (self.guests or {}).items()
            if status is GuestStatus.INVITED
        ]

    @classmethod
    def _from_pull(cls, session, data):
        return cls(
            session=session,
            id=data.get("event_id"),
            time=_util.seconds_to_datetime(int(data.get("event_time"))),
            title=data.get("event_title"),
            location=data.get("event_location_name"),
            location_id=data.get("event_location_id"),
            author_id=data.get("event_creator_id"),
            guests={
                x["node"]["id"]: GuestStatus[x["guest_list_state"]]
                for x in _util.parse_json(data["guest_state_list"])
            },
        )

    @classmethod
    def _from_fetch(cls, session, data):
        return cls(
            session=session,
            id=data.get("oid"),
            time=_util.seconds_to_datetime(data.get("event_time")),
            title=data.get("title"),
            location=data.get("location_name"),
            location_id=str(data["location_id"]) if data.get("location_id") else None,
            author_id=data.get("creator_id"),
            guests={id_: GuestStatus[s] for id_, s in data["event_members"].items()},
        )

    @classmethod
    def _from_graphql(cls, session, data):
        return cls(
            session=session,
            id=data.get("id"),
            time=_util.seconds_to_datetime(data.get("time")),
            title=data.get("event_title"),
            location=data.get("location_name"),
            author_id=data["lightweight_event_creator"].get("id"),
            guests={
                x["node"]["id"]: GuestStatus[x["guest_list_state"]]
                for x in data["event_reminder_members"]["edges"]
            },
        )
