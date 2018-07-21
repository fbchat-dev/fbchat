# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from pytest import mark
from fbchat.models import Message, FacebookError, Colour


def random_hex(length=20):
    return "{:X}".format(randrange(16 ** length))


@mark.parametrize("image", [])
def test_set_image(listener, client, group, image):
    with listener('on_image_set') as on_image_set:
        client.set_image(group, image)
    on_image_set.assert_called_once_with(group, client, old_image)


def test_set_title(listener, client, group, title):
    client.set_title(group, None)
    title = random_hex()
    with listener('on_title_set') as on_title_set:
        client.set_title(group, title)
    on_title_set.assert_called_once_with(group, client, None)

    with listener('on_title_set') as on_title_set:
        client.set_title(group)
    on_title_set.assert_called_once_with(group, client, title)


def test_set_nickname(listener, client, thread, a_client, random_hex):
    client.set_nickname(thread, a_client, None)
    nickname = random_hex()

    with listener('on_nickname_set') as on_nickname_set:
        client.set_nickname(thread, a_client, nickname)
    on_nickname_set.assert_called_once_with(thread, client, a_client, None)

    with listener('on_nickname_set') as on_nickname_set:
        client.set_nickname(thread, a_client)
    on_nickname_set.assert_called_once_with(thread, client, a_client, nickname)


class FakeColour(object):
    def __init__(self, value):
        self.value = value

@mark.parametrize("colour", [
    mark.xfail(FakeColour("#0077ff"), raises=ValueError),
    mark.xfail("not a colour", raises=ValueError),
] + list(Colour))
def test_set_colour(listener, client, thread, colour):
    with listener('on_colour_set') as on_colour_set:
        client.set_colour(thread, colour)
    on_colour_set.assert_called_once_with(thread, client, old_colour)


@mark.parametrize("emoji", [
    mark.xfail("🙃", raises=FacebookError),
    mark.xfail("not an emoji", raises=ValueError),
    "😀",
    "😂",
    "😕",
    "😍",
])
def test_set_emoji(listener, client, thread, emoji):
    with listener('on_emoji_set') as on_emoji_set:
        client.set_emoji(thread, emoji)
    on_emoji_set.assert_called_once_with(thread, client, old_emoji)


'''
@mark.parametrize("status", TypingStatus)
def test_typing_status(client, catch_event, compare, status):
    with catch_event("onTyping") as x:
        client.setTypingStatus(status)
    assert compare(x, status=status)
'''
