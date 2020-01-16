import attr
import abc
from ._core import kw_only
from . import _exception, _thread, _group, _user, _message

#: Default attrs settings for events
attrs_event = attr.s(slots=True, kw_only=kw_only, frozen=True)


@attrs_event
class Event(metaclass=abc.ABCMeta):
    """Base class for all events."""

    @classmethod
    @abc.abstractmethod
    def _parse(cls, session, data):
        raise NotImplementedError


@attrs_event
class UnknownEvent(Event):
    """Represent an unknown event."""

    #: The unknown data. This cannot be relied on, it's only for debugging purposes.
    data = attr.ib()

    @classmethod
    def _parse(cls, session, data):
        raise NotImplementedError


@attrs_event
class ThreadEvent(Event):
    """Represent an event that was done by a user/page in a thread."""

    #: The person who did the action
    author = attr.ib(type=_user.User)  # Or Union[User, Page]?
    #: Thread that the action was done in
    thread = attr.ib(type=_thread.ThreadABC)

    @staticmethod
    def _get_thread(session, data):
        # TODO: Handle pages? Is it even possible?
        key = data["threadKey"]

        if "threadFbId" in key:
            return _group.Group(session=session, id=str(key["threadFbId"]))
        elif "otherUserFbId" in key:
            return _user.User(session=session, id=str(key["otherUserFbId"]))
        raise _exception.ParseError("Could not find thread data", data=data)
