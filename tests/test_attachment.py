import pytest
import datetime
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


def test_share_with_image_subattachment():
    data = {
        "description": {"text": "Abc"},
        "media": {
            "animated_image": None,
            "image": {
                "uri": "https://scontent-arn2-1.xx.fbcdn.net/v/t1.0-9/1.jpg",
                "height": 960,
                "width": 720,
            },
            "playable_duration_in_ms": 0,
            "is_playable": False,
            "playable_url": None,
        },
        "source": {"text": "Def"},
        "style_list": ["attached_story", "fallback"],
        "title_with_entities": {"text": ""},
        "properties": [],
        "url": "https://www.facebook.com/groups/11223344/permalink/1234/",
        "deduplication_key": "deadbeef123",
        "action_links": [
            {"title": None, "url": None},
            {"title": None, "url": "https://www.facebook.com/groups/11223344/"},
            {
                "title": "Report Post to Admin",
                "url": "https://www.facebook.com/groups/11223344/members/",
            },
        ],
        "messaging_attribution": None,
        "messenger_call_to_actions": [],
        "xma_layout_info": None,
        "target": {
            "__typename": "Story",
            "title": None,
            "description": {"text": "Abc"},
            "actors": [
                {
                    "__typename": "User",
                    "name": "Def",
                    "id": "1111",
                    "short_name": "Def",
                    "url": "https://www.facebook.com/some-user",
                    "profile_picture": {
                        "uri": "https://scontent-arn2-1.xx.fbcdn.net/v/t1.0-1/c123.123.123.123a/s50x50/img.jpg",
                        "height": 50,
                        "width": 50,
                    },
                }
            ],
            "to": {
                "__typename": "Group",
                "name": "Some group",
                "url": "https://www.facebook.com/groups/11223344/",
            },
            "attachments": [
                {
                    "url": "https://www.facebook.com/photo.php?fbid=4321&set=gm.1234&type=3",
                    "media": {
                        "is_playable": False,
                        "image": {
                            "uri": "https://scontent-arn2-1.xx.fbcdn.net/v/t1.0-9/1.jpg",
                            "height": 960,
                            "width": 720,
                        },
                    },
                }
            ],
            "attached_story": None,
        },
        "subattachments": [
            {
                "description": {"text": "Abc"},
                "media": {
                    "animated_image": None,
                    "image": {
                        "uri": "https://scontent-arn2-1.xx.fbcdn.net/v/t1.0-9/1.jpg",
                        "height": 960,
                        "width": 720,
                    },
                    "playable_duration_in_ms": 0,
                    "is_playable": False,
                    "playable_url": None,
                },
                "source": None,
                "style_list": ["photo", "games_app", "fallback"],
                "title_with_entities": {"text": ""},
                "properties": [
                    {"key": "photoset_reference_token", "value": {"text": "gm.1234"}},
                    {"key": "layout_x", "value": {"text": "0"}},
                    {"key": "layout_y", "value": {"text": "0"}},
                    {"key": "layout_w", "value": {"text": "0"}},
                    {"key": "layout_h", "value": {"text": "0"}},
                ],
                "url": "https://www.facebook.com/photo.php?fbid=4321&set=gm.1234&type=3",
                "deduplication_key": "deadbeef456",
                "action_links": [],
                "messaging_attribution": None,
                "messenger_call_to_actions": [],
                "xma_layout_info": None,
                "target": {"__typename": "Photo"},
            }
        ],
    }
    assert ShareAttachment(
        author="1111",
        url="https://www.facebook.com/groups/11223344/permalink/1234/",
        original_url="https://www.facebook.com/groups/11223344/permalink/1234/",
        title="",
        description="Abc",
        source="Def",
        image_url="https://scontent-arn2-1.xx.fbcdn.net/v/t1.0-9/1.jpg",
        original_image_url="https://scontent-arn2-1.xx.fbcdn.net/v/t1.0-9/1.jpg",
        image_width=720,
        image_height=960,
        attachments=[None],
        uid="deadbeef123",
    ) == ShareAttachment._from_graphql(data)


