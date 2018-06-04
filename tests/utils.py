# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import threading
import logging
import six

from os import environ
from random import randrange
from contextlib import contextmanager
from six import viewitems
from fbchat import Client
from fbchat.models import ThreadType

log = logging.getLogger("fbchat.tests").addHandler(logging.NullHandler())


class ClientThread(threading.Thread):
    def __init__(self, client, *args, **kwargs):
        self.client = client
        self.should_stop = threading.Event()
        super(ClientThread, self).__init__(*args, **kwargs)

    def start(self):
        self.client.startListening()
        self.client.doOneListen()  # QPrimer, Facebook now knows we're about to start pulling
        super(ClientThread, self).start()

    def run(self):
        while not self.should_stop.is_set() and self.client.doOneListen():
            pass

        self.client.stopListening()


if six.PY2:
    event_class = threading._Event
else:
    event_class = threading.Event


class CaughtValue(event_class):
    def set(self, res):
        self.res = res
        super(CaughtValue, self).set()

    def wait(self, timeout=3):
        super(CaughtValue, self).wait(timeout=timeout)


def random_hex(length=20):
    return "{:X}".format(randrange(16 ** length))


def subset(a, **b):
    print(a)
    print(b)
    return viewitems(b) <= viewitems(a)


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


@contextmanager
def load_client(n, cache):
    client = Client(
        load_variable("client{}_email".format(n), cache),
        load_variable("client{}_password".format(n), cache),
        session_cookies=cache.get("client{}_session".format(n), None),
    )
    yield client
    cache.set("client{}_session".format(n), client.getSession())
