# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from os import environ
from contextlib import contextmanager
from threading import Thread, Event
from pytest import fixture, skip
from fbchat import Group, Client


'''
@fixture
def mocker(mocker):
    def autospec_as_default(*args, **kwargs):
        kwargs.setdefault('autospec', True)
        return mocker.patch.__class__._start_patch(mocker, *args, **kwargs)

    mocker.patch.object(mocker.patch, '_start_patch', side_effect=autospec_as_default)
    return mocker
'''


def load_variable(name, cache):
    var = environ.get(name, None)
    if var is not None:
        if cache.get(name, None) != var:
            cache.set(name, var)
        return var

    var = cache.get(name, None)
    if var is None:
        raise ValueError("Variable {!r} neither in environment nor cache".format(name))
    return var


@fixture(scope="session")
def group(pytestconfig):
    return Group(load_variable("group_id", pytestconfig.cache))


@contextmanager
def load_client(n, cache):
    email = load_variable("client{}_email".format(n), cache)
    password = load_variable("client{}_password".format(n), cache)
    session = cache.get("client{}_session".format(n), None)
    if email is None or password is None:
        skip("No client data was supplied")
    client = Client(email, password, session=session)
    yield client
    cache.set("client{}_session".format(n), client.get_session())


@fixture(scope="session")
def client(pytestconfig):
    with load_client(1, pytestconfig.cache) as c:
        yield c


@fixture(scope="session")
def listener_client(pytestconfig):
    with load_client(2, pytestconfig.cache) as c:
        t = Thread(target=c.listen)
        t.start()
        yield c
        c.stop_listen()
        # Make the client send a messages to itself, so the blocking request will return
        # This might not be safe, since the client is making two requests simultaneously
        try:
            c.send_text(c, "Shutdown")
        finally:
            t.join()


@fixture(scope="session")
def user(listener_client):
    return listener_client # Client subclasses User, so this is valid


@fixture(params=["user", "group"])
def thread(request, user, group):
    return user if request.param == "user" else group


@fixture(params=["client", "listener_client"])
def a_client(thread, client, listener_client):
    return client if request.param == "client" else listener_client


@fixture
def listener(mocker, listener_client):
    @contextmanager
    def inner(method_name, **kwargs):
        e = Event()
        kwargs['side_effect'] = e.set
        mocked = mocker.patch.object(listener_client, method_name, **kwargs)
        yield mocked
        e.wait(timeout=3)
        mocked.stopall()
    return inner
