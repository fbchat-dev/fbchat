# -*- coding: UTF-8 -*-
from __future__ import unicode_literals

from ._core import Enum


class ThreadType(Enum):
    """Used to specify what type of Facebook thread is being used. See :ref:`intro_threads` for more info"""

    USER = 1
    GROUP = 2
    ROOM = 2
    PAGE = 3


class ThreadLocation(Enum):
    """Used to specify where a thread is located (inbox, pending, archived, other)."""

    INBOX = "INBOX"
    PENDING = "PENDING"
    ARCHIVED = "ARCHIVED"
    OTHER = "OTHER"


class ThreadColor(Enum):
    """Used to specify a thread colors"""

    MESSENGER_BLUE = "#0084ff"
    VIKING = "#44bec7"
    GOLDEN_POPPY = "#ffc300"
    RADICAL_RED = "#fa3c4c"
    SHOCKING = "#d696bb"
    PICTON_BLUE = "#6699cc"
    FREE_SPEECH_GREEN = "#13cf13"
    PUMPKIN = "#ff7e29"
    LIGHT_CORAL = "#e68585"
    MEDIUM_SLATE_BLUE = "#7646ff"
    DEEP_SKY_BLUE = "#20cef5"
    FERN = "#67b868"
    CAMEO = "#d4a88c"
    BRILLIANT_ROSE = "#ff5ca1"
    BILOBA_FLOWER = "#a695c7"


class Thread(object):
    #: The unique identifier of the thread. Can be used a `thread_id`. See :ref:`intro_threads` for more info
    uid = None
    #: Specifies the type of thread. Can be used a `thread_type`. See :ref:`intro_threads` for more info
    type = None
    #: A url to the thread's picture
    photo = None
    #: The name of the thread
    name = None
    #: Timestamp of last message
    last_message_timestamp = None
    #: Number of messages in the thread
    message_count = None
    #: Set :class:`Plan`
    plan = None

    def __init__(
        self,
        _type,
        uid,
        photo=None,
        name=None,
        last_message_timestamp=None,
        message_count=None,
        plan=None,
    ):
        """Represents a Facebook thread"""
        self.uid = str(uid)
        self.type = _type
        self.photo = photo
        self.name = name
        self.last_message_timestamp = last_message_timestamp
        self.message_count = message_count
        self.plan = plan

    def __repr__(self):
        return self.__unicode__()

    def __unicode__(self):
        return "<{} {} ({})>".format(self.type.name, self.name, self.uid)
