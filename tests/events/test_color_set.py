import datetime
from fbchat import ColorSet, Group, User
from fbchat._events import parse_admin_message


def test_listen(session):
    data = {
        "irisSeqId": "1111111",
        "irisTags": ["DeltaAdminTextMessage", "is_from_iris_fanout"],
        "messageMetadata": {
            "actorFbId": "1234",
            "adminText": "You changed the chat theme to Orange.",
            "folderId": {"systemFolderId": "INBOX"},
            "messageId": "mid.$XYZ",
            "offlineThreadingId": "11223344556677889900",
            "skipBumpThread": False,
            "tags": ["source:titan:web", "no_push"],
            "threadKey": {"threadFbId": "4321"},
            "threadReadStateEffect": "MARK_UNREAD",
            "timestamp": "1500000000000",
            "unsendType": "deny_log_message",
        },
        "participants": ["1234", "2345", "3456"],
        "requestContext": {"apiArgs": {}},
        "tqSeqId": "1111",
        "type": "change_thread_theme",
        "untypedData": {
            "should_show_icon": "1",
            "theme_color": "FFFF7E29",
            "accessibility_label": "Orange",
        },
        "class": "AdminTextMessage",
    }
    assert ColorSet(
        author=User(session=session, id="1234"),
        thread=Group(session=session, id="4321"),
        color="#ff7e29",
        at=datetime.datetime(2017, 7, 14, 2, 40, tzinfo=datetime.timezone.utc),
    ) == parse_admin_message(session, data)


def test_fetch(session):
    data = {
        "__typename": "GenericAdminTextMessage",
        "message_id": "mid.$XYZ",
        "offline_threading_id": "1122334455",
        "message_sender": {"id": "1234", "email": "1234@facebook.com"},
        "ttl": 0,
        "timestamp_precise": "1500000000000",
        "unread": True,
        "is_sponsored": False,
        "ad_id": None,
        "ad_client_token": None,
        "commerce_message_type": None,
        "customizations": [],
        "tags_list": ["inbox", "sent", "source:generic_admin_text"],
        "platform_xmd_encoded": None,
        "message_source_data": None,
        "montage_reply_data": None,
        "message_reactions": [],
        "unsent_timestamp_precise": "0",
        "message_unsendability_status": "deny_log_message",
        "extensible_message_admin_text": {
            "__typename": "ThemeColorExtensibleMessageAdminText",
            "theme_color": "FFFFC300",
        },
        "extensible_message_admin_text_type": "CHANGE_THREAD_THEME",
        "snippet": "You changed the chat theme to Yellow.",
        "replied_to_message": None,
    }
    thread = User(session=session, id="4321")
    assert ColorSet(
        author=User(session=session, id="1234"),
        thread=thread,
        color="#ffc300",
        at=datetime.datetime(2017, 7, 14, 2, 40, tzinfo=datetime.timezone.utc),
    ) == ColorSet._from_fetch(thread, data)
