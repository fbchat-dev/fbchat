# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import threading
import logging
import six
import pytest

from os import environ
from random import randrange
from contextlib import contextmanager
from six import viewitems
from fbchat import Client
from fbchat.models import ThreadType, EmojiSize, FBchatFacebookError, Sticker

log = logging.getLogger("fbchat.tests").addHandler(logging.NullHandler())


EMOJI_LIST = [
    ("😆", EmojiSize.SMALL),
    ("😆", EmojiSize.MEDIUM),
    ("😆", EmojiSize.LARGE),
    # These fail in `catch_event` because the emoji is made into a sticker
    # This should be fixed
    pytest.param(None, EmojiSize.SMALL, marks=[pytest.mark.xfail()]),
    pytest.param(None, EmojiSize.MEDIUM, marks=[pytest.mark.xfail()]),
    pytest.param(None, EmojiSize.LARGE, marks=[pytest.mark.xfail()]),
]

STICKER_LIST = [
    Sticker("767334476626295"),
    pytest.param(Sticker("0"), marks=[pytest.mark.xfail(raises=FBchatFacebookError)]),
    pytest.param(Sticker(None), marks=[pytest.mark.xfail(raises=FBchatFacebookError)]),
]

TEXT_LIST = [
    "test_send",
    "😆",
    "\\\n\t%?&'\"",
    "ˁҭʚ¹Ʋջوװ՞ޱɣࠚԹБɑȑңКએ֭ʗыԈٌʼőԈ×௴nચϚࠖణٔє܅Ԇޑط",
    "a" * 20000,  # Maximum amount of characters you can send
    pytest.param("a" * 20001, marks=[pytest.mark.xfail(raises=FBchatFacebookError)]),
    pytest.param(None, marks=[pytest.mark.xfail(raises=FBchatFacebookError)]),
]


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
        user_agent="Mozilla/5.0 (Windows NT 6.3; WOW64; ; NCT50_AAP285C84A1328) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.90 Safari/537.36",
        session_cookies=cache.get("client{}_session".format(n), None),
        max_tries=1,
    )
    yield client
    cache.set("client{}_session".format(n), client.getSession())
