import pytest
from fbchat import Group, User, ParseError, ThreadEvent


def test_thread_event_get_thread_group1(session):
    data = {
        "threadKey": {"threadFbId": 1234},
        "messageId": "mid.$gAAT4Sw1WSGh14A3MOFvrsiDvr3Yc",
        "offlineThreadingId": "6623583531508397596",
        "actorFbId": 4321,
        "timestamp": 1500000000000,
        "tags": [
            "inbox",
            "sent",
            "tq",
            "blindly_apply_message_folder",
            "source:messenger:web",
        ],
    }
    assert Group(session=session, id="1234") == ThreadEvent._get_thread(session, data)


def test_thread_event_get_thread_group2(session):
    data = {
        "actorFbId": "4321",
        "folderId": {"systemFolderId": "INBOX"},
        "messageId": "mid.$XYZ",
        "offlineThreadingId": "112233445566",
        "skipBumpThread": False,
        "tags": ["source:messenger:web"],
        "threadKey": {"threadFbId": "1234"},
        "threadReadStateEffect": "KEEP_AS_IS",
        "timestamp": "1500000000000",
    }
    assert Group(session=session, id="1234") == ThreadEvent._get_thread(session, data)


def test_thread_event_get_thread_user(session):
    data = {
        "actorFbId": "4321",
        "folderId": {"systemFolderId": "INBOX"},
        "messageId": "mid.$XYZ",
        "offlineThreadingId": "112233445566",
        "skipBumpThread": False,
        "skipSnippetUpdate": False,
        "tags": ["source:messenger:web"],
        "threadKey": {"otherUserFbId": "1234"},
        "threadReadStateEffect": "KEEP_AS_IS",
        "timestamp": "1500000000000",
    }
    assert User(session=session, id="1234") == ThreadEvent._get_thread(session, data)


def test_thread_event_get_thread_unknown(session):
    data = {"threadKey": {"abc": "1234"}}
    with pytest.raises(ParseError, match="Could not find thread data"):
        ThreadEvent._get_thread(session, data)
