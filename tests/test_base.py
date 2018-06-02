# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import pytest
import py_compile

from glob import glob
from os import path
from fbchat import Client
from fbchat.models import FBchatFacebookError, Message
from utils import threads


def test_examples():
    # Compiles the examples, to check for syntax errors
    for name in glob(path.join(path.dirname(__file__), "../examples", "*.py")):
        py_compile.compile(name)


@pytest.mark.skip("Logging in multiple times in a row might disable the accounts")
def test_login(client):
    assert client.isLoggedIn()

    client.logout()

    assert not client.isLoggedIn()

    with pytest.raises(FBchatFacebookError):
        client.login("<invalid email>", "<invalid password>", max_tries=1)

    client.login(client.email, client.password)

    assert client.isLoggedIn()


def test_sessions(client):
    session = client.getSession()
    Client("no email needed", "no password needed", session_cookies=session)
    client.setSession(session)
    assert client.isLoggedIn()


@pytest.mark.parametrize("thread", threads)
def test_default_thread(client, thread):
    client.setDefaultThread(thread["id"], thread["type"])
    assert client.send(Message(text="Sent to the specified thread"))

    client.resetDefaultThread()
    with pytest.raises(ValueError):
        client.send(Message(text="Should not be sent"))
