# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import pytest
import json
import fbchat
import utils

from os import environ


def load_variable(name, cache):
    var = cache.get(name, None)
    if var is None:
        var = environ.get(name, None)
        cache.set(name, var)
    return var


@pytest.fixture(scope="session")
def client(client1):
    return client1


@pytest.fixture(scope="session")
def client1(request):
    email = load_variable("client1_email", request.config.cache)
    password = load_variable("client1_password", request.config.cache)
    client = fbchat.Client(
        email,
        password,
        session_cookies=request.config.cache.get("client1_session", None),
    )
    yield client
    request.config.cache.set("client1_session", client.getSession())


@pytest.fixture(scope="session")
def client2(request):
    email = load_variable("client2_email", request.config.cache)
    password = load_variable("client2_password", request.config.cache)
    client = fbchat.Client(
        email,
        password,
        session_cookies=request.config.cache.get("client2_session", None),
    )
    yield client
    request.config.cache.set("client2_session", client.getSession())


"""
@pytest.fixture(scope='session')
def client3(request):
    email = load_variable('client3_email', request.config.cache)
    password = load_variable('client3_password', request.config.cache)
    client = fbchat.Client(email, password, session_cookies=request.config.cache.get('client3_session', None))
    yield client
    request.config.cache.set('client3_session', client.getSession())
"""
