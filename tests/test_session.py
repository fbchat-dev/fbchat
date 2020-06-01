# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import brotli

from fbchat._session import Session, Response


class Expando(object):
    pass


def test_session_request_returns_local_response_type():
    r = Session().request('GET', "https://google.com")
    assert type(r) == Response


def test_response_behaves_normally_through___getattr__():
    r = Session().request('GET', "https://google.com")

    # not explicitely defined in Response class
    assert len(r.text) > 0


def test_response_converts_brotli_compression():
    fake_base_ressource = Expando()
    fake_base_ressource.content = brotli.compress(b'<html></html>')
    fake_base_ressource.headers = {
        'content-encoding': 'br'
    }
    r = Response(fake_base_ressource)
    assert r.content == b'<html></html>'
    assert r.content != brotli.compress(b'<html></html>')


def test_response_skips_unsupported_compression():
    fake_base_ressource = Expando()
    fake_base_ressource.content = brotli.compress(b'<html></html>')
    fake_base_ressource.headers = {
        'content-encoding': 'what-the-brot'
    }
    r = Response(fake_base_ressource)
    assert r.content == brotli.compress(b'<html></html>')
    assert r.content != b'<html></html>'
