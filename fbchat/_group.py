# -*- coding: UTF-8 -*-
from __future__ import unicode_literals

import attr
from . import _plan
from ._thread import ThreadType, Thread


@attr.s(cmp=False, init=False)
class Group(Thread):
    """Represents a Facebook group. Inherits `Thread`."""

    #: Unique list (set) of the group thread's participant user IDs
    participants = attr.ib(factory=set, converter=lambda x: set() if x is None else x)
    #: A dictionary, containing user nicknames mapped to their IDs
    nicknames = attr.ib(factory=dict, converter=lambda x: {} if x is None else x)
    #: A :class:`ThreadColor`. The groups's message color
    color = attr.ib(None)
    #: The groups's default emoji
    emoji = attr.ib(None)
    # Set containing user IDs of thread admins
    admins = attr.ib(factory=set, converter=lambda x: set() if x is None else x)
    # True if users need approval to join
    approval_mode = attr.ib(None)
    # Set containing user IDs requesting to join
    approval_requests = attr.ib(
        factory=set, converter=lambda x: set() if x is None else x
    )
    # Link for joining group
    join_link = attr.ib(None)

    def __init__(
        self,
        uid,
        participants=None,
        nicknames=None,
        color=None,
        emoji=None,
        admins=None,
        approval_mode=None,
        approval_requests=None,
        join_link=None,
        privacy_mode=None,
        **kwargs
    ):
        super(Group, self).__init__(ThreadType.GROUP, uid, **kwargs)
        if participants is None:
            participants = set()
        self.participants = participants
        if nicknames is None:
            nicknames = []
        self.nicknames = nicknames
        self.color = color
        self.emoji = emoji
        if admins is None:
            admins = set()
        self.admins = admins
        self.approval_mode = approval_mode
        if approval_requests is None:
            approval_requests = set()
        self.approval_requests = approval_requests
        self.join_link = join_link

    @classmethod
    def _from_graphql(cls, data):
        if data.get("image") is None:
            data["image"] = {}
        c_info = cls._parse_customization_info(data)
        last_message_timestamp = None
        if "last_message" in data:
            last_message_timestamp = data["last_message"]["nodes"][0][
                "timestamp_precise"
            ]
        plan = None
        if data.get("event_reminders") and data["event_reminders"].get("nodes"):
            plan = _plan.Plan._from_graphql(data["event_reminders"]["nodes"][0])

        return cls(
            data["thread_key"]["thread_fbid"],
            participants=set(
                [
                    node["messaging_actor"]["id"]
                    for node in data["all_participants"]["nodes"]
                ]
            ),
            nicknames=c_info.get("nicknames"),
            color=c_info.get("color"),
            emoji=c_info.get("emoji"),
            admins=set([node.get("id") for node in data.get("thread_admins")]),
            approval_mode=bool(data.get("approval_mode"))
            if data.get("approval_mode") is not None
            else None,
            approval_requests=set(
                node["requester"]["id"]
                for node in data["group_approval_queue"]["nodes"]
            )
            if data.get("group_approval_queue")
            else None,
            join_link=data["joinable_mode"].get("link"),
            photo=data["image"].get("uri"),
            name=data.get("name"),
            message_count=data.get("messages_count"),
            last_message_timestamp=last_message_timestamp,
            plan=plan,
        )

    def _to_send_data(self):
        return {"thread_fbid": self.uid}


@attr.s(cmp=False, init=False)
class Room(Group):
    """Deprecated. Use `Group` instead."""

    # True is room is not discoverable
    privacy_mode = attr.ib(None)

    def __init__(self, uid, privacy_mode=None, **kwargs):
        super(Room, self).__init__(uid, **kwargs)
        self.type = ThreadType.ROOM
        self.privacy_mode = privacy_mode
