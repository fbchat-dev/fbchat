import attr
import datetime
from ._common import attrs_event, Event, UnknownEvent, ThreadEvent
from .. import _util, _threads, _models

from typing import Sequence, Optional


@attrs_event
class ColorSet(ThreadEvent):
    """Somebody set the color in a thread."""

    #: The new color. Not limited to the ones in `ThreadABC.set_color`
    color = attr.ib(type=str)
    #: When the color was set
    at = attr.ib(type=datetime.datetime)

    @classmethod
    def _parse(cls, session, data):
        author, thread, at = cls._parse_metadata(session, data)
        color = _threads.ThreadABC._parse_color(data["untypedData"]["theme_color"])
        return cls(author=author, thread=thread, color=color, at=at)


@attrs_event
class EmojiSet(ThreadEvent):
    """Somebody set the emoji in a thread."""

    #: The new emoji
    emoji = attr.ib(type=str)
    #: When the emoji was set
    at = attr.ib(type=datetime.datetime)

    @classmethod
    def _parse(cls, session, data):
        author, thread, at = cls._parse_metadata(session, data)
        emoji = data["untypedData"]["thread_icon"]
        return cls(author=author, thread=thread, emoji=emoji, at=at)


@attrs_event
class NicknameSet(ThreadEvent):
    """Somebody set the nickname of a person in a thread."""

    #: The person whose nickname was set
    subject = attr.ib(type=str)
    #: The new nickname. If ``None``, the nickname was cleared
    nickname = attr.ib(type=Optional[str])
    #: When the nickname was set
    at = attr.ib(type=datetime.datetime)

    @classmethod
    def _parse(cls, session, data):
        author, thread, at = cls._parse_metadata(session, data)
        subject = _threads.User(
            session=session, id=data["untypedData"]["participant_id"]
        )
        nickname = data["untypedData"]["nickname"] or None  # None if ""
        return cls(
            author=author, thread=thread, subject=subject, nickname=nickname, at=at
        )


@attrs_event
class AdminsAdded(ThreadEvent):
    """Somebody added admins to a group."""

    #: The people that were set as admins
    added = attr.ib(type=Sequence["_threads.User"])
    #: When the admins were added
    at = attr.ib(type=datetime.datetime)

    @classmethod
    def _parse(cls, session, data):
        author, thread, at = cls._parse_metadata(session, data)
        subject = _threads.User(session=session, id=data["untypedData"]["TARGET_ID"])
        return cls(author=author, thread=thread, added=[subject], at=at)


@attrs_event
class AdminsRemoved(ThreadEvent):
    """Somebody removed admins from a group."""

    #: The people that were removed as admins
    removed = attr.ib(type=Sequence["_threads.User"])
    #: When the admins were removed
    at = attr.ib(type=datetime.datetime)

    @classmethod
    def _parse(cls, session, data):
        author, thread, at = cls._parse_metadata(session, data)
        subject = _threads.User(session=session, id=data["untypedData"]["TARGET_ID"])
        return cls(author=author, thread=thread, removed=[subject], at=at)


@attrs_event
class ApprovalModeSet(ThreadEvent):
    """Somebody changed the approval mode in a group."""

    require_admin_approval = attr.ib(type=bool)
    #: When the approval mode was set
    at = attr.ib(type=datetime.datetime)

    @classmethod
    def _parse(cls, session, data):
        author, thread, at = cls._parse_metadata(session, data)
        raa = data["untypedData"]["APPROVAL_MODE"] == "1"
        return cls(author=author, thread=thread, require_admin_approval=raa, at=at)


@attrs_event
class CallStarted(ThreadEvent):
    """Somebody started a call."""

    #: When the call was started
    at = attr.ib(type=datetime.datetime)

    @classmethod
    def _parse(cls, session, data):
        author, thread, at = cls._parse_metadata(session, data)
        return cls(author=author, thread=thread, at=at)


@attrs_event
class CallEnded(ThreadEvent):
    """Somebody ended a call."""

    #: How long the call took
    duration = attr.ib(type=datetime.timedelta)
    #: When the call ended
    at = attr.ib(type=datetime.datetime)

    @classmethod
    def _parse(cls, session, data):
        author, thread, at = cls._parse_metadata(session, data)
        duration = _util.seconds_to_timedelta(int(data["untypedData"]["call_duration"]))
        return cls(author=author, thread=thread, duration=duration, at=at)


@attrs_event
class CallJoined(ThreadEvent):
    """Somebody joined a call."""

    #: When the call ended
    at = attr.ib(type=datetime.datetime)

    @classmethod
    def _parse(cls, session, data):
        author, thread, at = cls._parse_metadata(session, data)
        return cls(author=author, thread=thread, at=at)


@attrs_event
class PollCreated(ThreadEvent):
    """Somebody created a group poll."""

    #: The new poll
    poll = attr.ib(type="_models.Poll")
    #: When the poll was created
    at = attr.ib(type=datetime.datetime)

    @classmethod
    def _parse(cls, session, data):
        author, thread, at = cls._parse_metadata(session, data)
        poll_data = _util.parse_json(data["untypedData"]["question_json"])
        poll = _models.Poll._from_graphql(session, poll_data)
        return cls(author=author, thread=thread, poll=poll, at=at)


