import pytest

from os import path
from fbchat import ThreadType, Message, Mention, EmojiSize, Sticker
from utils import subset, STICKER_LIST, EMOJI_LIST

pytestmark = pytest.mark.online


def test_fetch_all_users(client1):
    users = client1.fetch_all_users()
    assert len(users) > 0


def test_fetch_thread_list(client1):
    threads = client1.fetch_thread_list(limit=2)
    assert len(threads) == 2


def test_fetch_threads(client1):
    threads = client1.fetch_threads(limit=2)
    assert len(threads) == 2


@pytest.mark.parametrize("emoji, emoji_size", EMOJI_LIST)
def test_fetch_message_emoji(client, emoji, emoji_size):
    mid = client.send_emoji(emoji, emoji_size)
    message, = client.fetch_thread_messages(limit=1)

    assert subset(
        vars(message), uid=mid, author=client.uid, text=emoji, emoji_size=emoji_size
    )


@pytest.mark.parametrize("emoji, emoji_size", EMOJI_LIST)
def test_fetch_message_info_emoji(client, thread, emoji, emoji_size):
    mid = client.send_emoji(emoji, emoji_size)
    message = client.fetch_message_info(mid, thread_id=thread["id"])

    assert subset(
        vars(message), uid=mid, author=client.uid, text=emoji, emoji_size=emoji_size
    )


def test_fetch_message_mentions(client, thread, message_with_mentions):
    mid = client.send(message_with_mentions)
    message, = client.fetch_thread_messages(limit=1)

    assert subset(
        vars(message), uid=mid, author=client.uid, text=message_with_mentions.text
    )
    # The mentions are not ordered by offset
    for m in message.mentions:
        assert vars(m) in [vars(x) for x in message_with_mentions.mentions]


def test_fetch_message_info_mentions(client, thread, message_with_mentions):
    mid = client.send(message_with_mentions)
    message = client.fetch_message_info(mid, thread_id=thread["id"])

    assert subset(
        vars(message), uid=mid, author=client.uid, text=message_with_mentions.text
    )
    # The mentions are not ordered by offset
    for m in message.mentions:
        assert vars(m) in [vars(x) for x in message_with_mentions.mentions]


@pytest.mark.parametrize("sticker", STICKER_LIST)
def test_fetch_message_sticker(client, sticker):
    mid = client.send(Message(sticker=sticker))
    message, = client.fetch_thread_messages(limit=1)

    assert subset(vars(message), uid=mid, author=client.uid)
    assert subset(vars(message.sticker), uid=sticker.uid)


@pytest.mark.parametrize("sticker", STICKER_LIST)
def test_fetch_message_info_sticker(client, thread, sticker):
    mid = client.send(Message(sticker=sticker))
    message = client.fetch_message_info(mid, thread_id=thread["id"])

    assert subset(vars(message), uid=mid, author=client.uid)
    assert subset(vars(message.sticker), uid=sticker.uid)


def test_fetch_info(client1, group):
    info = client1.fetch_user_info("4")["4"]
    assert info.name == "Mark Zuckerberg"

    info = client1.fetch_group_info(group["id"])[group["id"]]
    assert info.type == ThreadType.GROUP


def test_fetch_image_url(client):
    client.send_local_files(
        [path.join(path.dirname(__file__), "resources", "image.png")]
    )
    message, = client.fetch_thread_messages(limit=1)

    assert client.fetch_image_url(message.attachments[0].uid)
