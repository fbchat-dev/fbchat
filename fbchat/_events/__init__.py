import attr
import datetime
from ._common import attrs_event, Event, UnknownEvent, ThreadEvent
from ._client_payload import *
from ._delta_class import *
from ._delta_type import *

from .. import _exception, _threads, _models

from typing import Mapping


@attrs_event
class Typing(ThreadEvent):
    """Somebody started/stopped typing in a thread."""

    #: ``True`` if the user started typing, ``False`` if they stopped
    status = attr.ib(type=bool)

    @classmethod
    def _parse_orca(cls, session, data):
        author = _threads.User(session=session, id=str(data["sender_fbid"]))
        status = data["state"] == 1
        return cls(author=author, thread=author, status=status)

    @classmethod
    def _parse_thread_typing(cls, session, data):
        author = _threads.User(session=session, id=str(data["sender_fbid"]))
        thread = _threads.Group(session=session, id=str(data["thread"]))
        status = data["state"] == 1
        return cls(author=author, thread=thread, status=status)


@attrs_event
class FriendRequest(Event):
    """Somebody sent a friend request."""

    #: The user that sent the request
    author = attr.ib(type="_threads.User")

    @classmethod
    def _parse(cls, session, data):
        author = _threads.User(session=session, id=str(data["from"]))
        return cls(author=author)


@attrs_event
class Presence(Event):
    """The list of active statuses was updated.

    Chat online presence update.
    """

    # TODO: Document this better!

    #: User ids mapped to their active status
    statuses = attr.ib(type=Mapping[str, "_models.ActiveStatus"])
    #: ``True`` if the list is fully updated and ``False`` if it's partially updated
    full = attr.ib(type=bool)

    @classmethod
    def _parse(cls, session, data):
        statuses = {
            str(d["u"]): _models.ActiveStatus._from_orca_presence(d)
            for d in data["list"]
        }
        return cls(statuses=statuses, full=data["list_type"] == "full")


@attrs_event
class Connect(Event):
    """The client was connected to Facebook.

    This is not guaranteed to be triggered the same amount of times `Disconnect`!
    """


@attrs_event
class Disconnect(Event):
    """The client lost the connection to Facebook.

    This is not guaranteed to be triggered the same amount of times `Connect`!
    """

    #: The reason / error string for the disconnect
    reason = attr.ib(type=str)


def parse_events(session, topic, data):
    # See Mqtt._configure_connect_options for information about these topics
    try:
        if topic == "/t_ms":
            # `deltas` will always be available, since we're filtering out the things
            # that don't have it earlier in the MQTT listener
            for delta in data["deltas"]:
                if delta["class"] == "ClientPayload":
                    yield from parse_client_payloads(session, delta)
                    continue
                try:
                    event = parse_delta(session, delta)
                    if event:  # Skip `None`
                        yield event
                except _exception.ParseError:
                    raise
                except Exception as e:
                    raise _exception.ParseError(
                        "Error parsing delta", data=delta
                    ) from e

        elif topic == "/thread_typing":
            yield Typing._parse_thread_typing(session, data)

        elif topic == "/orca_typing_notifications":
            yield Typing._parse_orca(session, data)

        elif topic == "/legacy_web":
            if data["type"] == "jewel_requests_add":
                yield FriendRequest._parse(session, data)
            else:
                yield UnknownEvent(source="/legacy_web", data=data)

        elif topic == "/orca_presence":
            yield Presence._parse(session, data)

        else:
            yield UnknownEvent(source=topic, data=data)
    except _exception.ParseError:
        raise
    except Exception as e:
        raise _exception.ParseError(
            "Error parsing MQTT topic {}".format(topic), data=data
        ) from e
