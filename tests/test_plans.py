# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import pytest

from fbchat.models import Plan, FBchatFacebookError, ThreadType
from utils import random_hex, subset
from time import time


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
    with catch_event("onPlanCreated") as x:
        client.createPlan(request.param, thread["id"])
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
    with catch_event("onPlanDeleted") as x:
        client.deletePlan(plan_id)
    assert compare(x)


@pytest.mark.tryfirst
def test_create_delete_plan(plan_data):
    pass


def test_fetch_plan_info(client, catch_event, plan_data):
    event, plan = plan_data
    fetched_plan = client.fetchPlanInfo(plan.uid)
    assert subset(
        vars(fetched_plan), time=plan.time, title=plan.title, author_id=int(client.uid)
    )


@pytest.mark.parametrize("take_part", [False, True])
def test_change_plan_participation(
    client, thread, catch_event, compare, plan_data, take_part
):
    event, plan = plan_data
    with catch_event("onPlanParticipation") as x:
        client.changePlanParticipation(plan, take_part=take_part)
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
    with catch_event("onPlanEdited") as x:
        client.editPlan(plan, new_plan)
    assert compare(x)
    assert subset(
        vars(x.res["plan"]),
        time=new_plan.time,
        title=new_plan.title,
        author_id=client.uid,
    )


@pytest.mark.trylast
@pytest.mark.expensive
def test_on_plan_ended(client, thread, catch_event, compare):
    with catch_event("onPlanEnded") as x:
        client.createPlan(Plan(int(time()) + 120, "Wait for ending"))
        x.wait(180)
    assert subset(
        x.res,
        thread_id=client.uid if thread["type"] == ThreadType.USER else thread["id"],
        thread_type=thread["type"],
    )


# createPlan(self, plan, thread_id=None)
# editPlan(self, plan, new_plan)
# deletePlan(self, plan)
# changePlanParticipation(self, plan, take_part=True)

# onPlanCreated(self, mid=None, plan=None, author_id=None, thread_id=None, thread_type=None, ts=None, metadata=None, msg=None)
# onPlanEnded(self, mid=None, plan=None, thread_id=None, thread_type=None, ts=None, metadata=None, msg=None)
# onPlanEdited(self, mid=None, plan=None, author_id=None, thread_id=None, thread_type=None, ts=None, metadata=None, msg=None)
# onPlanDeleted(self, mid=None, plan=None, author_id=None, thread_id=None, thread_type=None, ts=None, metadata=None, msg=None)
# onPlanParticipation(self, mid=None, plan=None, take_part=None, author_id=None, thread_id=None, thread_type=None, ts=None, metadata=None, msg=None)

# fetchPlanInfo(self, plan_id)
