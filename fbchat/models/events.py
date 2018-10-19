# -*- coding: UTF-8 -*-

import attr

from random import randint
from time import time
from datetime import datetime
from typing import Union, Optional, T, Type

from .core import ID, JSON
from .threads import Thread, Group, User, Page


__all__ = ("Event",)


@attr.s(slots=True)
class Event:
    """Represents an event in a Facebook thread"""

    #: The unique identifier of the event
    id = attr.ib(type=ID)
    #: The thread the event was sent to
    thread = attr.ib(type=Thread)
    #: The person who sent the event
    actor = attr.ib(type=Union[User, Page])
    #: When the event was sent
    time = attr.ib(type=datetime)
    #: Whether the event is read
    is_read = attr.ib(type=Optional[bool])

    @staticmethod
    def datetime_from_milliseconds(timestamp: float) -> datetime:
        return datetime.fromtimestamp(timestamp / 1000)

    @staticmethod
    def thread_from_pull(metadata: JSON, time: datetime) -> Thread:
        thread_key = metadata["threadKey"]
        if "threadFbId" in thread_key:
            return Group(thread_key["threadFbId"], last_activity=time)
        elif "otherUserFbId" in thread_key:
            return User(thread_key["otherUserFbId"], last_activity=time)
        raise ValueError("Could not find thread ID")

    @classmethod
    def from_pull(cls: Type[T], delta: JSON, **kwargs) -> T:
        self = cls.__new__(cls)

        metadata = delta["messageMetadata"]
        time = cls.datetime_from_milliseconds(float(metadata["timestamp"]))

        self.id = ID(metadata["messageId"])
        self.thread = cls.thread_from_pull(metadata, time)
        self.actor = User(metadata["actorFbId"])
        self.time = time
        self.is_read = None

        return self

    def to_send(self) -> JSON:
        millisecond_timestamp = int(time() * 1000)
        message_id = (millisecond_timestamp << 22) + randint(0, 2 ** 22 - 1)

        return {
            "client": "mercury",
            "timestamp": millisecond_timestamp,
            "source": "source:chat:web",
            "offline_threading_id": message_id,
            "message_id": message_id,
            "ephemeral_ttl_mode": 0,
        }

    @classmethod
    def from_send(
        cls: Type[T], action: JSON, old: T, *, thread: Thread, actor: Union[User, Page]
    ) -> T:
        self = cls.__new__(cls)

        self.id = ID(action["message_id"])
        self.time = cls.time_from_milliseconds(action["timestamp"])
        self.thread = thread
        self.actor = actor
        self.is_read = None

        return self
