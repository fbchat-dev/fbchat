# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import pytest

from os import path
from fbchat.models import ThreadType, Message, Mention, EmojiSize, Sticker
from utils import subset, STICKER_LIST, EMOJI_LIST


def test_fetch_all_users(client):
    users = client.fetchAllUsers()
    assert len(users) > 0


def test_fetch_thread_list(client):
    threads = client.fetchThreadList(limit=2)
    assert len(threads) == 2


@pytest.mark.parametrize("emoji, emoji_size", EMOJI_LIST)
def test_fetch_message_emoji(client, emoji, emoji_size):
    mid = client.sendEmoji(emoji, emoji_size)
    message, = client.fetchThreadMessages(limit=1)

    assert subset(
        vars(message), uid=mid, author=client.uid, text=emoji, emoji_size=emoji_size
    )


def test_fetch_message_mentions(client):
    text = "This is a test of fetchThreadMessages"
    mentions = [Mention(client.uid, offset=10, length=4)]

    mid = client.send(Message(text, mentions=mentions))
    message, = client.fetchThreadMessages(limit=1)

    assert subset(vars(message), uid=mid, author=client.uid, text=text)
    for i, m in enumerate(mentions):
        assert vars(message.mentions[i]) == vars(m)


@pytest.mark.parametrize("sticker", STICKER_LIST)
def test_fetch_message_sticker(client, sticker):
    mid = client.send(Message(sticker=sticker))
    message, = client.fetchThreadMessages(limit=1)

    assert subset(vars(message), uid=mid, author=client.uid)
    assert subset(vars(message.sticker), uid=sticker.uid)


def test_fetch_info(client1, group):
    info = client1.fetchUserInfo("4")["4"]
    assert info.name == "Mark Zuckerberg"

    info = client1.fetchGroupInfo(group["id"])[group["id"]]
    assert info.type == ThreadType.GROUP


def test_fetch_image_url(client):
    url = path.join(path.dirname(__file__), "image.png")

    client.sendLocalImage(url)
    message, = client.fetchThreadMessages(limit=1)

    assert client.fetchImageUrl(message.attachments[0].uid)
