import attr
from .._common import kw_only
from .. import _exception, _util, _threads

from typing import Any

#: Default attrs settings for events
attrs_event = attr.s(slots=True, kw_only=kw_only, frozen=True)


@attrs_event
class Event:
    """Base class for all events."""

    @staticmethod
    def _get_thread(session, data):
        # TODO: Handle pages? Is it even possible?
        key = data["threadKey"]

        if "threadFbId" in key:
            return _threads.Group(session=session, id=str(key["threadFbId"]))
        elif "otherUserFbId" in key:
            return _threads.User(session=session, id=str(key["otherUserFbId"]))
        raise _exception.ParseError("Could not find thread data", data=data)


@attrs_event
class UnknownEvent(Event):
    """Represent an unknown event."""

    #: Some data describing the unknown event's origin
    source = attr.ib(type=str)
    #: The unknown data. This cannot be relied on, it's only for debugging purposes.
    data = attr.ib(type=Any)

    @classmethod
    def _parse(cls, session, data):
        raise NotImplementedError


@attrs_event
class ThreadEvent(Event):
    """Represent an event that was done by a user/page in a thread."""

    #: The person who did the action
    author = attr.ib(type="_threads.User")  # Or Union[User, Page]?
    #: Thread that the action was done in
    thread = attr.ib(type="_threads.ThreadABC")

    @classmethod
    def _parse_metadata(cls, session, data):
        metadata = data["messageMetadata"]
        author = _threads.User(session=session, id=metadata["actorFbId"])
        thread = cls._get_thread(session, metadata)
        at = _util.millis_to_datetime(int(metadata["timestamp"]))
        return author, thread, at

    @classmethod
    def _parse_fetch(cls, session, data):
        author = _threads.User(session=session, id=data["message_sender"]["id"])
        at = _util.millis_to_datetime(int(data["timestamp_precise"]))
        return author, at
