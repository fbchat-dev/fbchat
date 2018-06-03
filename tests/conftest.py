# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import pytest
import json

from utils import *
from contextlib import contextmanager
from fbchat.models import ThreadType


@pytest.fixture(scope="session")
def user(client2):
    return {"id": client2.uid, "type": ThreadType.USER}


@pytest.fixture(scope="session")
def group():
    return {"id": "1463789480385605", "type": ThreadType.GROUP}


@pytest.fixture(scope="session", params=["user", "group"])
def thread(request, user, group):
    return user if request.param == "user" else group


@pytest.fixture(scope="session")
def client1(pytestconfig):
    with load_client(1, pytestconfig.cache) as c:
        yield c


@pytest.fixture(scope="session")
def client2(pytestconfig):
    with load_client(2, pytestconfig.cache) as c:
        yield c


@pytest.fixture  # (scope="session")
def client(client1, thread):
    client1.setDefaultThread(thread["id"], thread["type"])
    yield client1
    client1.resetDefaultThread()


@pytest.fixture(scope="session", params=["client1", "client2"])
def client_all(request, client1, client2):
    return client1 if request.param == "client1" else client2


@pytest.fixture(scope="session")
def catch_event(client2):
    t = ClientThread(client2)
    t.start()

    @contextmanager
    def inner(method_name):
        caught = CaughtValue()
        old_method = getattr(client2, method_name)

        # Will be called by the other thread
        def catch_value(*args, **kwargs):
            old_method(*args, **kwargs)
            # Make sure the `set` is only called once
            if not caught.is_set():
                caught.set(kwargs)

        setattr(client2, method_name, catch_value)
        yield caught
        caught.wait()
        if not caught.is_set():
            raise ValueError("The value could not be caught")
        setattr(client2, method_name, old_method)

    yield inner

    t.should_stop.set()

    try:
        # Make the client send a messages to itself, so the blocking pull request will return
        # This is probably not safe, since the client is making two requests simultaneously
        client2.sendMessage("Shutdown", client2.uid)
    finally:
        t.join()


@pytest.fixture  # (scope="session")
def compare(client, thread):
    def inner(caught_event, **kwargs):
        d = {
            "author_id": client.uid,
            "thread_id": client.uid
            if thread["type"] == ThreadType.USER
            else thread["id"],
            "thread_type": thread["type"],
        }
        d.update(kwargs)
        return subset(caught_event.res, **d)

    return inner
