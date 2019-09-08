import pytest


def test_catch_event(client2, catch_event):
    mid = "test"
    with catch_event("on_message") as x:
        client2.on_message(mid=mid)
    assert x.res["mid"] == mid
