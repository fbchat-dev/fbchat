import datetime
import pytest
from fbchat import (
    ParseError,
    User,
    Group,
    Message,
    MessageData,
    ThreadLocation,
    UnknownEvent,
    PeopleAdded,
    PersonRemoved,
    TitleSet,
    UnfetchedThreadEvent,
    MessagesDelivered,
    ThreadsRead,
    MessageEvent,
    ThreadFolder,
)
from fbchat._events import parse_delta


def test_people_added(session):
    data = {
        "addedParticipants": [
            {
                "fanoutPolicy": "IRIS_MESSAGE_QUEUE",
                "firstName": "Abc",
                "fullName": "Abc Def",
                "initialFolder": "FOLDER_INBOX",
                "initialFolderId": {"systemFolderId": "INBOX"},
                "isMessengerUser": False,
                "userFbId": "1234",
            }
        ],
        "irisSeqId": "11223344",
        "irisTags": ["DeltaParticipantsAddedToGroupThread", "is_from_iris_fanout"],
        "messageMetadata": {
            "actorFbId": "3456",
            "adminText": "You added Abc Def to the group.",
            "folderId": {"systemFolderId": "INBOX"},
            "messageId": "mid.$XYZ",
            "offlineThreadingId": "1122334455",
            "skipBumpThread": False,
            "tags": [],
            "threadKey": {"threadFbId": "4321"},
            "threadReadStateEffect": "KEEP_AS_IS",
            "timestamp": "1500000000000",
            "unsendType": "deny_log_message",
        },
        "participants": ["1234", "2345", "3456", "4567"],
        "requestContext": {"apiArgs": {}},
        "tqSeqId": "1111",
        "class": "ParticipantsAddedToGroupThread",
    }
    assert PeopleAdded(
        author=User(session=session, id="3456"),
        thread=Group(session=session, id="4321"),
        added=[User(session=session, id="1234")],
        at=datetime.datetime(2017, 7, 14, 2, 40, tzinfo=datetime.timezone.utc),
    ) == parse_delta(session, data)


def test_person_removed(session):
    data = {
        "irisSeqId": "11223344",
        "irisTags": ["DeltaParticipantLeftGroupThread", "is_from_iris_fanout"],
        "leftParticipantFbId": "1234",
        "messageMetadata": {
            "actorFbId": "3456",
            "adminText": "You removed Abc Def from the group.",
            "folderId": {"systemFolderId": "INBOX"},
            "messageId": "mid.$XYZ",
            "offlineThreadingId": "1122334455",
            "skipBumpThread": True,
            "tags": [],
            "threadKey": {"threadFbId": "4321"},
            "threadReadStateEffect": "KEEP_AS_IS",
            "timestamp": "1500000000000",
            "unsendType": "deny_log_message",
        },
        "participants": ["1234", "2345", "3456", "4567"],
        "requestContext": {"apiArgs": {}},
        "tqSeqId": "1111",
        "class": "ParticipantLeftGroupThread",
    }
    assert PersonRemoved(
        author=User(session=session, id="3456"),
        thread=Group(session=session, id="4321"),
        removed=User(session=session, id="1234"),
        at=datetime.datetime(2017, 7, 14, 2, 40, tzinfo=datetime.timezone.utc),
    ) == parse_delta(session, data)


def test_title_set(session):
    data = {
        "irisSeqId": "11223344",
        "irisTags": ["DeltaThreadName", "is_from_iris_fanout"],
        "messageMetadata": {
            "actorFbId": "3456",
            "adminText": "You named the group abc.",
            "folderId": {"systemFolderId": "INBOX"},
            "messageId": "mid.$XYZ",
            "offlineThreadingId": "1122334455",
            "skipBumpThread": False,
            "tags": [],
            "threadKey": {"threadFbId": "4321"},
            "threadReadStateEffect": "KEEP_AS_IS",
            "timestamp": "1500000000000",
            "unsendType": "deny_log_message",
        },
        "name": "abc",
        "participants": ["1234", "2345", "3456", "4567"],
        "requestContext": {"apiArgs": {}},
        "tqSeqId": "1111",
        "class": "ThreadName",
    }
    assert TitleSet(
        author=User(session=session, id="3456"),
        thread=Group(session=session, id="4321"),
        title="abc",
        at=datetime.datetime(2017, 7, 14, 2, 40, tzinfo=datetime.timezone.utc),
    ) == parse_delta(session, data)


