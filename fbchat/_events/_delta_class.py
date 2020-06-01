import attr
import datetime
from ._common import attrs_event, Event, UnknownEvent, ThreadEvent
from . import _delta_type
from .. import _util, _threads, _models

from typing import Sequence, Optional


@attrs_event
class PeopleAdded(ThreadEvent):
    """somebody added people to a group thread."""

    # TODO: Add message id

    thread = attr.ib(type="_threads.Group")  # Set the correct type
    #: The people who got added
    added = attr.ib(type=Sequence["_threads.User"])
    #: When the people were added
    at = attr.ib(type=datetime.datetime)

    @classmethod
    def _parse(cls, session, data):
        author, thread, at = cls._parse_metadata(session, data)
        added = [
            # TODO: Parse user name
            _threads.User(session=session, id=x["userFbId"])
            for x in data["addedParticipants"]
        ]
        return cls(author=author, thread=thread, added=added, at=at)


@attrs_event
class PersonRemoved(ThreadEvent):
    """Somebody removed a person from a group thread."""

    # TODO: Add message id

    thread = attr.ib(type="_threads.Group")  # Set the correct type
    #: Person who got removed
    removed = attr.ib(type="_models.Message")
    #: When the person were removed
    at = attr.ib(type=datetime.datetime)

    @classmethod
    def _parse(cls, session, data):
        author, thread, at = cls._parse_metadata(session, data)
        removed = _threads.User(session=session, id=data["leftParticipantFbId"])
        return cls(author=author, thread=thread, removed=removed, at=at)


@attrs_event
class TitleSet(ThreadEvent):
    """Somebody changed a group's title."""

    thread = attr.ib(type="_threads.Group")  # Set the correct type
    #: The new title. If ``None``, the title was removed
    title = attr.ib(type=Optional[str])
    #: When the title was set
    at = attr.ib(type=datetime.datetime)

    @classmethod
    def _parse(cls, session, data):
        author, thread, at = cls._parse_metadata(session, data)
        return cls(author=author, thread=thread, title=data["name"] or None, at=at)


@attrs_event
class UnfetchedThreadEvent(Event):
    """A message was received, but the data must be fetched manually.

    Use `Message.fetch` to retrieve the message data.

    This is usually used when somebody changes the group's photo, or when a new pending
    group is created.
    """

    # TODO: Present this in a way that users can fetch the changed group photo easily

    #: The thread the message was sent to
    thread = attr.ib(type="_threads.ThreadABC")
    #: The message
    message = attr.ib(type=Optional["_models.Message"])

    @classmethod
    def _parse(cls, session, data):
        thread = cls._get_thread(session, data)
        message = None
        if "messageId" in data:
            message = _models.Message(thread=thread, id=data["messageId"])
        return cls(thread=thread, message=message)


@attrs_event
class MessagesDelivered(ThreadEvent):
    """Somebody marked messages as delivered in a thread."""

    #: The messages that were marked as delivered
    messages = attr.ib(type=Sequence["_models.Message"])
    #: When the messages were delivered
    at = attr.ib(type=datetime.datetime)

    @classmethod
    def _parse(cls, session, data):
        thread = cls._get_thread(session, data)
        if "actorFbId" in data:
            author = _threads.User(session=session, id=data["actorFbId"])
        else:
            author = thread
        messages = [_models.Message(thread=thread, id=x) for x in data["messageIds"]]
        at = _util.millis_to_datetime(int(data["deliveredWatermarkTimestampMs"]))
        return cls(author=author, thread=thread, messages=messages, at=at)


@attrs_event
class ThreadsRead(Event):
    """Somebody marked threads as read/seen."""

    #: The person who marked the threads as read
    author = attr.ib(type="_threads.ThreadABC")
    #: The threads that were marked as read
    threads = attr.ib(type=Sequence["_threads.ThreadABC"])
    #: When the threads were read
    at = attr.ib(type=datetime.datetime)

    @classmethod
    def _parse_read_receipt(cls, session, data):
        author = _threads.User(session=session, id=data["actorFbId"])
        thread = cls._get_thread(session, data)
        at = _util.millis_to_datetime(int(data["actionTimestampMs"]))
        return cls(author=author, threads=[thread], at=at)

    @classmethod
    def _parse(cls, session, data):
        threads = [
            cls._get_thread(session, {"threadKey": x}) for x in data["threadKeys"]
        ]
        at = _util.millis_to_datetime(int(data["actionTimestamp"]))
        return cls(author=session.user, threads=threads, at=at)


@attrs_event
class MessageEvent(ThreadEvent):
    """Somebody sent a message to a thread."""

    #: The sent message
    message = attr.ib(type="_models.Message")
    #: When the threads were read
    at = attr.ib(type=datetime.datetime)

    @classmethod
    def _parse(cls, session, data):
        author, thread, at = cls._parse_metadata(session, data)
        message = _models.MessageData._from_pull(
            thread, data, author=author.id, created_at=at,
        )
        return cls(author=author, thread=thread, message=message, at=at)


@attrs_event
class ThreadFolder(Event):
    """A thread was created in a folder.

    Somebody that isn't connected with you on either Facebook or Messenger sends a
    message. After that, you need to use `ThreadABC.fetch_messages` to actually read it.
    """

    # TODO: Finish this

    #: The created thread
    thread = attr.ib(type="_threads.ThreadABC")
    #: The folder/location
    folder = attr.ib(type="_models.ThreadLocation")

    @classmethod
    def _parse(cls, session, data):
        thread = cls._get_thread(session, data)
        folder = _models.ThreadLocation._parse(data["folder"])
        return cls(thread=thread, folder=folder)


def parse_delta(session, data):
    class_ = data["class"]
    if class_ == "AdminTextMessage":
        return _delta_type.parse_admin_message(session, data)
    elif class_ == "ParticipantsAddedToGroupThread":
        return PeopleAdded._parse(session, data)
    elif class_ == "ParticipantLeftGroupThread":
        return PersonRemoved._parse(session, data)
    elif class_ == "MarkFolderSeen":
        # TODO: Finish this
        folders = [_models.ThreadLocation._parse(folder) for folder in data["folders"]]
        at = _util.millis_to_datetime(int(data["timestamp"]))
        return None
    elif class_ == "ThreadName":
        return TitleSet._parse(session, data)
    elif class_ == "ForcedFetch":
        return UnfetchedThreadEvent._parse(session, data)
    elif class_ == "DeliveryReceipt":
        return MessagesDelivered._parse(session, data)
    elif class_ == "ReadReceipt":
        return ThreadsRead._parse_read_receipt(session, data)
    elif class_ == "MarkRead":
        return ThreadsRead._parse(session, data)
    elif class_ == "NoOp":
        # Skip "no operation" events
        return None
    elif class_ == "NewMessage":
        return MessageEvent._parse(session, data)
    elif class_ == "ThreadFolder":
        return ThreadFolder._parse(session, data)
    elif class_ == "ClientPayload":
        raise ValueError("This is implemented in `parse_events`")
    return UnknownEvent(source="Delta class", data=data)
