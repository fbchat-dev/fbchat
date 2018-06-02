# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import pytest

from fbchat.models import Message, MessageReaction
from utils import threads


@pytest.mark.parametrize("thread", threads)
def test_set_reaction(client, thread):
    mid = client.send(
        Message(text="This message will be reacted to"),
        thread_id=thread["id"],
        thread_type=thread["type"],
    )
    client.reactToMessage(mid, MessageReaction.LOVE)
