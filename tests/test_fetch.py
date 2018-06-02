# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import pytest

from os import path
from fbchat.models import ThreadType, Message
from utils import set_default_client, threads, group


def test_fetch_all_users(client):
    users = client.fetchAllUsers()
    assert len(users) > 0


def test_fetch_thread_list(client):
    threads = client.fetchThreadList(limit=2)
    assert len(threads) == 2


@pytest.mark.parametrize("thread", threads)
def test_fetch_thread_messages(client, thread):
    text = "This is a test of fetchThreadMessages"

    with set_default_client(client, thread):
        client.sendMessage(text)
        messages = client.fetchThreadMessages(limit=1)

    assert messages[0].author == client.uid
    assert messages[0].text == text


def test_fetch_info(client):
    info = client.fetchUserInfo("4")["4"]
    assert info.name == "Mark Zuckerberg"

    info = client.fetchGroupInfo(group["id"])[group["id"]]
    assert info.type == ThreadType.GROUP


@pytest.mark.parametrize("thread", threads)
def test_fetch_image_url(client, thread):
    url = path.join(path.dirname(__file__), "image.png")

    with set_default_client(client, thread):
        client.sendLocalImage(url)
        message, = client.fetchThreadMessages(limit=1)

    assert client.fetchImageUrl(message.attachments[0].uid)