def test_title_removed(session):
    data = {
        "irisSeqId": "11223344",
        "irisTags": ["DeltaThreadName", "is_from_iris_fanout"],
        "messageMetadata": {
            "actorFbId": "3456",
            "adminText": "You removed the group name.",
            "folderId": {"systemFolderId": "INBOX"},
            "messageId": "mid.$XYZ",
            "offlineThreadingId": "1122334455",
            "skipBumpThread": False,
            "tags": [],
            "threadKey": {"threadFbId": "4321"},
            "threadReadStateEffect": "KEEP_AS_IS",
            "timestamp": "1500000000000",
            "unsendType": "deny_log_message",
        },
        "name": "",
        "participants": ["1234", "2345", "3456", "4567"],
        "requestContext": {"apiArgs": {}},
        "tqSeqId": "1111",
        "class": "ThreadName",
    }
    assert TitleSet(
        author=User(session=session, id="3456"),
        thread=Group(session=session, id="4321"),
        title=None,
        at=datetime.datetime(2017, 7, 14, 2, 40, tzinfo=datetime.timezone.utc),
    ) == parse_delta(session, data)


def test_forced_fetch(session):
    data = {
        "forceInsert": False,
        "messageId": "mid.$XYZ",
        "threadKey": {"threadFbId": "1234"},
        "class": "ForcedFetch",
    }
    thread = Group(session=session, id="1234")
    assert UnfetchedThreadEvent(
        thread=thread, message=Message(thread=thread, id="mid.$XYZ")
    ) == parse_delta(session, data)


def test_forced_fetch_pending(session):
    data = {
        "forceInsert": False,
        "irisSeqId": "1111",
        "isLazy": False,
        "threadKey": {"threadFbId": "1234"},
        "class": "ForcedFetch",
    }
    assert UnfetchedThreadEvent(
        thread=Group(session=session, id="1234"), message=None
    ) == parse_delta(session, data)


def test_delivery_receipt_group(session):
    data = {
        "actorFbId": "1234",
        "deliveredWatermarkTimestampMs": "1500000000000",
        "irisSeqId": "1111111",
        "irisTags": ["DeltaDeliveryReceipt"],
        "messageIds": ["mid.$XYZ", "mid.$ABC"],
        "requestContext": {"apiArgs": {}},
        "threadKey": {"threadFbId": "4321"},
        "class": "DeliveryReceipt",
    }
    thread = Group(session=session, id="4321")
    assert MessagesDelivered(
        author=User(session=session, id="1234"),
        thread=thread,
        messages=[
            Message(thread=thread, id="mid.$XYZ"),
            Message(thread=thread, id="mid.$ABC"),
        ],
        at=datetime.datetime(2017, 7, 14, 2, 40, tzinfo=datetime.timezone.utc),
    ) == parse_delta(session, data)


def test_delivery_receipt_user(session):
    data = {
        "deliveredWatermarkTimestampMs": "1500000000000",
        "irisSeqId": "1111111",
        "irisTags": ["DeltaDeliveryReceipt", "is_from_iris_fanout"],
        "messageIds": ["mid.$XYZ", "mid.$ABC"],
        "requestContext": {"apiArgs": {}},
        "threadKey": {"otherUserFbId": "1234"},
        "class": "DeliveryReceipt",
    }
    thread = User(session=session, id="1234")
    assert MessagesDelivered(
        author=thread,
        thread=thread,
        messages=[
            Message(thread=thread, id="mid.$XYZ"),
            Message(thread=thread, id="mid.$ABC"),
        ],
        at=datetime.datetime(2017, 7, 14, 2, 40, tzinfo=datetime.timezone.utc),
    ) == parse_delta(session, data)


def test_read_receipt(session):
    data = {
        "actionTimestampMs": "1600000000000",
        "actorFbId": "1234",
        "irisSeqId": "1111111",
        "irisTags": ["DeltaReadReceipt", "is_from_iris_fanout"],
        "requestContext": {"apiArgs": {}},
        "threadKey": {"threadFbId": "4321"},
        "tqSeqId": "1111",
        "watermarkTimestampMs": "1500000000000",
        "class": "ReadReceipt",
    }
    assert ThreadsRead(
        author=User(session=session, id="1234"),
        threads=[Group(session=session, id="4321")],
        at=datetime.datetime(2020, 9, 13, 12, 26, 40, tzinfo=datetime.timezone.utc),
    ) == parse_delta(session, data)


