import datetime
from fbchat import User, Group, ParticipantRemoved
from fbchat._events import parse_delta


def test_listen(session):
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
    assert ParticipantRemoved(
        author=User(session=session, id="3456"),
        thread=Group(session=session, id="4321"),
        removed=User(session=session, id="1234"),
        at=datetime.datetime(2017, 7, 14, 2, 40, tzinfo=datetime.timezone.utc),
    ) == parse_delta(session, data)


def test_send(session):
    thread = Group(session=session, id="4321")
    assert ParticipantRemoved(
        author=session.user,
        thread=thread,
        removed=User(session=session, id="1234"),
        at=None,
    ) == ParticipantRemoved._from_send(thread, "1234")


def test_fetch(session):
    data = {
        "__typename": "ParticipantLeftMessage",
        "message_id": "mid.$XYZ",
        "offline_threading_id": "1122334455",
        "message_sender": {"id": "3456", "email": "3456@facebook.com"},
        "ttl": 0,
        "timestamp_precise": "1500000000000",
        "unread": False,
        "is_sponsored": False,
        "ad_id": None,
        "ad_client_token": None,
        "commerce_message_type": None,
        "customizations": [],
        "tags_list": [
            "inbox",
            "tq",
            "blindly_apply_message_folder",
            "filtered_content",
            "filtered_content_account",
        ],
        "platform_xmd_encoded": None,
        "message_source_data": None,
        "montage_reply_data": None,
        "message_reactions": [],
        "unsent_timestamp_precise": "0",
        "message_unsendability_status": "deny_for_non_sender",
        "participants_removed": [{"id": "1234"}],
        "snippet": "A contact removed Abc Def from the group.",
        "replied_to_message": None,
    }
    thread = Group(session=session, id="4321")
    assert ParticipantRemoved(
        author=User(session=session, id="3456"),
        thread=thread,
        removed=User(session=session, id="1234"),
        at=datetime.datetime(2017, 7, 14, 2, 40, tzinfo=datetime.timezone.utc),
    ) == ParticipantRemoved._from_fetch(thread, data)
