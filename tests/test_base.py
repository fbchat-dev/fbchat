# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import pytest
import py_compile

from glob import glob
from os import path, environ
from fbchat import Client
from fbchat.models import FBchatUserError, Message


@pytest.mark.offline
def test_examples():
    # Compiles the examples, to check for syntax errors
    for name in glob(path.join(path.dirname(__file__), "../examples", "*.py")):
        py_compile.compile(name)


@pytest.mark.trylast
@pytest.mark.expensive
def test_login(client1):
    assert client1.isLoggedIn()
    email = client1.email
    password = client1.password

    client1.logout()

    assert not client1.isLoggedIn()

    with pytest.raises(FBchatUserError):
        client1.login("<invalid email>", "<invalid password>", max_tries=1)

    client1.login(email, password)

    assert client1.isLoggedIn()


@pytest.mark.trylast
def test_sessions(client1):
    session = client1.getSession()
    Client("no email needed", "no password needed", session_cookies=session)
    client1.setSession(session)
    assert client1.isLoggedIn()


@pytest.mark.tryfirst
def test_default_thread(client1, thread):
    client1.setDefaultThread(thread["id"], thread["type"])
    assert client1.send(Message(text="Sent to the specified thread"))

    client1.resetDefaultThread()
    with pytest.raises(ValueError):
        client1.send(Message(text="Should not be sent"))
