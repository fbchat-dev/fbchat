import pytest
import datetime
from fbchat._location import LocationAttachment, LiveLocationAttachment


def test_location_attachment_from_graphql():
    data = {
        "description": {"text": ""},
        "media": {
            "animated_image": None,
            "image": {
                "uri": "https://external-arn2-1.xx.fbcdn.net/static_map.php?v=1020&osm_provider=2&size=545x280&zoom=15&markers=55.40000000%2C12.43220000&language=en",
                "height": 280,
                "width": 545,
            },
            "playable_duration_in_ms": 0,
            "is_playable": False,
            "playable_url": None,
        },
        "source": None,
        "style_list": ["message_location", "fallback"],
        "title_with_entities": {"text": "Your location"},
        "properties": [
            {"key": "width", "value": {"text": "545"}},
            {"key": "height", "value": {"text": "280"}},
        ],
        "url": "https://l.facebook.com/l.php?u=https%3A%2F%2Fwww.bing.com%2Fmaps%2Fdefault.aspx%3Fv%3D2%26pc%3DFACEBK%26mid%3D8100%26where1%3D55.4%252C%2B12.4322%26FORM%3DFBKPL1%26mkt%3Den-GB&h=a&s=1",
        "deduplication_key": "400828513928715",
        "action_links": [],
        "messaging_attribution": None,
        "messenger_call_to_actions": [],
        "xma_layout_info": None,
        "target": {"__typename": "MessageLocation"},
        "subattachments": [],
    }
    expected = LocationAttachment(latitude=55.4, longitude=12.4322, uid=400828513928715)
    expected.image_url = "https://external-arn2-1.xx.fbcdn.net/static_map.php?v=1020&osm_provider=2&size=545x280&zoom=15&markers=55.40000000%2C12.43220000&language=en"
    expected.image_width = 545
    expected.image_height = 280
    expected.url = "https://l.facebook.com/l.php?u=https%3A%2F%2Fwww.bing.com%2Fmaps%2Fdefault.aspx%3Fv%3D2%26pc%3DFACEBK%26mid%3D8100%26where1%3D55.4%252C%2B12.4322%26FORM%3DFBKPL1%26mkt%3Den-GB&h=a&s=1"
    assert expected == LocationAttachment._from_graphql(data)


@pytest.mark.skip(reason="need to gather test data")
def test_live_location_from_pull():
    data = ...
    assert LiveLocationAttachment(...) == LiveLocationAttachment._from_pull(data)


def test_live_location_from_graphql_expired():
    data = {
        "description": {"text": "Last update 4 Jan"},
        "media": None,
        "source": None,
        "style_list": ["message_live_location", "fallback"],
        "title_with_entities": {"text": "Location-sharing ended"},
        "properties": [],
        "url": "https://www.facebook.com/",
        "deduplication_key": "2254535444791641",
        "action_links": [],
        "messaging_attribution": None,
        "messenger_call_to_actions": [],
        "target": {
            "__typename": "MessageLiveLocation",
            "live_location_id": "2254535444791641",
            "is_expired": True,
            "expiration_time": 1546626345,
            "sender": {"id": "100007056224713"},
            "coordinate": None,
            "location_title": None,
            "sender_destination": None,
            "stop_reason": "CANCELED",
        },
        "subattachments": [],
    }
    expected = LiveLocationAttachment(
        uid=2254535444791641,
        name="Location-sharing ended",
        expires_at=datetime.datetime(
            2019, 1, 4, 18, 25, 45, tzinfo=datetime.timezone.utc
        ),
        is_expired=True,
    )
    expected.url = "https://www.facebook.com/"
    assert expected == LiveLocationAttachment._from_graphql(data)


@pytest.mark.skip(reason="need to gather test data")
def test_live_location_from_graphql():
    data = ...
    assert LiveLocationAttachment(...) == LiveLocationAttachment._from_graphql(data)
