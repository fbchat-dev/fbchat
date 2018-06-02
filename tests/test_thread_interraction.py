# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import pytest

from fbchat.models import (
    Message,
    ThreadType,
    FBchatFacebookError,
    TypingStatus,
    ThreadColor,
)
from utils import set_default_client, threads


@pytest.mark.parametrize("thread", threads)
def test_remove_from_and_add_to_group(client1, client2, thread):
    if thread["type"] != ThreadType.GROUP:
        return
    # Test both methods, while ensuring that the user gets added to the group
    try:
        client1.removeUserFromGroup(client2.uid, thread["id"])
    finally:
        client1.addUsersToGroup(client2.uid, thread["id"])


@pytest.mark.skip("Blocked because of something")
@pytest.mark.parametrize("thread", threads)
def test_change_thread_title(client, thread):
    with set_default_client(client, thread):
        client.changeThreadTitle("A Title")


@pytest.mark.parametrize("thread", threads)
def test_change_nickname(client1, client2, thread):
    with set_default_client(client1, thread):
        client1.changeNickname("test_changeNicknameSelf★", client1.uid)
        client1.changeNickname("test_changeNicknameOther★", client2.uid)


@pytest.mark.parametrize("thread", threads)
def test_change_thread_emoji(client, thread):
    with set_default_client(client, thread):
        client.changeThreadEmoji("😀")
        client.changeThreadEmoji("😀")


@pytest.mark.parametrize("thread", threads)
def test_change_thread_colour(client, thread):
    with set_default_client(client, thread):
        client.changeThreadColor(ThreadColor.BRILLIANT_ROSE)
        client.changeThreadColor(ThreadColor.MESSENGER_BLUE)


@pytest.mark.parametrize("thread", threads)
def test_typing_status(client, thread):
    with set_default_client(client, thread):
        client.setTypingStatus(TypingStatus.TYPING)
        client.setTypingStatus(TypingStatus.STOPPED)
