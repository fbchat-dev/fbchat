# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import pytest

from os import path
from fbchat.models import Message, Mention, EmojiSize, FBchatFacebookError, Sticker

from utils import set_default_client, threads


@pytest.fixture
def thread(thread):
    print("test")
    return thread


@pytest.mark.parametrize("thread", threads)
@pytest.mark.parametrize(
    "emoji, emoji_size",
    [
        ("😆", EmojiSize.SMALL),
        ("😆", EmojiSize.MEDIUM),
        ("😆", EmojiSize.LARGE),
        (None, EmojiSize.SMALL),
        (None, EmojiSize.MEDIUM),
        (None, EmojiSize.LARGE),
    ],
)
def test_send_emoji(client, thread, emoji, emoji_size):
    assert client.sendEmoji(emoji, emoji_size, thread["id"], thread["type"])


@pytest.mark.parametrize("thread", threads)
@pytest.mark.parametrize(
    "text",
    [
        "test_send",
        "😆",
        "\\\n\t%?&'\"",
        "ˁҭʚ¹Ʋջوװ՞ޱɣࠚԹБɑȑңКએ֭ʗыԈٌʼőԈ×௴nચϚࠖణٔє܅Ԇޑط",
        "a" * 20000,  # Maximum amount of messages you can send
    ],
)
def test_send_text(client, thread, text):
    assert client.sendMessage(text, thread["id"], thread["type"])


@pytest.mark.parametrize("thread", threads)
@pytest.mark.xfail(error=FBchatFacebookError)
def test_send_text(client, thread):
    # Send a message that is too long
    assert client.sendMessage("a" * 20001, thread["id"], thread["type"])


@pytest.mark.parametrize("thread", threads)
def test_send_mention(client, thread):
    assert client.send(
        Message("Hi there @me", mentions=[Mention(client.uid, offset=9, length=3)]),
        thread["id"],
        thread["type"],
    )


@pytest.mark.requires_two_clients
@pytest.mark.parametrize("thread", threads)
def test_send_mentions(client1, client2, thread):
    assert client1.send(
        Message(
            "Hi there @me, @other and @thread",
            mentions=[
                Mention(client1.uid, offset=9, length=3),
                Mention(client2.uid, offset=14, length=6),
                Mention(thread["id"], offset=26, length=7),
            ],
        ),
        thread["id"],
        thread["type"],
    )


@pytest.mark.parametrize("thread", threads)
@pytest.mark.parametrize("sticker_id", ["767334476626295"])
def test_send(client, thread, sticker_id):
    assert client.send(
        Message(sticker=Sticker(sticker_id)), thread["id"], thread["type"]
    )


@pytest.mark.parametrize("thread", threads)
def test_send_remote_images(client, thread):
    assert client.sendRemoteImage(
        "https://github.com/carpedm20/fbchat/raw/master/tests/image.png",
        Message("A remote image"),
        thread["id"],
        thread["type"],
    )


@pytest.mark.parametrize("thread", threads)
def test_send_local_images(client, thread):
    assert client.sendLocalImage(
        path.join(path.dirname(__file__), "image.png"),
        Message("A local image"),
        thread["id"],
        thread["type"],
    )
