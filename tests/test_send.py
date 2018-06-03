# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import pytest

from os import path
from fbchat.models import Message, Mention, EmojiSize, FBchatFacebookError, Sticker
from utils import subset


@pytest.mark.parametrize(
    "text",
    [
        "test_send",
        "😆",
        "\\\n\t%?&'\"",
        "ˁҭʚ¹Ʋջوװ՞ޱɣࠚԹБɑȑңКએ֭ʗыԈٌʼőԈ×௴nચϚࠖణٔє܅Ԇޑط",
        "a" * 20000,  # Maximum amount of characters you can send
    ],
)
def test_send_text(client, catch_event, compare, text):
    with catch_event("onMessage") as x:
        mid = client.sendMessage(text)

    assert compare(x, mid=mid, message=text)
    assert subset(vars(x.res["message_object"]), uid=mid, author=client.uid, text=text)


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
def test_send_emoji(client, catch_event, compare, emoji, emoji_size):
    with catch_event("onMessage") as x:
        mid = client.sendEmoji(emoji, emoji_size)

    assert compare(x, mid=mid, message=emoji)
    assert subset(
        vars(x.res["message_object"]),
        uid=mid,
        author=client.uid,
        text=emoji,
        emoji_size=emoji_size,
    )


@pytest.mark.xfail(error=FBchatFacebookError)
@pytest.mark.parametrize("message", [Message("a" * 20001)])
def test_send_invalid(client, message):
    client.send(message)


def test_send_mentions(client, client2, thread, catch_event, compare):
    text = "Hi there @me, @other and @thread"
    mentions = [
        Mention(client.uid, offset=9, length=3),
        Mention(client2.uid, offset=14, length=6),
        Mention(thread["id"], offset=26, length=7),
    ]
    with catch_event("onMessage") as x:
        mid = client.send(Message(text, mentions=mentions))

    assert compare(x, mid=mid, message=text)
    assert subset(vars(x.res["message_object"]), uid=mid, author=client.uid, text=text)
    for i, m in enumerate(mentions):
        assert vars(x.res["message_object"].mentions[i]) == vars(m)


@pytest.mark.parametrize(
    "sticker_id",
    ["767334476626295", pytest.mark.xfail("0", raises=FBchatFacebookError)],
)
def test_send_sticker(client, catch_event, compare, sticker_id):
    with catch_event("onMessage") as x:
        mid = client.send(Message(sticker=Sticker(sticker_id)))

    assert compare(x, mid=mid)
    assert subset(vars(x.res["message_object"]), uid=mid, author=client.uid)
    assert subset(vars(x.res["message_object"].sticker), uid=sticker_id)


@pytest.mark.parametrize(
    "method_name, url",
    [
        (
            "sendRemoteImage",
            "https://github.com/carpedm20/fbchat/raw/master/tests/image.png",
        ),
        ("sendLocalImage", path.join(path.dirname(__file__), "image.png")),
    ],
)
def test_send_images(client, catch_event, compare, method_name, url):
    text = "An image sent with {}".format(method_name)
    with catch_event("onMessage") as x:
        mid = getattr(client, method_name)(url, Message(text))

    assert compare(x, mid=mid, message=text)
    assert subset(vars(x.res["message_object"]), uid=mid, author=client.uid, text=text)
    assert x.res["message_object"].attachments[0]
