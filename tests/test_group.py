from fbchat import GroupData, User


def test_group_from_graphql(session):
    data = {
        "name": "Group ABC",
        "thread_key": {"thread_fbid": "11223344"},
        "image": None,
        "is_group_thread": True,
        "all_participants": {
            "nodes": [
                {"messaging_actor": {"__typename": "User", "id": "1234"}},
                {"messaging_actor": {"__typename": "User", "id": "2345"}},
                {"messaging_actor": {"__typename": "User", "id": "3456"}},
            ]
        },
        "customization_info": {
            "participant_customizations": [],
            "outgoing_bubble_color": None,
            "emoji": "😀",
        },
        "thread_admins": [{"id": "1234"}],
        "group_approval_queue": {"nodes": []},
        "approval_mode": 0,
        "joinable_mode": {"mode": "0", "link": ""},
        "event_reminders": {"nodes": []},
    }
    assert GroupData(
        session=session,
        id="11223344",
        photo=None,
        name="Group ABC",
        last_active=None,
        message_count=None,
        plan=None,
        participants=[
            User(session=session, id="1234"),
            User(session=session, id="2345"),
            User(session=session, id="3456"),
        ],
        nicknames={},
        color="#0084ff",
        emoji="😀",
        admins={"1234"},
        approval_mode=False,
        approval_requests=set(),
        join_link="",
    ) == GroupData._from_graphql(session, data)