def test_mark_read(session):
    data = {
        "actionTimestamp": "1600000000000",
        "irisSeqId": "1111111",
        "irisTags": ["DeltaMarkRead", "is_from_iris_fanout"],
        "threadKeys": [{"threadFbId": "1234"}, {"otherUserFbId": "2345"}],
        "tqSeqId": "1111",
        "watermarkTimestamp": "1500000000000",
        "class": "MarkRead",
    }
    assert ThreadsRead(
        author=session.user,
        threads=[Group(session=session, id="1234"), User(session=session, id="2345")],
        at=datetime.datetime(2020, 9, 13, 12, 26, 40, tzinfo=datetime.timezone.utc),
    ) == parse_delta(session, data)


def test_new_message_user(session):
    data = {
        "attachments": [],
        "body": "test",
        "irisSeqId": "1111111",
        "irisTags": ["DeltaNewMessage"],
        "messageMetadata": {
            "actorFbId": "1234",
            "folderId": {"systemFolderId": "INBOX"},
            "messageId": "mid.$XYZ",
            "offlineThreadingId": "11223344556677889900",
            "skipBumpThread": False,
            "skipSnippetUpdate": False,
            "tags": ["source:messenger:web"],
            "threadKey": {"otherUserFbId": "1234"},
            "threadReadStateEffect": "KEEP_AS_IS",
            "timestamp": "1600000000000",
        },
        "requestContext": {"apiArgs": {}},
        "class": "NewMessage",
    }
    assert MessageEvent(
        author=User(session=session, id="1234"),
        thread=User(session=session, id="1234"),
        message=MessageData(
            thread=User(session=session, id="1234"),
            id="mid.$XYZ",
            author="1234",
            text="test",
            created_at=datetime.datetime(
                2020, 9, 13, 12, 26, 40, tzinfo=datetime.timezone.utc
            ),
        ),
        at=datetime.datetime(2020, 9, 13, 12, 26, 40, tzinfo=datetime.timezone.utc),
    ) == parse_delta(session, data)


def test_new_message_group(session):
    data = {
        "attachments": [],
        "body": "test",
        "irisSeqId": "1111111",
        "irisTags": ["DeltaNewMessage", "is_from_iris_fanout"],
        "messageMetadata": {
            "actorFbId": "4321",
            "folderId": {"systemFolderId": "INBOX"},
            "messageId": "mid.$XYZ",
            "offlineThreadingId": "11223344556677889900",
            "skipBumpThread": False,
            "tags": ["source:messenger:web"],
            "threadKey": {"threadFbId": "1234"},
            "threadReadStateEffect": "KEEP_AS_IS",
            "timestamp": "1600000000000",
        },
        "participants": ["4321", "5432", "6543"],
        "requestContext": {"apiArgs": {}},
        "tqSeqId": "1111",
        "class": "NewMessage",
    }
    assert MessageEvent(
        author=User(session=session, id="4321"),
        thread=Group(session=session, id="1234"),
        message=MessageData(
            thread=Group(session=session, id="1234"),
            id="mid.$XYZ",
            author="4321",
            text="test",
            created_at=datetime.datetime(
                2020, 9, 13, 12, 26, 40, tzinfo=datetime.timezone.utc
            ),
        ),
        at=datetime.datetime(2020, 9, 13, 12, 26, 40, tzinfo=datetime.timezone.utc),
    ) == parse_delta(session, data)


def test_thread_folder(session):
    data = {
        "class": "ThreadFolder",
        "folder": "FOLDER_PENDING",
        "irisSeqId": "1111",
        "irisTags": ["DeltaThreadFolder", "is_from_iris_fanout"],
        "requestContext": {"apiArgs": {}},
        "threadKey": {"otherUserFbId": "1234"},
    }
    assert ThreadFolder(
        thread=User(session=session, id="1234"), folder=ThreadLocation.PENDING
    ) == parse_delta(session, data)


def test_noop(session):
    assert parse_delta(session, {"class": "NoOp"}) is None


def test_parse_delta_unknown(session):
    data = {"class": "Abc"}
    assert UnknownEvent(source="Delta class", data=data) == parse_delta(session, data)
