import datetime
import pytest
from fbchat import (
    ParseError,
    User,
    Group,
    Message,
    MessageData,
    UnknownEvent,
    ReactionEvent,
    UserStatusEvent,
    LiveLocationEvent,
    UnsendEvent,
    MessageReplyEvent,
)
from fbchat._events import parse_client_delta, parse_client_payloads


def test_reaction_event_added(session):
    data = {
        "threadKey": {"otherUserFbId": 1234},
        "messageId": "mid.$XYZ",
        "action": 0,
        "userId": 4321,
        "reaction": "😍",
        "senderId": 4321,
        "offlineThreadingId": "6623596674408921967",
    }
    thread = User(session=session, id="1234")
    assert ReactionEvent(
        author=User(session=session, id="4321"),
        thread=thread,
        message=Message(thread=thread, id="mid.$XYZ"),
        reaction="😍",
    ) == parse_client_delta(session, {"deltaMessageReaction": data})


def test_reaction_event_removed(session):
    data = {
        "threadKey": {"threadFbId": 1234},
        "messageId": "mid.$XYZ",
        "action": 1,
        "userId": 4321,
        "senderId": 4321,
        "offlineThreadingId": "6623586106713014836",
    }
    thread = Group(session=session, id="1234")
    assert ReactionEvent(
        author=User(session=session, id="4321"),
        thread=thread,
        message=Message(thread=thread, id="mid.$XYZ"),
        reaction=None,
    ) == parse_client_delta(session, {"deltaMessageReaction": data})


def test_user_status_blocked(session):
    data = {
        "threadKey": {"otherUserFbId": 1234},
        "canViewerReply": False,
        "reason": 2,
        "actorFbid": 4321,
    }
    assert UserStatusEvent(
        author=User(session=session, id="4321"),
        thread=User(session=session, id="1234"),
        blocked=True,
    ) == parse_client_delta(session, {"deltaChangeViewerStatus": data})


def test_user_status_unblocked(session):
    data = {
        "threadKey": {"otherUserFbId": 1234},
        "canViewerReply": True,
        "reason": 2,
        "actorFbid": 1234,
    }
    assert UserStatusEvent(
        author=User(session=session, id="1234"),
        thread=User(session=session, id="1234"),
        blocked=False,
    ) == parse_client_delta(session, {"deltaChangeViewerStatus": data})


@pytest.mark.skip(reason="need to gather test data")
def test_live_location(session):
    pass


def test_message_reply(session):
    message = {
        "messageMetadata": {
            "threadKey": {"otherUserFbId": 1234},
            "messageId": "mid.$XYZ",
            "offlineThreadingId": "112233445566",
            "actorFbId": 1234,
            "timestamp": 1500000000000,
            "tags": ["source:messenger:web", "cg-enabled", "sent", "inbox"],
            "threadReadStateEffect": 3,
            "skipBumpThread": False,
            "skipSnippetUpdate": False,
            "unsendType": "can_unsend",
            "folderId": {"systemFolderId": 0},
        },
        "body": "xyz",
        "attachments": [],
        "irisSeqId": 1111111,
        "messageReply": {"replyToMessageId": {"id": "mid.$ABC"}, "status": 0,},
        "requestContext": {"apiArgs": "..."},
        "irisTags": ["DeltaNewMessage"],
    }
    reply = {
        "messageMetadata": {
            "threadKey": {"otherUserFbId": 1234},
            "messageId": "mid.$ABC",
            "offlineThreadingId": "665544332211",
            "actorFbId": 4321,
            "timestamp": 1600000000000,
            "tags": ["inbox", "sent", "source:messenger:web"],
        },
        "body": "abc",
        "attachments": [],
        "requestContext": {"apiArgs": "..."},
        "irisTags": [],
    }
    data = {
        "message": message,
        "repliedToMessage": reply,
        "status": 0,
    }
    thread = User(session=session, id="1234")
    assert MessageReplyEvent(
        author=User(session=session, id="1234"),
        thread=thread,
        message=MessageData(
            thread=thread,
            id="mid.$XYZ",
            author="1234",
            created_at=datetime.datetime(
                2017, 7, 14, 2, 40, tzinfo=datetime.timezone.utc
            ),
            text="xyz",
            reply_to_id="mid.$ABC",
        ),
        replied_to=MessageData(
            thread=thread,
            id="mid.$ABC",
            author="4321",
            created_at=datetime.datetime(
                2020, 9, 13, 12, 26, 40, tzinfo=datetime.timezone.utc
            ),
            text="abc",
        ),
    ) == parse_client_delta(session, {"deltaMessageReply": data})


def test_parse_client_delta_unknown(session):
    assert UnknownEvent(
        source="client payload", data={"abc": 10}
    ) == parse_client_delta(session, {"abc": 10})


def test_parse_client_payloads_empty(session):
    # This is never something that happens, it's just so that we can test the parsing
    # payload = '{"deltas":[]}'
    payload = [123, 34, 100, 101, 108, 116, 97, 115, 34, 58, 91, 93, 125]
    data = {"payload": payload, "class": "ClientPayload"}
    assert [] == list(parse_client_payloads(session, data))


def test_parse_client_payloads_invalid(session):
    # payload = '{"invalid":"data"}'
    payload = [123, 34, 105, 110, 118, 97, 108, 105, 100, 34, 58, 34, 97, 34, 125]
    data = {"payload": payload, "class": "ClientPayload"}
    with pytest.raises(ParseError, match="Error parsing ClientPayload"):
        list(parse_client_payloads(session, data))
