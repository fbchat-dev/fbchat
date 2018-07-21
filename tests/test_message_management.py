# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from pytest import mark, fixture
from fbchat.models import Message, Reaction


@fixture(scope='module')
def message(client):
    return client.send_text("This message will be reacted to")


@mark.parametrize("reaction", [
    mark.xfail("😀", raises=ValueError),
    mark.xfail("🎉", raises=ValueError),
    mark.xfail("not an emoji", raises=ValueError),
    None,
    "😍",
    "😆",
    "😮",
    "😢",
    "😠",
    "👍",
    "👎",
])
def test_set_reaction(listener, client, message, reaction):
    client.set_reaction(message, reaction)

    with listener('on_reaction_set') as on_reaction_set:
        client.set_reaction(message)
    on_reaction_set.assert_called_once_with(message, client, reaction)
