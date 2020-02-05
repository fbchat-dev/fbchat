import datetime
from fbchat import TitleSet, Group, User
from fbchat._events import parse_delta


def test_listen(session):
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


def test_fetch(session):
    data = {
        "__typename": "ThreadNameMessage",
        "message_id": "mid.$XYZ",
        "offline_threading_id": "1122334455",
        "message_sender": {"id": "1234", "email": "1234@facebook.com"},
        "ttl": 0,
        "timestamp_precise": "1500000000000",
        "unread": False,
        "is_sponsored": False,
        "ad_id": None,
        "ad_client_token": None,
        "commerce_message_type": None,
        "customizations": [],
        "tags_list": ["inbox", "sent", "tq", "blindly_apply_message_folder"],
        "platform_xmd_encoded": None,
        "message_source_data": None,
        "montage_reply_data": None,
        "message_reactions": [],
        "unsent_timestamp_precise": "0",
        "message_unsendability_status": "deny_log_message",
        "thread_name": "",
        "snippet": "You removed the group name.",
        "replied_to_message": None,
    }
    thread = Group(session=session, id="4321")
    assert TitleSet(
        author=User(session=session, id="1234"),
        thread=thread,
        title=None,
        at=datetime.datetime(2017, 7, 14, 2, 40, tzinfo=datetime.timezone.utc),
    ) == TitleSet._from_fetch(thread, data)
