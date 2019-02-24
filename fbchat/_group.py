# -*- coding: UTF-8 -*-
from __future__ import unicode_literals

from ._thread import ThreadType, Thread


class Group(Thread):
    #: Unique list (set) of the group thread's participant user IDs
    participants = None
    #: A dict, containing user nicknames mapped to their IDs
    nicknames = None
    #: A :class:`ThreadColor`. The groups's message color
    color = None
    #: The groups's default emoji
    emoji = None
    # Set containing user IDs of thread admins
    admins = None
    # True if users need approval to join
    approval_mode = None
    # Set containing user IDs requesting to join
    approval_requests = None
    # Link for joining group
    join_link = None

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
        """Represents a Facebook group. Inherits `Thread`"""
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


class Room(Group):
    # True is room is not discoverable
    privacy_mode = None

    def __init__(self, uid, privacy_mode=None, **kwargs):
        """Deprecated. Use :class:`Group` instead"""
        super(Room, self).__init__(uid, **kwargs)
        self.type = ThreadType.ROOM
        self.privacy_mode = privacy_mode
