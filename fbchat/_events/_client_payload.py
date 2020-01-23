import attr
import datetime
from ._common import attrs_event, UnknownEvent, ThreadEvent
from .. import _exception, _util, _threads, _models

from typing import Optional


@attrs_event
class ReactionEvent(ThreadEvent):
    """Somebody reacted to a message."""

    #: Message that the user reacted to
    message = attr.ib(type="_models.Message")

    reaction = attr.ib(type=Optional[str])
    """The reaction.

    Not limited to the ones in `Message.react`.

    If ``None``, the reaction was removed.
    """

    @classmethod
    def _parse(cls, session, data):
        thread = cls._get_thread(session, data)
        return cls(
            author=_threads.User(session=session, id=str(data["userId"])),
            thread=thread,
            message=_models.Message(thread=thread, id=data["messageId"]),
            reaction=data["reaction"] if data["action"] == 0 else None,
        )


@attrs_event
class UserStatusEvent(ThreadEvent):
    #: Whether the user was blocked or unblocked
    blocked = attr.ib(type=bool)

    @classmethod
    def _parse(cls, session, data):
        return cls(
            author=_threads.User(session=session, id=str(data["actorFbid"])),
            thread=cls._get_thread(session, data),
            blocked=not data["canViewerReply"],
        )


@attrs_event
class LiveLocationEvent(ThreadEvent):
    """Somebody sent live location info."""

    # TODO: This!

    @classmethod
    def _parse(cls, session, data):
        from . import _location

        thread = cls._get_thread(session, data)
        for location_data in data["messageLiveLocations"]:
            message = _models.Message(thread=thread, id=data["messageId"])
            author = _threads.User(session=session, id=str(location_data["senderId"]))
            location = _location.LiveLocationAttachment._from_pull(location_data)

        return None


@attrs_event
class UnsendEvent(ThreadEvent):
    """Somebody unsent a message (which deletes it for everyone)."""

    #: The unsent message
    message = attr.ib(type="_models.Message")
    #: When the message was unsent
    at = attr.ib(type=datetime.datetime)

    @classmethod
    def _parse(cls, session, data):
        thread = cls._get_thread(session, data)
        return cls(
            author=_threads.User(session=session, id=str(data["senderID"])),
            thread=thread,
            message=_models.Message(thread=thread, id=data["messageID"]),
            at=_util.millis_to_datetime(data["deletionTimestamp"]),
        )


@attrs_event
class MessageReplyEvent(ThreadEvent):
    """Somebody replied to a message."""

    #: The sent message
    message = attr.ib(type="_models.MessageData")
    #: The message that was replied to
    replied_to = attr.ib(type="_models.MessageData")

    @classmethod
    def _parse(cls, session, data):
        metadata = data["message"]["messageMetadata"]
        thread = cls._get_thread(session, metadata)
        return cls(
            author=_threads.User(session=session, id=str(metadata["actorFbId"])),
            thread=thread,
            message=_models.MessageData._from_reply(thread, data["message"]),
            replied_to=_models.MessageData._from_reply(
                thread, data["repliedToMessage"]
            ),
        )


def parse_client_delta(session, data):
    if "deltaMessageReaction" in data:
        return ReactionEvent._parse(session, data["deltaMessageReaction"])
    elif "deltaChangeViewerStatus" in data:
        # TODO: Parse all `reason`
        if data["deltaChangeViewerStatus"]["reason"] == 2:
            return UserStatusEvent._parse(session, data["deltaChangeViewerStatus"])
    elif "liveLocationData" in data:
        return LiveLocationEvent._parse(session, data["liveLocationData"])
    elif "deltaRecallMessageData" in data:
        return UnsendEvent._parse(session, data["deltaRecallMessageData"])
    elif "deltaMessageReply" in data:
        return MessageReplyEvent._parse(session, data["deltaMessageReply"])
    return UnknownEvent(source="client payload", data=data)


def parse_client_payloads(session, data):
    payload = _util.parse_json("".join(chr(z) for z in data["payload"]))

    try:
        for delta in payload["deltas"]:
            yield parse_client_delta(session, delta)
    except _exception.ParseError:
        raise
    except Exception as e:
        raise _exception.ParseError("Error parsing ClientPayload", data=payload) from e
