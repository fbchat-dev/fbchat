# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import pytest

from os import path
from fbchat.models import FBchatFacebookError, Message, Mention
from utils import subset, STICKER_LIST, EMOJI_LIST, TEXT_LIST


@pytest.mark.parametrize("text", TEXT_LIST)
def test_send_text(client, catch_event, compare, text):
    with catch_event("onMessage") as x:
        mid = client.sendMessage(text)

    assert compare(x, mid=mid, message=text)
    assert subset(vars(x.res["message_object"]), uid=mid, author=client.uid, text=text)


@pytest.mark.parametrize("emoji, emoji_size", EMOJI_LIST)
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


@pytest.fixture
def message_with_mentions(client, client2, thread):
    text = "Hi there @me, @other and @thread"
    mentions = [
        dict(thread_id=client.uid, offset=9, length=3),
        dict(thread_id=client2.uid, offset=14, length=6),
        dict(thread_id=thread["id"], offset=26, length=7),
    ]
    return Message(text, mentions=[Mention(**d) for d in mentions])


def test_send_mentions(client, catch_event, compare, message_with_mentions):
    with catch_event("onMessage") as x:
        mid = client.send(message_with_mentions)

    assert compare(x, mid=mid, message=message_with_mentions.text)
    assert subset(vars(x.res["message_object"]), uid=mid, author=client.uid, text=message_with_mentions.text)
    # The mentions are not ordered by offset
    for m in x.res["message_object"].mentions:
        assert vars(m) in [vars(x) for x in message_with_mentions.mentions]


@pytest.mark.parametrize("sticker", STICKER_LIST)
def test_send_sticker(client, catch_event, compare, sticker):
    with catch_event("onMessage") as x:
        mid = client.send(Message(sticker=sticker))

    assert compare(x, mid=mid)
    assert subset(vars(x.res["message_object"]), uid=mid, author=client.uid)
    assert subset(vars(x.res["message_object"].sticker), uid=sticker.uid)


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
