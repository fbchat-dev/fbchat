# -*- coding: utf-8 -*-

from __future__ import unicode_literals


def test_search_for(client):
    users = client.searchForUsers("Mark Zuckerberg")
    assert len(users) > 0

    u = users[0]

    assert u.uid == "4"
    assert isinstance(u, User)
    assert u.photo[:4] == "http"
    assert u.url[:4] == "http"
    assert u.name == "Mark Zuckerberg"
