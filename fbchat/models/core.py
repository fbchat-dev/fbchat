# -*- coding: UTF-8 -*-

from __future__ import unicode_literals

import json
import attr

from random import randint
from time import time

from datetime import datetime, timedelta
from typing import Dict, Set, List, Union
from enum import Enum


@attr.s(slots=True)
class Dimension(object):
    """Represents the width and height of an object"""

    #: Width of the object
    width = attr.ib(type=int, converter=int)
    #: Height of the object
    height = attr.ib(type=int, converter=int)

    @classmethod
    def from_dict(cls, items):
        return cls(items["width"], items["height"])


@attr.s(slots=True, str=True)
class FacebookError(Exception):
    """Thrown when Facebook returns an error"""

    #: The error code that Facebook returned
    fb_error_code = attr.ib(type=int, converter=int)
    #: A localized error message that Facebook returned
    fb_error_message = attr.ib(type=str)


@attr.s(slots=True)
class Event(object):
    """Represents an event in a Facebook thread"""

    #: The unique identifier of the event
    id = attr.ib(None, type=str)
    #: The thread the event was sent to
    thread = attr.ib(None, type=Thread)
    #: The person who sent the event
    actor = attr.ib(None, type=Union[User, Page])
    #: When the event was sent
    time = attr.ib(None, type=datetime)
    #: Whether the event is read
    is_read = attr.ib(None, type=bool)

    def __eq__(self, other):
        return isinstance(other, Event) and self.id == other.id

    def __ne__(self, other):
        return not self.__eq__(other)

    @staticmethod
    def time_from_milliseconds(timestamp):
        return datetime.fromtimestamp(int(timestamp) / 1000)

    @staticmethod
    def pull_data_get_thread(delta, time):
        thread_key = delta["messageMetadata"]["threadKey"]
        if "threadFbId" in thread_key:
            return Group(thread_key["threadFbId"], last_activity=time)
        elif "otherUserFbId" in thread_key:
            return User(thread_key["otherUserFbId"], last_activity=time)

    @classmethod
    def from_pull(cls, delta, **kwargs):
        metadata = delta["messageMetadata"]
        return cls(
            id=metadata["messageId"],
            thread=cls.pull_data_get_thread(delta, time),
            actor=User(metadata["actorFbId"]),
            time=cls.time_from_milliseconds(metadata["timestamp"]),
            **kwargs
        )

    def to_send(self, **kwargs):
        millisecond_timestamp = int(time() * 1000)
        message_id = (millisecond_timestamp << 22) + randint(0, 2 ** 22 - 1)

        return dict(
            client="mercury",
            timestamp=millisecond_timestamp,
            source="source:chat:web",
            offline_threading_id=message_id,
            message_id=message_id,
            ephemeral_ttl_mode=0,
            **kwargs
        )

    @classmethod
    def from_send(cls, action, old, **kwargs):
        # `thread` and `actor` should be set by the caller in `kwargs`
        return cls(
            id=action["message_id"],
            time=cls.time_from_milliseconds(action["timestamp"]),
            **kwargs
        )
