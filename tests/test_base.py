# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import py_compile

from glob import glob
from os import path, environ
from pytest import mark
from fbchat import Client, FacebookError


def test_examples():
    # Compiles the examples, to check for syntax errors
    for name in glob(path.join(path.dirname(__file__), "../examples", "*.py")):
        py_compile.compile(name)


@mark.tryfirst
def test_init(client, listener_client):
    assert client.is_logged_in()
    assert listener_client.is_logged_in()


@mark.parametrize('email, password', [
    mark.xfail(('<email>', '<password>'), raises=FacebookError),
    mark.xfail((None, '<password>'), raises=ValueError),
    mark.xfail(('<email>', None), raises=ValueError),
    mark.xfail((None, None), raises=ValueError),
])
def test_init_invalid(email, password):
    Client(email, password)


def test_init_session(mocker, client):
    _login = mocker.patch.object(Client, '_login')
    session = client.get_session()
    c = Client("<email>", "<password>", session=session)
    _login.assert_not_called()
    assert c.is_logged_in()


@mark.parametrize('max_tries', [
    mark.xfail(None, raises=ValueError),
    mark.xfail(-1, raises=ValueError),
    mark.xfail(0, raises=ValueError),
    1,
    5,
    10,
])
def test_init_max_tries(mocker, max_tries):
    _login = mocker.patch.object(Client, '_login')
    c = Client("<email>", "<password>", max_tries=max_tries)
    assert _login.calls_count == max_tries
    assert _login.mock_calls == [mocker.call("<email>", "<password>")] * max_tries


'''
@mark.parametrize('user_agent', [0, None, 5, 10])
def test_init_user_agent(mocker, user_agent):
    mocker.patch.object(Client._login)
    c = Client('email', 'password', user_agent=user_agent)
    assert c.s.user_agent == user_agent
'''


def test_session(client):
    session = client.get_session()
    client.set_session(session)
    assert client.is_logged_in()


@mark.trylast
@mark.expensive
def test_logout(client):
    assert client.is_logged_in()

    client.logout()

    assert not client.is_logged_in()
