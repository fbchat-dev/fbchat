# -*- coding: UTF-8 -*-
from __future__ import unicode_literals


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
