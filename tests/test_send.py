# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from os import path
from pytest import mark
from fbchat.models import Client, Message, Mention, Size, FacebookError, Sticker


'''
@fixture
def client(mocker, client, thread):
    send = mocker.spy(client, 'send')
    yield client
    assert send.return_value == *client.fetch_messages(thread, limit=1)
    assert send.return_value == *client.get_messages(thread, limit=1)
'''


@mark.parametrize("text", [
    "test_send",
    "😆",
    "\\\n\t%?&'\"",
    "ˁҭʚ¹Ʋջوװ՞ޱɣࠚԹБɑȑңКએ֭ʗыԈٌʼőԈ×௴nચϚࠖణٔє܅Ԇޑط",
    "a" * 20000,
    mark.xfail("a" * 20001, raises=FacebookError, reason="You can only send a maximum of 20000 characters")
])
def test_send_text(listener, client, thread, text):
    with listener('on_text') as on_text:
        client.send_text(thread, text)
    on_text.assert_called_once_with(thread, client, text)


def test_send_mentions(listener, client, listener_client, thread):
    text = "Hi there @me, @other and @thread"
    mentions = [
        Mention(thread=client, offset=9, length=3),
        Mention(thread=listener_client, offset=14, length=6),
        Mention(thread=thread, offset=26, length=7),
    ]
    with listener('on_text') as on_text:
        client.send_text(thread, text, mentions=mentions)
    on_text.assert_called_once_with(thread, client, text, mentions)


@mark.parametrize("sticker", [
    Sticker("767334476626295"),
    mark.xfail(Sticker("0"), raises=FacebookError)
])
def test_send_sticker(listener, client, thread, sticker):
    with listener('on_sticker') as on_sticker:
        client.send_sticker(thread, sticker)
    on_sticker.assert_called_once_with(thread, client, sticker)


@mark.parametrize("emoji, size", [
    ("😆", Size.SMALL),
    ("😆", Size.MEDIUM),
    ("😆", Size.LARGE),
    (None, Size.SMALL),
    (None, Size.MEDIUM),
    (None, Size.LARGE),
])
def test_send_emoji(listener, client, thread, emoji, size):
    with listener('on_emoji') as on_emoji:
        client.send_emoji(thread, emoji, size)
    on_emoji.assert_called_once_with(thread, client, emoji, size)


@mark.parametrize("file", [
    path.join(path.dirname(__file__), "image.png"),
])
def test_send_file(listener, client, thread, file):
    with listener('on_file') as on_file:
        client.send_file(thread, file)
    on_file.assert_called_once_with(thread, author, 'the file')
