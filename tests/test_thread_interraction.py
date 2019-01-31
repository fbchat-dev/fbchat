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
from os import path


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
            client1.addUsersToGroup(client2.uid, group["id"])
        assert subset(
            x.res, added_ids=[client2.uid], author_id=client1.uid, thread_id=group["id"]
        )


def test_remove_from_and_add_admins_to_group(client1, client2, group, catch_event):
    # Test both methods, while ensuring that the user gets added as group admin
    try:
        with catch_event("onAdminRemoved") as x:
            client1.removeGroupAdmins(client2.uid, group["id"])
        assert subset(
            x.res, removed_id=client2.uid, author_id=client1.uid, thread_id=group["id"]
        )
    finally:
        with catch_event("onAdminAdded") as x:
            client1.addGroupAdmins(client2.uid, group["id"])
        assert subset(
            x.res, added_id=client2.uid, author_id=client1.uid, thread_id=group["id"]
        )


def test_change_title(client1, group, catch_event):
    title = random_hex()
    with catch_event("onTitleChange") as x:
        client1.changeThreadTitle(title, group["id"], thread_type=ThreadType.GROUP)
    assert subset(
        x.res,
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


@pytest.mark.parametrize(
    "emoji",
    [
        "😀",
        "😂",
        "😕",
        "😍",
        pytest.param("🙃", marks=[pytest.mark.xfail(raises=FBchatFacebookError)]),
        pytest.param(
            "not an emoji", marks=[pytest.mark.xfail(raises=FBchatFacebookError)]
        ),
    ],
)
def test_change_emoji(client, catch_event, compare, emoji):
    with catch_event("onEmojiChange") as x:
        client.changeThreadEmoji(emoji)
    assert compare(x, new_emoji=emoji)


def test_change_image_local(client1, group, catch_event):
    url = path.join(path.dirname(__file__), "resources", "image.png")
    with catch_event("onImageChange") as x:
        image_id = client1.changeGroupImageLocal(url, group["id"])
    assert subset(
        x.res, new_image=image_id, author_id=client1.uid, thread_id=group["id"]
    )


# To be changed when merged into master
def test_change_image_remote(client1, group, catch_event):
    url = "https://github.com/carpedm20/fbchat/raw/master/tests/image.png"
    with catch_event("onImageChange") as x:
        image_id = client1.changeGroupImageRemote(url, group["id"])
    assert subset(
        x.res, new_image=image_id, author_id=client1.uid, thread_id=group["id"]
    )


@pytest.mark.parametrize(
    "color",
    [
        x
        if x in [ThreadColor.MESSENGER_BLUE, ThreadColor.PUMPKIN]
        else pytest.param(x, marks=[pytest.mark.expensive()])
        for x in ThreadColor
    ],
)
def test_change_color(client, catch_event, compare, color):
    with catch_event("onColorChange") as x:
        client.changeThreadColor(color)
    assert compare(x, new_color=color)


@pytest.mark.xfail(raises=FBchatFacebookError, reason="Should fail, but doesn't")
def test_change_color_invalid(client):
    class InvalidColor:
        value = "#0077ff"

    client.changeThreadColor(InvalidColor())


@pytest.mark.parametrize("status", TypingStatus)
def test_typing_status(client, catch_event, compare, status):
    with catch_event("onTyping") as x:
        client.setTypingStatus(status)
    assert compare(x, status=status)


@pytest.mark.parametrize("require_admin_approval", [True, False])
def test_change_approval_mode(client1, group, catch_event, require_admin_approval):
    with catch_event("onApprovalModeChange") as x:
        client1.changeGroupApprovalMode(require_admin_approval, group["id"])

    assert subset(
        x.res,
        approval_mode=require_admin_approval,
        author_id=client1.uid,
        thread_id=group["id"],
    )


@pytest.mark.parametrize("mute_time", [0, 10, 100, 1000, -1])
def test_mute_thread(client, mute_time):
    assert client.muteThread(mute_time)
    assert client.unmuteThread()


def test_mute_thread_reactions(client):
    assert client.muteThreadReactions()
    assert client.unmuteThreadReactions()


def test_mute_thread_mentions(client):
    assert client.muteThreadMentions()
    assert client.unmuteThreadMentions()
