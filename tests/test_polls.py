import pytest

from fbchat import Poll, PollOption, ThreadType
from utils import random_hex, subset

pytestmark = pytest.mark.online


@pytest.fixture(
    scope="module",
    params=[
        Poll(title=random_hex(), options=[]),
        Poll(
            title=random_hex(),
            options=[
                PollOption(random_hex(), vote=True),
                PollOption(random_hex(), vote=True),
            ],
        ),
        Poll(
            title=random_hex(),
            options=[
                PollOption(random_hex(), vote=False),
                PollOption(random_hex(), vote=False),
            ],
        ),
        Poll(
            title=random_hex(),
            options=[
                PollOption(random_hex(), vote=True),
                PollOption(random_hex(), vote=True),
                PollOption(random_hex(), vote=False),
                PollOption(random_hex(), vote=False),
                PollOption(random_hex()),
                PollOption(random_hex()),
            ],
        ),
        pytest.param(
            Poll(title=None, options=[]), marks=[pytest.mark.xfail(raises=ValueError)]
        ),
    ],
)
def poll_data(request, client1, group, catch_event):
    with catch_event("on_poll_created") as x:
        client1.create_poll(request.param, thread_id=group["id"])
    options = client1.fetch_poll_options(x.res["poll"].uid)
    return x.res, request.param, options


def test_create_poll(client1, group, catch_event, poll_data):
    event, poll, _ = poll_data
    assert subset(
        event,
        author_id=client1.uid,
        thread_id=group["id"],
        thread_type=ThreadType.GROUP,
    )
    assert subset(
        vars(event["poll"]), title=poll.title, options_count=len(poll.options)
    )
    for recv_option in event[
        "poll"
    ].options:  # The recieved options may not be the full list
        old_option, = list(filter(lambda o: o.text == recv_option.text, poll.options))
        voters = [client1.uid] if old_option.vote else []
        assert subset(
            vars(recv_option), voters=voters, votes_count=len(voters), vote=False
        )


def test_fetch_poll_options(client1, group, catch_event, poll_data):
    _, poll, options = poll_data
    assert len(options) == len(poll.options)
    for option in options:
        assert subset(vars(option))


@pytest.mark.trylast
def test_update_poll_vote(client1, group, catch_event, poll_data):
    event, poll, options = poll_data
    new_vote_ids = [o.uid for o in options[0 : len(options) : 2] if not o.vote]
    re_vote_ids = [o.uid for o in options[0 : len(options) : 2] if o.vote]
    new_options = [random_hex(), random_hex()]
    with catch_event("on_poll_voted") as x:
        client1.update_poll_vote(
            event["poll"].uid,
            option_ids=new_vote_ids + re_vote_ids,
            new_options=new_options,
        )

    assert subset(
        x.res,
        author_id=client1.uid,
        thread_id=group["id"],
        thread_type=ThreadType.GROUP,
    )
    assert subset(
        vars(x.res["poll"]), title=poll.title, options_count=len(options + new_options)
    )
    for o in new_vote_ids:
        assert o in x.res["added_options"]
    assert len(x.res["added_options"]) == len(new_vote_ids) + len(new_options)
    assert set(x.res["removed_options"]) == set(
        o.uid for o in options if o.vote and o.uid not in re_vote_ids
    )
