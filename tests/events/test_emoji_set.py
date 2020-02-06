import datetime
from fbchat import EmojiSet, Group, User
from fbchat._events import parse_admin_message


def test_listen(session):
    data = {
        "irisSeqId": "1111111",
        "irisTags": ["DeltaAdminTextMessage"],
        "messageMetadata": {
            "actorFbId": "1234",
            "adminText": "You set the emoji to 🌟.",
            "folderId": {"systemFolderId": "INBOX"},
            "messageId": "mid.$XYZ",
            "offlineThreadingId": "11223344556677889900",
            "skipBumpThread": False,
            "skipSnippetUpdate": False,
            "tags": ["source:generic_admin_text"],
            "threadKey": {"otherUserFbId": "1234"},
            "threadReadStateEffect": "MARK_UNREAD",
            "timestamp": "1500000000000",
            "unsendType": "deny_log_message",
        },
        "requestContext": {"apiArgs": {}},
        "type": "change_thread_icon",
        "untypedData": {
            "thread_icon_url": "https://www.facebook.com/images/emoji.php/v9/te0/1/16/1f31f.png",
            "thread_icon": "🌟",
        },
        "class": "AdminTextMessage",
    }
    assert EmojiSet(
        author=User(session=session, id="1234"),
        thread=User(session=session, id="1234"),
        emoji="🌟",
        at=datetime.datetime(2017, 7, 14, 2, 40, tzinfo=datetime.timezone.utc),
    ) == parse_admin_message(session, data)


def test_fetch(session):
    data = {
        "__typename": "GenericAdminTextMessage",
        "message_id": "mid.$XYZ",
        "offline_threading_id": "1122334455",
        "message_sender": {"id": "1234", "email": "1234@facebook.com",},
        "ttl": 0,
        "timestamp_precise": "1500000000000",
        "unread": True,
        "is_sponsored": False,
        "ad_id": None,
        "ad_client_token": None,
        "commerce_message_type": None,
        "customizations": [],
        "tags_list": [
            "inbox",
            "sent",
            "no_push",
            "tq",
            "blindly_apply_message_folder",
            "source:titan:web",
        ],
        "platform_xmd_encoded": None,
        "message_source_data": None,
        "montage_reply_data": None,
        "message_reactions": [],
        "unsent_timestamp_precise": "0",
        "message_unsendability_status": "deny_log_message",
        "extensible_message_admin_text": {
            "__typename": "ThreadIconExtensibleMessageAdminText",
            "thread_icon": "😊",
        },
        "extensible_message_admin_text_type": "CHANGE_THREAD_ICON",
        "snippet": "You set the emoji to 😊.",
        "replied_to_message": None,
    }
    thread = Group(session=session, id="4321")
    assert EmojiSet(
        author=User(session=session, id="1234"),
        thread=thread,
        emoji="😊",
        at=datetime.datetime(2017, 7, 14, 2, 40, tzinfo=datetime.timezone.utc),
    ) == EmojiSet._from_fetch(thread, data)