def test_share_with_video_subattachment():
    data = {
        "description": {"text": "Abc"},
        "media": {
            "animated_image": None,
            "image": {
                "uri": "https://scontent-arn2-1.xx.fbcdn.net/v/t15.5256-10/p180x540/1.jpg",
                "height": 540,
                "width": 960,
            },
            "playable_duration_in_ms": 24469,
            "is_playable": True,
            "playable_url": "https://video-arn2-1.xx.fbcdn.net/v/t42.9040-2/vid.mp4",
        },
        "source": {"text": "Def"},
        "style_list": ["attached_story", "fallback"],
        "title_with_entities": {"text": ""},
        "properties": [],
        "url": "https://www.facebook.com/groups/11223344/permalink/1234/",
        "deduplication_key": "deadbeef123",
        "action_links": [
            {"title": None, "url": None},
            {"title": None, "url": "https://www.facebook.com/groups/11223344/"},
            {"title": None, "url": None},
            {"title": "A watch party is currently playing this video.", "url": None},
        ],
        "messaging_attribution": None,
        "messenger_call_to_actions": [],
        "xma_layout_info": None,
        "target": {
            "__typename": "Story",
            "title": None,
            "description": {"text": "Abc"},
            "actors": [
                {
                    "__typename": "User",
                    "name": "Def",
                    "id": "1111",
                    "short_name": "Def",
                    "url": "https://www.facebook.com/some-user",
                    "profile_picture": {
                        "uri": "https://scontent-arn2-1.xx.fbcdn.net/v/t1.0-1/c1.0.50.50a/p50x50/profile.jpg",
                        "height": 50,
                        "width": 50,
                    },
                }
            ],
            "to": {
                "__typename": "Group",
                "name": "Some group",
                "url": "https://www.facebook.com/groups/11223344/",
            },
            "attachments": [
                {
                    "url": "https://www.facebook.com/some-user/videos/2222/",
                    "media": {
                        "is_playable": True,
                        "image": {
                            "uri": "https://scontent-arn2-1.xx.fbcdn.net/v/t15.5256-10/p180x540/1.jpg",
                            "height": 540,
                            "width": 960,
                        },
                    },
                }
            ],
            "attached_story": None,
        },
        "subattachments": [
            {
                "description": None,
                "media": {
                    "animated_image": None,
                    "image": {
                        "uri": "https://scontent-arn2-1.xx.fbcdn.net/v/t15.5256-10/p180x540/1.jpg",
                        "height": 540,
                        "width": 960,
                    },
                    "playable_duration_in_ms": 24469,
                    "is_playable": True,
                    "playable_url": "https://video-arn2-1.xx.fbcdn.net/v/t42.9040-2/vid.mp4",
                },
                "source": None,
                "style_list": [
                    "video_autoplay",
                    "video_inline",
                    "video",
                    "games_app",
                    "fallback",
                ],
                "title_with_entities": {"text": ""},
                "properties": [
                    {
                        "key": "can_autoplay_result",
                        "value": {"text": "ugc_default_allowed"},
                    }
                ],
                "url": "https://www.facebook.com/some-user/videos/2222/",
                "deduplication_key": "deadbeef456",
                "action_links": [],
                "messaging_attribution": None,
                "messenger_call_to_actions": [],
                "xma_layout_info": None,
                "target": {
                    "__typename": "Video",
                    "video_id": "2222",
                    "video_messenger_cta_payload": None,
                },
            }
        ],
    }
    assert ShareAttachment(
        author="1111",
        url="https://www.facebook.com/groups/11223344/permalink/1234/",
        original_url="https://www.facebook.com/groups/11223344/permalink/1234/",
        title="",
        description="Abc",
        source="Def",
        image_url="https://scontent-arn2-1.xx.fbcdn.net/v/t15.5256-10/p180x540/1.jpg",
        original_image_url="https://scontent-arn2-1.xx.fbcdn.net/v/t15.5256-10/p180x540/1.jpg",
        image_width=960,
        image_height=540,
        attachments=[
            fbchat.VideoAttachment(
                uid="2222",
                duration=datetime.timedelta(seconds=24, microseconds=469000),
                preview_url="https://video-arn2-1.xx.fbcdn.net/v/t42.9040-2/vid.mp4",
                medium_image={
                    "uri": "https://scontent-arn2-1.xx.fbcdn.net/v/t15.5256-10/p180x540/1.jpg",
                    "width": 960,
                    "height": 540,
                },
            )
        ],
        uid="deadbeef123",
    ) == ShareAttachment._from_graphql(data)
