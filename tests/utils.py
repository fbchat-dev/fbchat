# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from contextlib import contextmanager
from fbchat.models import ThreadType

user = {"id": "100026538491708", "type": ThreadType.USER}
group = {"id": "1463789480385605", "type": ThreadType.GROUP}
threads = [user, group]


@contextmanager
def set_default_client(client, thread):
    client.setDefaultThread(thread["id"], thread["type"])
    yield client
    client.resetDefaultThread()


"""
@contextmanager
def catch_event(*clients, method_name='onMessage', attr_name='caught'):
    for c in clients:
        c.startListening()
        c.doOneListen()
        setattr(c, method_name, lambda **kwargs: setattr(c, attr_name, kwargs))
    yield
    for c in clients:
        while not hasattr(c, attr_name):
            c.doOneListen()
        c.stopListening()
"""
