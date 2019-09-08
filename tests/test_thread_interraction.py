import pytest

from fbchat import Message, ThreadType, FBchatFacebookError, TypingStatus, ThreadColor
from utils import random_hex, subset
from os import path

pytestmark = pytest.mark.online


def test_remove_from_and_add_to_group(client1, client2, group, catch_event):
    # Test both methods, while ensuring that the user gets added to the group
    try:
        with catch_event("on_person_removed") as x:
            client1.remove_user_from_group(client2.uid, group["id"])
        assert subset(
            x.res, removed_id=client2.uid, author_id=client1.uid, thread_id=group["id"]
        )
    finally:
        with catch_event("on_people_added") as x:
            client1.add_users_to_group(client2.uid, group["id"])
        assert subset(
            x.res, added_ids=[client2.uid], author_id=client1.uid, thread_id=group["id"]
        )


def test_remove_from_and_add_admins_to_group(client1, client2, group, catch_event):
    # Test both methods, while ensuring that the user gets added as group admin
    try:
        with catch_event("on_admin_removed") as x:
            client1.remove_group_admins(client2.uid, group["id"])
        assert subset(
            x.res, removed_id=client2.uid, author_id=client1.uid, thread_id=group["id"]
        )
    finally:
        with catch_event("on_admin_added") as x:
            client1.add_group_admins(client2.uid, group["id"])
        assert subset(
            x.res, added_id=client2.uid, author_id=client1.uid, thread_id=group["id"]
        )


def test_change_title(client1, group, catch_event):
    title = random_hex()
    with catch_event("on_title_change") as x:
        client1.change_thread_title(title, group["id"], thread_type=ThreadType.GROUP)
    assert subset(
        x.res,
        author_id=client1.uid,
        new_title=title,
        thread_id=group["id"],
        thread_type=ThreadType.GROUP,
    )


def test_change_nickname(client, client_all, catch_event, compare):
    nickname = random_hex()
    with catch_event("on_nickname_change") as x:
        client.change_nickname(nickname, client_all.uid)
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
    with catch_event("on_emoji_change") as x:
        client.change_thread_emoji(emoji)
    assert compare(x, new_emoji=emoji)


def test_change_image_local(client1, group, catch_event):
    url = path.join(path.dirname(__file__), "resources", "image.png")
    with catch_event("on_image_change") as x:
        image_id = client1.change_group_image_local(url, group["id"])
    assert subset(
        x.res, new_image=image_id, author_id=client1.uid, thread_id=group["id"]
    )


# To be changed when merged into master
def test_change_image_remote(client1, group, catch_event):
    url = "https://github.com/carpedm20/fbchat/raw/master/tests/image.png"
    with catch_event("on_image_change") as x:
        image_id = client1.change_group_image_remote(url, group["id"])
    assert subset(
        x.res, new_image=image_id, author_id=client1.uid, thread_id=group["id"]
    )


@pytest.mark.parametrize(
    "color",
    [x for x in ThreadColor if x in [ThreadColor.MESSENGER_BLUE, ThreadColor.PUMPKIN]],
)
def test_change_color(client, catch_event, compare, color):
    with catch_event("on_color_change") as x:
        client.change_thread_color(color)
    assert compare(x, new_color=color)


@pytest.mark.xfail(raises=FBchatFacebookError, reason="Should fail, but doesn't")
def test_change_color_invalid(client):
    class InvalidColor:
        value = "#0077ff"

    client.change_thread_color(InvalidColor())


@pytest.mark.parametrize("status", TypingStatus)
def test_typing_status(client, catch_event, compare, status):
    with catch_event("on_typing") as x:
        client.set_typing_status(status)
    assert compare(x, status=status)


@pytest.mark.parametrize("require_admin_approval", [True, False])
def test_change_approval_mode(client1, group, catch_event, require_admin_approval):
    with catch_event("on_approval_mode_change") as x:
        client1.change_group_approval_mode(require_admin_approval, group["id"])

    assert subset(
        x.res,
        approval_mode=require_admin_approval,
        author_id=client1.uid,
        thread_id=group["id"],
    )


@pytest.mark.parametrize("mute_time", [0, 10, 100, 1000, -1])
def test_mute_thread(client, mute_time):
    assert client.mute_thread(mute_time)
    assert client.unmute_thread()


def test_mute_thread_reactions(client):
    assert client.mute_thread_reactions()
    assert client.unmute_thread_reactions()


def test_mute_thread_mentions(client):
    assert client.mute_thread_mentions()
    assert client.unmute_thread_mentions()
