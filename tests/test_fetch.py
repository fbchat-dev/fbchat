# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import pytest

from os import path
from fbchat.models import Group, Message, Mention, Size, Sticker


def test_fetch_all_users(client):
    users = client.fetchAllUsers()
    assert len(users) > 0


def test_fetch_thread_list(client):
    threads = client.fetchThreadList(limit=2)
    assert len(threads) == 2


def test_fetch_info(client, group):
    info = client.fetchUserInfo("4")["4"]
    assert info.name == "Mark Zuckerberg"

    info = client.fetchGroupInfo(group["id"])[group["id"]]
    assert isinstance(info, Group)


def test_fetch_image_url(client):
    url = path.join(path.dirname(__file__), "image.png")

    client.sendLocalImage(url)
    message, = client.fetchThreadMessages(limit=1)

    assert client.fetchImageUrl(message.attachments[0].uid)