@attrs_event
class PollVoted(ThreadEvent):
    """Somebody voted in a group poll."""

    #: The updated poll
    poll = attr.ib(type="_models.Poll")
    #: Ids of the voted options
    added_ids = attr.ib(type=Sequence[str])
    #: Ids of the un-voted options
    removed_ids = attr.ib(type=Sequence[str])
    #: When the poll was voted in
    at = attr.ib(type=datetime.datetime)

    @classmethod
    def _parse(cls, session, data):
        author, thread, at = cls._parse_metadata(session, data)
        poll_data = _util.parse_json(data["untypedData"]["question_json"])
        poll = _models.Poll._from_graphql(session, poll_data)
        added_ids = _util.parse_json(data["untypedData"]["added_option_ids"])
        removed_ids = _util.parse_json(data["untypedData"]["removed_option_ids"])
        return cls(
            author=author,
            thread=thread,
            poll=poll,
            added_ids=[str(x) for x in added_ids],
            removed_ids=[str(x) for x in removed_ids],
            at=at,
        )


@attrs_event
class PlanCreated(ThreadEvent):
    """Somebody created a plan in a group."""

    #: The new plan
    plan = attr.ib(type="_models.PlanData")
    #: When the plan was created
    at = attr.ib(type=datetime.datetime)

    @classmethod
    def _parse(cls, session, data):
        author, thread, at = cls._parse_metadata(session, data)
        plan = _models.PlanData._from_pull(session, data["untypedData"])
        return cls(author=author, thread=thread, plan=plan, at=at)


@attrs_event
class PlanEnded(ThreadEvent):
    """A plan ended."""

    #: The ended plan
    plan = attr.ib(type="_models.PlanData")
    #: When the plan ended
    at = attr.ib(type=datetime.datetime)

    @classmethod
    def _parse(cls, session, data):
        author, thread, at = cls._parse_metadata(session, data)
        plan = _models.PlanData._from_pull(session, data["untypedData"])
        return cls(author=author, thread=thread, plan=plan, at=at)


@attrs_event
class PlanEdited(ThreadEvent):
    """Somebody changed a plan in a group."""

    #: The updated plan
    plan = attr.ib(type="_models.PlanData")
    #: When the plan was updated
    at = attr.ib(type=datetime.datetime)

    @classmethod
    def _parse(cls, session, data):
        author, thread, at = cls._parse_metadata(session, data)
        plan = _models.PlanData._from_pull(session, data["untypedData"])
        return cls(author=author, thread=thread, plan=plan, at=at)


@attrs_event
class PlanDeleted(ThreadEvent):
    """Somebody removed a plan in a group."""

    #: The removed plan
    plan = attr.ib(type="_models.PlanData")
    #: When the plan was removed
    at = attr.ib(type=datetime.datetime)

    @classmethod
    def _parse(cls, session, data):
        author, thread, at = cls._parse_metadata(session, data)
        plan = _models.PlanData._from_pull(session, data["untypedData"])
        return cls(author=author, thread=thread, plan=plan, at=at)


@attrs_event
class PlanResponded(ThreadEvent):
    """Somebody responded to a plan in a group."""

    #: The plan that was responded to
    plan = attr.ib(type="_models.PlanData")
    #: Whether the author will go to the plan or not
    take_part = attr.ib(type=bool)
    #: When the plan was removed
    at = attr.ib(type=datetime.datetime)

    @classmethod
    def _parse(cls, session, data):
        author, thread, at = cls._parse_metadata(session, data)
        plan = _models.PlanData._from_pull(session, data["untypedData"])
        take_part = data["untypedData"]["guest_status"] == "GOING"
        return cls(author=author, thread=thread, plan=plan, take_part=take_part, at=at)


def parse_admin_message(session, data):
    type_ = data["type"]
    if type_ == "change_thread_theme":
        return ColorSet._parse(session, data)
    elif type_ == "change_thread_icon":
        return EmojiSet._parse(session, data)
    elif type_ == "change_thread_nickname":
        return NicknameSet._parse(session, data)
    elif type_ == "change_thread_admins":
        event_type = data["untypedData"]["ADMIN_EVENT"]
        if event_type == "add_admin":
            return AdminsAdded._parse(session, data)
        elif event_type == "remove_admin":
            return AdminsRemoved._parse(session, data)
        else:
            pass
    elif type_ == "change_thread_approval_mode":
        return ApprovalModeSet._parse(session, data)
    elif type_ == "instant_game_update":
        pass  # TODO: This
    elif type_ == "messenger_call_log":  # Previously "rtc_call_log"
        event_type = data["untypedData"]["event"]
        if event_type == "group_call_started":
            return CallStarted._parse(session, data)
        elif event_type in ["group_call_ended", "one_on_one_call_ended"]:
            return CallEnded._parse(session, data)
        else:
            pass
    elif type_ == "participant_joined_group_call":
        return CallJoined._parse(session, data)
    elif type_ == "group_poll":
        event_type = data["untypedData"]["event_type"]
        if event_type == "question_creation":
            return PollCreated._parse(session, data)
        elif event_type == "update_vote":
            return PollVoted._parse(session, data)
        else:
            pass
    elif type_ == "lightweight_event_create":
        return PlanCreated._parse(session, data)
    elif type_ == "lightweight_event_notify":
        return PlanEnded._parse(session, data)
    elif type_ == "lightweight_event_update":
        return PlanEdited._parse(session, data)
    elif type_ == "lightweight_event_delete":
        return PlanDeleted._parse(session, data)
    elif type_ == "lightweight_event_rsvp":
        return PlanResponded._parse(session, data)
    return UnknownEvent(source="Delta type", data=data)
