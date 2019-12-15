# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import pytest

from os import path
from fbchat.models import ThreadType, Message, Mention, EmojiSize, Sticker
from utils import subset, STICKER_LIST, EMOJI_LIST


def test_fetch_all_users(client1):
    users = client1.fetchAllUsers()
    assert len(users) > 0


def test_fetch_thread_list(client1):
    threads = client1.fetchThreadList(limit=2)
    assert len(threads) == 2


def test_fetch_threads(client1):
    threads = client1.fetchThreads(limit=2)
    assert len(threads) == 2


@pytest.mark.parametrize("emoji, emoji_size", EMOJI_LIST)
def test_fetch_message_emoji(client, emoji, emoji_size):
    mid = client.sendEmoji(emoji, emoji_size)
    (message,) = client.fetchThreadMessages(limit=1)

    assert subset(
        vars(message), uid=mid, author=client.uid, text=emoji, emoji_size=emoji_size
    )


@pytest.mark.parametrize("emoji, emoji_size", EMOJI_LIST)
def test_fetch_message_info_emoji(client, thread, emoji, emoji_size):
    mid = client.sendEmoji(emoji, emoji_size)
    message = client.fetchMessageInfo(mid, thread_id=thread["id"])

    assert subset(
        vars(message), uid=mid, author=client.uid, text=emoji, emoji_size=emoji_size
    )


def test_fetch_message_mentions(client, thread, message_with_mentions):
    mid = client.send(message_with_mentions)
    (message,) = client.fetchThreadMessages(limit=1)

    assert subset(
        vars(message), uid=mid, author=client.uid, text=message_with_mentions.text
    )
    # The mentions are not ordered by offset
    for m in message.mentions:
        assert vars(m) in [vars(x) for x in message_with_mentions.mentions]


def test_fetch_message_info_mentions(client, thread, message_with_mentions):
    mid = client.send(message_with_mentions)
    message = client.fetchMessageInfo(mid, thread_id=thread["id"])

    assert subset(
        vars(message), uid=mid, author=client.uid, text=message_with_mentions.text
    )
    # The mentions are not ordered by offset
    for m in message.mentions:
        assert vars(m) in [vars(x) for x in message_with_mentions.mentions]


@pytest.mark.parametrize("sticker", STICKER_LIST)
def test_fetch_message_sticker(client, sticker):
    mid = client.send(Message(sticker=sticker))
    (message,) = client.fetchThreadMessages(limit=1)

    assert subset(vars(message), uid=mid, author=client.uid)
    assert subset(vars(message.sticker), uid=sticker.uid)


@pytest.mark.parametrize("sticker", STICKER_LIST)
def test_fetch_message_info_sticker(client, thread, sticker):
    mid = client.send(Message(sticker=sticker))
    message = client.fetchMessageInfo(mid, thread_id=thread["id"])

    assert subset(vars(message), uid=mid, author=client.uid)
    assert subset(vars(message.sticker), uid=sticker.uid)


def test_fetch_info(client1, group):
    info = client1.fetchUserInfo("4")["4"]
    assert info.name == "Mark Zuckerberg"

    info = client1.fetchGroupInfo(group["id"])[group["id"]]
    assert info.type == ThreadType.GROUP


def test_fetch_image_url(client):
    client.sendLocalFiles([path.join(path.dirname(__file__), "resources", "image.png")])
    (message,) = client.fetchThreadMessages(limit=1)

    assert client.fetchImageUrl(message.attachments[0].uid)
