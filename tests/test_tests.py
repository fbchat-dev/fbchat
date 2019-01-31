# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import pytest


def test_catch_event(client2, catch_event):
    mid = "test"
    with catch_event("onMessage") as x:
        client2.onMessage(mid=mid)
    assert x.res["mid"] == mid
