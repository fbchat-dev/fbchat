from fbchat._poll import Poll, PollOption


def test_poll_option_from_graphql_unvoted():
    data = {
        "id": "123456789",
        "text": "abc",
        "total_count": 0,
        "viewer_has_voted": "false",
        "voters": [],
    }
    assert PollOption(
        text="abc", vote=False, voters=[], votes_count=0, uid=123456789
    ) == PollOption._from_graphql(data)


def test_poll_option_from_graphql_voted():
    data = {
        "id": "123456789",
        "text": "abc",
        "total_count": 2,
        "viewer_has_voted": "true",
        "voters": ["1234", "2345"],
    }
    assert PollOption(
        text="abc", vote=True, voters=["1234", "2345"], votes_count=2, uid=123456789
    ) == PollOption._from_graphql(data)


def test_poll_option_from_graphql_alternate_format():
    # Format received when fetching poll options
    data = {
        "id": "123456789",
        "text": "abc",
        "viewer_has_voted": True,
        "voters": {
            "count": 2,
            "edges": [{"node": {"id": "1234"}}, {"node": {"id": "2345"}}],
        },
    }
    assert PollOption(
        text="abc", vote=True, voters=["1234", "2345"], votes_count=2, uid=123456789
    ) == PollOption._from_graphql(data)


def test_poll_from_graphql():
    data = {
        "id": "123456789",
        "text": "Some poll",
        "total_count": 5,
        "viewer_has_voted": "true",
        "options": [
            {
                "id": "1111",
                "text": "Abc",
                "total_count": 1,
                "viewer_has_voted": "true",
                "voters": ["1234"],
            },
            {
                "id": "2222",
                "text": "Def",
                "total_count": 2,
                "viewer_has_voted": "false",
                "voters": ["2345", "3456"],
            },
            {
                "id": "3333",
                "text": "Ghi",
                "total_count": 0,
                "viewer_has_voted": "false",
                "voters": [],
            },
        ],
    }
    assert Poll(
        title="Some poll",
        options=[
            PollOption(text="Abc", vote=True, voters=["1234"], votes_count=1, uid=1111),
            PollOption(
                text="Def", vote=False, voters=["2345", "3456"], votes_count=2, uid=2222
            ),
            PollOption(text="Ghi", vote=False, voters=[], votes_count=0, uid=3333),
        ],
        options_count=5,
        uid=123456789,
    ) == Poll._from_graphql(data)
