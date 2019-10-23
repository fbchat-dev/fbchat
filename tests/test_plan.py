import datetime
from fbchat._plan import GuestStatus, Plan


def test_plan_properties():
    plan = Plan(time=..., title=...)
    plan.guests = {
        "1234": GuestStatus.INVITED,
        "2345": GuestStatus.INVITED,
        "3456": GuestStatus.GOING,
        "4567": GuestStatus.DECLINED,
    }
    assert set(plan.invited) == {"1234", "2345"}
    assert plan.going == ["3456"]
    assert plan.declined == ["4567"]


def test_plan_from_pull():
    data = {
        "event_timezone": "",
        "event_creator_id": "1234",
        "event_id": "1111",
        "event_type": "EVENT",
        "event_track_rsvp": "1",
        "event_title": "abc",
        "event_time": "1500000000",
        "event_seconds_to_notify_before": "3600",
        "guest_state_list": (
            '[{"guest_list_state":"INVITED","node":{"id":"1234"}},'
            '{"guest_list_state":"INVITED","node":{"id":"2356"}},'
            '{"guest_list_state":"DECLINED","node":{"id":"3456"}},'
            '{"guest_list_state":"GOING","node":{"id":"4567"}}]'
        ),
    }
    plan = Plan(
        time=datetime.datetime(2017, 7, 14, 2, 40, tzinfo=datetime.timezone.utc),
        title="abc",
    )
    plan.uid = "1111"
    plan.author_id = "1234"
    plan.guests = {
        "1234": GuestStatus.INVITED,
        "2356": GuestStatus.INVITED,
        "3456": GuestStatus.DECLINED,
        "4567": GuestStatus.GOING,
    }
    assert plan == Plan._from_pull(data)


def test_plan_from_fetch():
    data = {
        "message_thread_id": 123456789,
        "event_time": 1500000000,
        "creator_id": 1234,
        "event_time_updated_time": 1450000000,
        "title": "abc",
        "track_rsvp": 1,
        "event_type": "EVENT",
        "status": "created",
        "message_id": "mid.xyz",
        "seconds_to_notify_before": 3600,
        "event_time_source": "user",
        "repeat_mode": "once",
        "creation_time": 1400000000,
        "location_id": 0,
        "location_name": None,
        "latitude": "",
        "longitude": "",
        "event_id": 0,
        "trigger_message_id": "",
        "note": "",
        "timezone_id": 0,
        "end_time": 0,
        "list_id": 0,
        "payload_id": 0,
        "cu_app": "",
        "location_sharing_subtype": "",
        "reminder_notif_param": [],
        "workplace_meeting_id": "",
        "genie_fbid": 0,
        "galaxy": "",
        "oid": 1111,
        "type": 8128,
        "is_active": True,
        "location_address": None,
        "event_members": {
            "1234": "INVITED",
            "2356": "INVITED",
            "3456": "DECLINED",
            "4567": "GOING",
        },
    }
    plan = Plan(
        time=datetime.datetime(2017, 7, 14, 2, 40, tzinfo=datetime.timezone.utc),
        title="abc",
        location="",
        location_id="",
    )
    plan.uid = 1111
    plan.author_id = 1234
    plan.guests = {
        "1234": GuestStatus.INVITED,
        "2356": GuestStatus.INVITED,
        "3456": GuestStatus.DECLINED,
        "4567": GuestStatus.GOING,
    }
    assert plan == Plan._from_fetch(data)


def test_plan_from_graphql():
    data = {
        "id": "1111",
        "lightweight_event_creator": {"id": "1234"},
        "time": 1500000000,
        "lightweight_event_type": "EVENT",
        "location_name": None,
        "location_coordinates": None,
        "location_page": None,
        "lightweight_event_status": "CREATED",
        "note": "",
        "repeat_mode": "ONCE",
        "event_title": "abc",
        "trigger_message": None,
        "seconds_to_notify_before": 3600,
        "allows_rsvp": True,
        "related_event": None,
        "event_reminder_members": {
            "edges": [
                {"node": {"id": "1234"}, "guest_list_state": "INVITED"},
                {"node": {"id": "2356"}, "guest_list_state": "INVITED"},
                {"node": {"id": "3456"}, "guest_list_state": "DECLINED"},
                {"node": {"id": "4567"}, "guest_list_state": "GOING"},
            ]
        },
    }
    plan = Plan(
        time=datetime.datetime(2017, 7, 14, 2, 40, tzinfo=datetime.timezone.utc),
        title="abc",
        location="",
        location_id="",
    )
    plan.uid = "1111"
    plan.author_id = "1234"
    plan.guests = {
        "1234": GuestStatus.INVITED,
        "2356": GuestStatus.INVITED,
        "3456": GuestStatus.DECLINED,
        "4567": GuestStatus.GOING,
    }
    assert plan == Plan._from_graphql(data)
