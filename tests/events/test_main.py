import datetime
from fbchat import (
    _util,
    User,
    Group,
    Message,
    ParseError,
    UnknownEvent,
    Typing,
    FriendRequest,
    Presence,
    ReactionEvent,
    UnfetchedThreadEvent,
    ActiveStatus,
)
from fbchat._events import parse_events


def test_t_ms_full(session):
    """A full example of parsing of data in /t_ms."""
    payload = {
        "deltas": [
            {
                "deltaMessageReaction": {
                    "threadKey": {"threadFbId": 4321},
                    "messageId": "mid.$XYZ",
                    "action": 0,
                    "userId": 1234,
                    "reaction": "😢",
                    "senderId": 1234,
                    "offlineThreadingId": "1122334455",
                }
            }
        ]
    }
    data = {
        "deltas": [
            {
                "payload": [ord(x) for x in _util.json_minimal(payload)],
                "class": "ClientPayload",
            },
            {"class": "NoOp",},
            {
                "forceInsert": False,
                "messageId": "mid.$ABC",
                "threadKey": {"threadFbId": "4321"},
                "class": "ForcedFetch",
            },
        ],
        "firstDeltaSeqId": 111111,
        "lastIssuedSeqId": 111113,
        "queueEntityId": 1234,
    }
    thread = Group(session=session, id="4321")
    assert [
        ReactionEvent(
            author=User(session=session, id="1234"),
            thread=thread,
            message=Message(thread=thread, id="mid.$XYZ"),
            reaction="😢",
        ),
        UnfetchedThreadEvent(
            thread=thread, message=Message(thread=thread, id="mid.$ABC"),
        ),
    ] == list(parse_events(session, "/t_ms", data))


def test_thread_typing(session):
    data = {"sender_fbid": 1234, "state": 0, "type": "typ", "thread": "4321"}
    (event,) = parse_events(session, "/thread_typing", data)
    assert event == Typing(
        author=User(session=session, id="1234"),
        thread=Group(session=session, id="4321"),
        status=False,
    )


def test_orca_typing_notifications(session):
    data = {"type": "typ", "sender_fbid": 1234, "state": 1}
    (event,) = parse_events(session, "/orca_typing_notifications", data)
    assert event == Typing(
        author=User(session=session, id="1234"),
        thread=User(session=session, id="1234"),
        status=True,
    )


def test_friend_request(session):
    data = {"type": "jewel_requests_add", "from": "1234"}
    (event,) = parse_events(session, "/legacy_web", data)
    assert event == FriendRequest(author=User(session=session, id="1234"))


def test_orca_presence_inc(session):
    data = {
        "list_type": "inc",
        "list": [
            {"u": 1234, "p": 0, "l": 1500000000, "vc": 74},
            {"u": 2345, "p": 2, "c": 9969664, "vc": 10},
        ],
    }
    (event,) = parse_events(session, "/orca_presence", data)
    la = datetime.datetime(2017, 7, 14, 2, 40, tzinfo=datetime.timezone.utc)
    assert event == Presence(
        statuses={
            "1234": ActiveStatus(active=False, last_active=la),
            "2345": ActiveStatus(active=True),
        },
        full=False,
    )


def test_orca_presence_full(session):
    data = {
        "list_type": "full",
        "list": [
            {"u": 1234, "p": 2, "c": 5767242},
            {"u": 2345, "p": 2, "l": 1500000000},
            {"u": 3456, "p": 2, "c": 9961482},
            {"u": 4567, "p": 0, "l": 1500000000},
            {"u": 5678, "p": 0},
            {"u": 6789, "p": 2, "c": 14168154},
        ],
    }
    (event,) = parse_events(session, "/orca_presence", data)
    la = datetime.datetime(2017, 7, 14, 2, 40, tzinfo=datetime.timezone.utc)
    assert event == Presence(
        statuses={
            "1234": ActiveStatus(active=True),
            "2345": ActiveStatus(active=True, last_active=la),
            "3456": ActiveStatus(active=True),
            "4567": ActiveStatus(active=False, last_active=la),
            "5678": ActiveStatus(active=False),
            "6789": ActiveStatus(active=True),
        },
        full=True,
    )
