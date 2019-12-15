# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import pytest

from fbchat.models import Message, MessageReaction
from utils import subset


def test_set_reaction(client):
    mid = client.send(Message(text="This message will be reacted to"))
    client.reactToMessage(mid, MessageReaction.LOVE)


def test_delete_messages(client):
    text1 = "This message will stay"
    text2 = "This message will be removed"
    mid1 = client.sendMessage(text1)
    mid2 = client.sendMessage(text2)
    client.deleteMessages(mid2)
    (message,) = client.fetchThreadMessages(limit=1)
    assert subset(vars(message), uid=mid1, author=client.uid, text=text1)
