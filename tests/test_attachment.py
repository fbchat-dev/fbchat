import pytest
import fbchat
from fbchat._attachment import UnsentMessage, ShareAttachment


def test_parse_unsent_message():
    data = {
        "legacy_attachment_id": "ee.mid.$xyz",
        "story_attachment": {
            "description": {"text": "You removed a message"},
            "media": None,
            "source": None,
            "style_list": ["globally_deleted_message_placeholder", "fallback"],
            "title_with_entities": {"text": ""},
            "properties": [],
            "url": None,
            "deduplication_key": "deadbeef123",
            "action_links": [],
            "messaging_attribution": None,
            "messenger_call_to_actions": [],
            "xma_layout_info": None,
            "target": None,
            "subattachments": [],
        },
        "genie_attachment": {"genie_message": None},
    }
    assert UnsentMessage(
        uid="ee.mid.$xyz"
    ) == fbchat._message.graphql_to_extensible_attachment(data)


def test_share_from_graphql_minimal():
    data = {
        "target": {},
        "url": "a.com",
        "title_with_entities": {"text": "a.com"},
        "subattachments": [],
    }
    assert ShareAttachment(
        url="a.com", original_url="a.com", title="a.com"
    ) == ShareAttachment._from_graphql(data)


def test_share_from_graphql_link():
    data = {
        "description": {"text": ""},
        "media": {
            "animated_image": None,
            "image": None,
            "playable_duration_in_ms": 0,
            "is_playable": False,
            "playable_url": None,
        },
        "source": {"text": "a.com"},
        "style_list": ["share", "fallback"],
        "title_with_entities": {"text": "a.com"},
        "properties": [],
        "url": "http://l.facebook.com/l.php?u=http%3A%2F%2Fa.com%2F&h=def&s=1",
        "deduplication_key": "ee.mid.$xyz",
        "action_links": [{"title": "About this website", "url": None}],
        "messaging_attribution": None,
        "messenger_call_to_actions": [],
        "xma_layout_info": None,
        "target": {"__typename": "ExternalUrl"},
        "subattachments": [],
    }
    assert ShareAttachment(
        author=None,
        url="http://l.facebook.com/l.php?u=http%3A%2F%2Fa.com%2F&h=def&s=1",
        original_url="http://a.com/",
        title="a.com",
        description="",
        source="a.com",
        image_url=None,
        original_image_url=None,
        image_width=None,
        image_height=None,
        attachments=[],
        uid="ee.mid.$xyz",
    ) == ShareAttachment._from_graphql(data)


def test_share_from_graphql_link_with_image():
    data = {
        "description": {
            "text": (
                "Create an account or log in to Facebook."
                " Connect with friends, family and other people you know."
                " Share photos and videos, send messages and get updates."
            )
        },
        "media": {
            "animated_image": None,
            "image": {
                "uri": "https://www.facebook.com/rsrc.php/v3/x.png",
                "height": 325,
                "width": 325,
            },
            "playable_duration_in_ms": 0,
            "is_playable": False,
            "playable_url": None,
        },
        "source": None,
        "style_list": ["share", "fallback"],
        "title_with_entities": {"text": "Facebook – log in or sign up"},
        "properties": [],
        "url": "http://facebook.com/",
        "deduplication_key": "deadbeef123",
        "action_links": [],
        "messaging_attribution": None,
        "messenger_call_to_actions": [],
        "xma_layout_info": None,
        "target": {"__typename": "ExternalUrl"},
        "subattachments": [],
    }
    assert ShareAttachment(
        author=None,
        url="http://facebook.com/",
        original_url="http://facebook.com/",
        title="Facebook – log in or sign up",
        description=(
            "Create an account or log in to Facebook."
            " Connect with friends, family and other people you know."
            " Share photos and videos, send messages and get updates."
        ),
        source=None,
        image_url="https://www.facebook.com/rsrc.php/v3/x.png",
        original_image_url="https://www.facebook.com/rsrc.php/v3/x.png",
        image_width=325,
        image_height=325,
        attachments=[],
        uid="deadbeef123",
    ) == ShareAttachment._from_graphql(data)


def test_share_from_graphql_video():
    data = {
        "description": {
            "text": (
                "Rick Astley's official music video for “Never Gonna Give You Up”"
                " Listen to Rick Astley: https://RickAstley.lnk.to/_listenYD"
                " Subscribe to the official Rick As..."
            )
        },
        "media": {
            "animated_image": None,
            "image": {
                "uri": (
                    "https://external-arn2-1.xx.fbcdn.net/safe_image.php?d=xyz123"
                    "&w=960&h=540&url=https%3A%2F%2Fi.ytimg.com%2Fvi%2FdQw4w9WgXcQ"
                    "%2Fmaxresdefault.jpg&sx=0&sy=0&sw=1280&sh=720&_nc_hash=abc123"
                ),
                "height": 540,
                "width": 960,
            },
            "playable_duration_in_ms": 0,
            "is_playable": True,
            "playable_url": "https://www.youtube.com/embed/dQw4w9WgXcQ?autoplay=1",
        },
        "source": {"text": "youtube.com"},
        "style_list": ["share", "fallback"],
        "title_with_entities": {
            "text": "Rick Astley - Never Gonna Give You Up (Video)"
        },
        "properties": [
            {"key": "width", "value": {"text": "1280"}},
            {"key": "height", "value": {"text": "720"}},
        ],
        "url": "https://l.facebook.com/l.php?u=https%3A%2F%2Fyoutu.be%2FdQw4w9WgXcQ",
        "deduplication_key": "ee.mid.$gAAT4Sw1WSGhzQ9uRWVtEpZHZ8ZPV",
        "action_links": [{"title": "About this website", "url": None}],
        "messaging_attribution": None,
        "messenger_call_to_actions": [],
        "xma_layout_info": None,
        "target": {"__typename": "ExternalUrl"},
        "subattachments": [],
    }
    assert ShareAttachment(
        author=None,
        url="https://l.facebook.com/l.php?u=https%3A%2F%2Fyoutu.be%2FdQw4w9WgXcQ",
        original_url="https://youtu.be/dQw4w9WgXcQ",
        title="Rick Astley - Never Gonna Give You Up (Video)",
        description=(
            "Rick Astley's official music video for “Never Gonna Give You Up”"
            " Listen to Rick Astley: https://RickAstley.lnk.to/_listenYD"
            " Subscribe to the official Rick As..."
        ),
        source="youtube.com",
        image_url=(
            "https://external-arn2-1.xx.fbcdn.net/safe_image.php?d=xyz123"
            "&w=960&h=540&url=https%3A%2F%2Fi.ytimg.com%2Fvi%2FdQw4w9WgXcQ"
            "%2Fmaxresdefault.jpg&sx=0&sy=0&sw=1280&sh=720&_nc_hash=abc123"
        ),
        original_image_url="https://i.ytimg.com/vi/dQw4w9WgXcQ/maxresdefault.jpg",
        image_width=960,
        image_height=540,
        attachments=[],
        uid="ee.mid.$gAAT4Sw1WSGhzQ9uRWVtEpZHZ8ZPV",
    ) == ShareAttachment._from_graphql(data)
