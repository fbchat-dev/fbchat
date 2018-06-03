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
from utils import random_hex, subset
from os import environ


def test_remove_from_and_add_to_group(client1, client2, group, catch_event):
    # Test both methods, while ensuring that the user gets added to the group
    try:
        with catch_event("onPersonRemoved") as x:
            client1.removeUserFromGroup(client2.uid, group["id"])
        assert subset(
            x.res, removed_id=client2.uid, author_id=client1.uid, thread_id=group["id"]
        )
    finally:
        with catch_event("onPeopleAdded") as x:
            mid = client1.addUsersToGroup(client2.uid, group["id"])
        assert subset(
            x.res,
            mid=mid,
            added_ids=[client2.uid],
            author_id=client1.uid,
            thread_id=group["id"],
        )


@pytest.mark.skipif(not environ.get("EXPENSIVE_TESTS"), reason="Often rate limited")
def test_change_title(client1, catch_event, group):
    title = random_hex()
    with catch_event("onTitleChange") as x:
        mid = client1.changeThreadTitle(title, group["id"])
    assert subset(
        x.res,
        mid=mid,
        author_id=client1.uid,
        new_title=title,
        thread_id=group["id"],
        thread_type=ThreadType.GROUP,
    )


def test_change_nickname(client, client_all, catch_event, compare):
    nickname = random_hex()
    with catch_event("onNicknameChange") as x:
        client.changeNickname(nickname, client_all.uid)
    assert compare(x, changed_for=client_all.uid, new_nickname=nickname)


@pytest.mark.parametrize("emoji", ["😀", "😂", "😕", "😍"])
def test_change_emoji(client, catch_event, compare, emoji):
    with catch_event("onEmojiChange") as x:
        client.changeThreadEmoji(emoji)
    assert compare(x, new_emoji=emoji)


@pytest.mark.xfail(FBchatFacebookError)
@pytest.mark.parametrize("emoji", ["🙃", "not an emoji"])
def test_change_emoji_invalid(client, emoji):
    client.changeThreadEmoji(emoji)


@pytest.mark.parametrize(
    "color",
    ThreadColor
    if environ.get("EXPENSIVE_TESTS")
    else [ThreadColor.MESSENGER_BLUE, ThreadColor.PUMPKIN],
)
def test_change_color(client, catch_event, compare, color):
    with catch_event("onColorChange") as x:
        client.changeThreadColor(color)
    assert compare(x, new_color=color)


@pytest.mark.xfail(FBchatFacebookError)
def test_change_colour_invalid(client):
    class InvalidColor:
        value = "#0077ff"

    client.changeThreadColor(InvalidColor())


@pytest.mark.skip("Apparently onTyping is broken")
@pytest.mark.parametrize("status", TypingStatus)
def test_typing_status(client, catch_event, compare, status):
    with catch_event("onTyping") as x:
        client.setTypingStatus(status)
        x.wait(40)
    assert compare(x, status=status)
