# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import pytest

from fbchat.models import Message, MessageReaction


def test_set_reaction(client):
    mid = client.send(Message(text="This message will be reacted to"))
    client.reactToMessage(mid, MessageReaction.LOVE)
