import pytest
import datetime
import fbchat
from fbchat import UserData, ActiveStatus


def test_user_from_graphql(session):
    data = {
        "id": "1234",
        "name": "Abc Def Ghi",
        "first_name": "Abc",
        "last_name": "Ghi",
        "profile_picture": {"uri": "https://scontent-arn2-1.xx.fbcdn.net/v/..."},
        "is_viewer_friend": True,
        "url": "https://www.facebook.com/profile.php?id=1234",
        "gender": "FEMALE",
        "viewer_affinity": 0.4560002,
    }
    assert UserData(
        session=session,
        id="1234",
        photo=fbchat.Image(url="https://scontent-arn2-1.xx.fbcdn.net/v/..."),
        name="Abc Def Ghi",
        url="https://www.facebook.com/profile.php?id=1234",
        first_name="Abc",
        last_name="Ghi",
        is_friend=True,
        gender="female_singular",
        affinity=0.4560002,
        color="#0084ff",
    ) == UserData._from_graphql(session, data)


def test_user_from_thread_fetch(session):
    data = {
        "thread_key": {"thread_fbid": None, "other_user_id": "1234"},
        "name": None,
        "last_message": {
            "nodes": [
                {
                    "snippet": "aaa",
                    "message_sender": {"messaging_actor": {"id": "1234"}},
                    "timestamp_precise": "1500000000000",
                    "commerce_message_type": None,
                    "extensible_attachment": None,
                    "sticker": None,
                    "blob_attachments": [],
                }
            ]
        },
        "unread_count": 0,
        "messages_count": 1111,
        "image": None,
        "updated_time_precise": "1500000000000",
        "mute_until": None,
        "is_pin_protected": False,
        "is_viewer_subscribed": True,
        "thread_queue_enabled": False,
        "folder": "INBOX",
        "has_viewer_archived": False,
        "is_page_follow_up": False,
        "cannot_reply_reason": None,
        "ephemeral_ttl_mode": 0,
        "customization_info": {
            "emoji": None,
            "participant_customizations": [
                {"participant_id": "4321", "nickname": "B"},
                {"participant_id": "1234", "nickname": "A"},
            ],
            "outgoing_bubble_color": None,
        },
        "thread_admins": [],
        "approval_mode": None,
        "joinable_mode": {"mode": "0", "link": ""},
        "thread_queue_metadata": None,
        "event_reminders": {"nodes": []},
        "montage_thread": None,
        "last_read_receipt": {"nodes": [{"timestamp_precise": "1500000050000"}]},
        "related_page_thread": None,
        "rtc_call_data": {
            "call_state": "NO_ONGOING_CALL",
            "server_info_data": "",
            "initiator": None,
        },
        "associated_object": None,
        "privacy_mode": 1,
        "reactions_mute_mode": "REACTIONS_NOT_MUTED",
        "mentions_mute_mode": "MENTIONS_NOT_MUTED",
        "customization_enabled": True,
        "thread_type": "ONE_TO_ONE",
        "participant_add_mode_as_string": None,
        "is_canonical_neo_user": False,
        "participants_event_status": [],
        "page_comm_item": None,
        "all_participants": {
            "nodes": [
                {
                    "messaging_actor": {
                        "id": "1234",
                        "__typename": "User",
                        "name": "Abc Def Ghi",
                        "gender": "FEMALE",
                        "url": "https://www.facebook.com/profile.php?id=1234",
                        "big_image_src": {
                            "uri": "https://scontent-arn2-1.xx.fbcdn.net/v/..."
                        },
                        "short_name": "Abc",
                        "username": "",
                        "is_viewer_friend": True,
                        "is_messenger_user": True,
                        "is_verified": False,
                        "is_message_blocked_by_viewer": False,
                        "is_viewer_coworker": False,
                        "is_employee": None,
                    }
                },
                {
                    "messaging_actor": {
                        "id": "4321",
                        "__typename": "User",
                        "name": "Aaa Bbb Ccc",
                        "gender": "NEUTER",
                        "url": "https://www.facebook.com/aaabbbccc",
                        "big_image_src": {
                            "uri": "https://scontent-arn2-1.xx.fbcdn.net/v/..."
                        },
                        "short_name": "Aaa",
                        "username": "aaabbbccc",
                        "is_viewer_friend": False,
                        "is_messenger_user": True,
                        "is_verified": False,
                        "is_message_blocked_by_viewer": False,
                        "is_viewer_coworker": False,
                        "is_employee": None,
                    }
                },
            ]
        },
        "read_receipts": ...,
        "delivery_receipts": ...,
    }
    assert UserData(
        session=session,
        id="1234",
        photo=fbchat.Image(url="https://scontent-arn2-1.xx.fbcdn.net/v/..."),
        name="Abc Def Ghi",
        last_active=datetime.datetime(2017, 7, 14, 2, 40, tzinfo=datetime.timezone.utc),
        message_count=1111,
        url="https://www.facebook.com/profile.php?id=1234",
        first_name="Abc",
        is_friend=True,
        gender="female_singular",
        nickname="A",
        own_nickname="B",
        color="#0084ff",
        emoji=None,
    ) == UserData._from_thread_fetch(session, data)


def test_user_from_all_fetch(session):
    data = {
        "id": "1234",
        "name": "Abc Def Ghi",
        "firstName": "Abc",
        "vanity": "",
        "thumbSrc": "https://scontent-arn2-1.xx.fbcdn.net/v/...",
        "uri": "https://www.facebook.com/profile.php?id=1234",
        "gender": 1,
        "i18nGender": 2,
        "type": "friend",
        "is_friend": True,
        "mThumbSrcSmall": None,
        "mThumbSrcLarge": None,
        "dir": None,
        "searchTokens": ["Abc", "Ghi"],
        "alternateName": "",
        "is_nonfriend_messenger_contact": False,
        "is_blocked": False,
    }
    assert UserData(
        session=session,
        id="1234",
        photo=fbchat.Image(url="https://scontent-arn2-1.xx.fbcdn.net/v/..."),
        name="Abc Def Ghi",
        url="https://www.facebook.com/profile.php?id=1234",
        first_name="Abc",
        is_friend=True,
        gender="female_singular",
    ) == UserData._from_all_fetch(session, data)


@pytest.mark.skip(reason="can't gather test data, the pulling is broken")
def test_active_status_from_chatproxy_presence():
    assert ActiveStatus() == ActiveStatus._from_chatproxy_presence(data)


@pytest.mark.skip(reason="can't gather test data, the pulling is broken")
def test_active_status_from_buddylist_overlay():
    assert ActiveStatus() == ActiveStatus._from_buddylist_overlay(data)
