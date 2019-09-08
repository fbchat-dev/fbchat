import pytest

from fbchat import Plan, FBchatFacebookError, ThreadType
from utils import random_hex, subset
from time import time

pytestmark = pytest.mark.online


@pytest.fixture(
    scope="module",
    params=[
        Plan(int(time()) + 100, random_hex()),
        pytest.param(
            Plan(int(time()), random_hex()),
            marks=[pytest.mark.xfail(raises=FBchatFacebookError)],
        ),
        pytest.param(Plan(0, None), marks=[pytest.mark.xfail()]),
    ],
)
def plan_data(request, client, user, thread, catch_event, compare):
    with catch_event("on_plan_created") as x:
        client.create_plan(request.param, thread["id"])
    assert compare(x)
    assert subset(
        vars(x.res["plan"]),
        time=request.param.time,
        title=request.param.title,
        author_id=client.uid,
        going=[client.uid],
        declined=[],
    )
    plan_id = x.res["plan"]
    assert user["id"] in x.res["plan"].invited
    request.param.uid = x.res["plan"].uid
    yield x.res, request.param
    with catch_event("on_plan_deleted") as x:
        client.delete_plan(plan_id)
    assert compare(x)


@pytest.mark.tryfirst
def test_create_delete_plan(plan_data):
    pass


def test_fetch_plan_info(client, catch_event, plan_data):
    event, plan = plan_data
    fetched_plan = client.fetch_plan_info(plan.uid)
    assert subset(
        vars(fetched_plan), time=plan.time, title=plan.title, author_id=int(client.uid)
    )


@pytest.mark.parametrize("take_part", [False, True])
def test_change_plan_participation(
    client, thread, catch_event, compare, plan_data, take_part
):
    event, plan = plan_data
    with catch_event("on_plan_participation") as x:
        client.change_plan_participation(plan, take_part=take_part)
    assert compare(x, take_part=take_part)
    assert subset(
        vars(x.res["plan"]),
        time=plan.time,
        title=plan.title,
        author_id=client.uid,
        going=[client.uid] if take_part else [],
        declined=[client.uid] if not take_part else [],
    )


@pytest.mark.trylast
def test_edit_plan(client, thread, catch_event, compare, plan_data):
    event, plan = plan_data
    new_plan = Plan(plan.time + 100, random_hex())
    with catch_event("on_plan_edited") as x:
        client.edit_plan(plan, new_plan)
    assert compare(x)
    assert subset(
        vars(x.res["plan"]),
        time=new_plan.time,
        title=new_plan.title,
        author_id=client.uid,
    )


@pytest.mark.trylast
@pytest.mark.skip
def test_on_plan_ended(client, thread, catch_event, compare):
    with catch_event("on_plan_ended") as x:
        client.create_plan(Plan(int(time()) + 120, "Wait for ending"))
        x.wait(180)
    assert subset(
        x.res,
        thread_id=client.uid if thread["type"] == ThreadType.USER else thread["id"],
        thread_type=thread["type"],
    )


# create_plan(self, plan, thread_id=None)
# edit_plan(self, plan, new_plan)
# delete_plan(self, plan)
# change_plan_participation(self, plan, take_part=True)

# on_plan_created(self, mid=None, plan=None, author_id=None, thread_id=None, thread_type=None, ts=None, metadata=None, msg=None)
# on_plan_ended(self, mid=None, plan=None, thread_id=None, thread_type=None, ts=None, metadata=None, msg=None)
# on_plan_edited(self, mid=None, plan=None, author_id=None, thread_id=None, thread_type=None, ts=None, metadata=None, msg=None)
# on_plan_deleted(self, mid=None, plan=None, author_id=None, thread_id=None, thread_type=None, ts=None, metadata=None, msg=None)
# on_plan_participation(self, mid=None, plan=None, take_part=None, author_id=None, thread_id=None, thread_type=None, ts=None, metadata=None, msg=None)

# fetch_plan_info(self, plan_id)
