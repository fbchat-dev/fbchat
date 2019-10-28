import datetime
import fbchat
from fbchat._file import (
    FileAttachment,
    AudioAttachment,
    ImageAttachment,
    VideoAttachment,
    graphql_to_attachment,
    graphql_to_subattachment,
)


def test_imageattachment_from_list():
    data = {
        "__typename": "MessageImage",
        "id": "bWVzc2...",
        "legacy_attachment_id": "1234",
        "image": {"uri": "https://scontent-arn2-1.xx.fbcdn.net/v/s261x260/1.jpg"},
        "image1": {
            "height": 463,
            "width": 960,
            "uri": "https://scontent-arn2-1.xx.fbcdn.net/v/2.jpg",
        },
        "image2": {
            "height": 988,
            "width": 2048,
            "uri": "https://scontent-arn2-1.xx.fbcdn.net/v/s2048x2048/3.jpg",
        },
        "original_dimensions": {"x": 2833, "y": 1367},
        "photo_encodings": [],
    }
    assert ImageAttachment(
        uid="1234",
        width=2833,
        height=1367,
        thumbnail_url="https://scontent-arn2-1.xx.fbcdn.net/v/s261x260/1.jpg",
        preview={
            "uri": "https://scontent-arn2-1.xx.fbcdn.net/v/2.jpg",
            "width": 960,
            "height": 463,
        },
        large_preview={
            "uri": "https://scontent-arn2-1.xx.fbcdn.net/v/s2048x2048/3.jpg",
            "width": 2048,
            "height": 988,
        },
    ) == ImageAttachment._from_list({"node": data})


def test_videoattachment_from_list():
    data = {
        "__typename": "MessageVideo",
        "id": "bWVzc2...",
        "legacy_attachment_id": "1234",
        "image": {
            "uri": "https://scontent-arn2-1.xx.fbcdn.net/v/t15.3394-10/p261x260/1.jpg"
        },
        "image1": {
            "height": 368,
            "width": 640,
            "uri": "https://scontent-arn2-1.xx.fbcdn.net/v/t15.3394-10/2.jpg",
        },
        "image2": {
            "height": 368,
            "width": 640,
            "uri": "https://scontent-arn2-1.xx.fbcdn.net/v/t15.3394-10/3.jpg",
        },
        "original_dimensions": {"x": 640, "y": 368},
    }
    assert VideoAttachment(
        uid="1234",
        width=640,
        height=368,
        small_image={
            "uri": "https://scontent-arn2-1.xx.fbcdn.net/v/t15.3394-10/p261x260/1.jpg"
        },
        medium_image={
            "uri": "https://scontent-arn2-1.xx.fbcdn.net/v/t15.3394-10/2.jpg",
            "width": 640,
            "height": 368,
        },
        large_image={
            "uri": "https://scontent-arn2-1.xx.fbcdn.net/v/t15.3394-10/3.jpg",
            "width": 640,
            "height": 368,
        },
    ) == VideoAttachment._from_list({"node": data})


def test_graphql_to_attachment_empty():
    assert fbchat.Attachment() == graphql_to_attachment({"__typename": "Unknown"})


def test_graphql_to_attachment_simple():
    data = {"__typename": "Unknown", "legacy_attachment_id": "1234"}
    assert fbchat.Attachment(uid="1234") == graphql_to_attachment(data)


def test_graphql_to_attachment_file():
    data = {
        "__typename": "MessageFile",
        "attribution_app": None,
        "attribution_metadata": None,
        "filename": "file.txt",
        "url": "https://l.facebook.com/l.php?u=https%3A%2F%2Fcdn.fbsbx.com%2Fv%2Ffile.txt&h=AT1...&s=1",
        "content_type": "attach:text",
        "is_malicious": False,
        "message_file_fbid": "1234",
        "url_shimhash": "AT0...",
        "url_skipshim": True,
    }
    assert FileAttachment(
        uid="1234",
        url="https://l.facebook.com/l.php?u=https%3A%2F%2Fcdn.fbsbx.com%2Fv%2Ffile.txt&h=AT1...&s=1",
        size=None,
        name="file.txt",
        is_malicious=False,
    ) == graphql_to_attachment(data)


def test_graphql_to_attachment_audio():
    data = {
        "__typename": "MessageAudio",
        "attribution_app": None,
        "attribution_metadata": None,
        "filename": "audio.mp3",
        "playable_url": "https://cdn.fbsbx.com/v/audio.mp3?dl=1",
        "playable_duration_in_ms": 27745,
        "is_voicemail": False,
        "audio_type": "FILE_ATTACHMENT",
        "url_shimhash": "AT0...",
        "url_skipshim": True,
    }
    assert AudioAttachment(
        uid=None,
        filename="audio.mp3",
        url="https://cdn.fbsbx.com/v/audio.mp3?dl=1",
        duration=datetime.timedelta(seconds=27, microseconds=745000),
        audio_type="FILE_ATTACHMENT",
    ) == graphql_to_attachment(data)


def test_graphql_to_attachment_image1():
    data = {
        "__typename": "MessageImage",
        "attribution_app": None,
        "attribution_metadata": None,
        "filename": "image-1234",
        "preview": {
            "uri": "https://scontent-arn2-1.xx.fbcdn.net/v/1.png",
            "height": 128,
            "width": 128,
        },
        "large_preview": {
            "uri": "https://scontent-arn2-1.xx.fbcdn.net/v/2.png",
            "height": 128,
            "width": 128,
        },
        "thumbnail": {"uri": "https://scontent-arn2-1.xx.fbcdn.net/v/p50x50/3.png"},
        "photo_encodings": [],
        "legacy_attachment_id": "1234",
        "original_dimensions": {"x": 128, "y": 128},
        "original_extension": "png",
        "render_as_sticker": False,
        "blurred_image_uri": None,
    }
    assert ImageAttachment(
        uid="1234",
        original_extension="png",
        width=None,
        height=None,
        is_animated=False,
        thumbnail_url="https://scontent-arn2-1.xx.fbcdn.net/v/p50x50/3.png",
        preview={
            "uri": "https://scontent-arn2-1.xx.fbcdn.net/v/1.png",
            "width": 128,
            "height": 128,
        },
        large_preview={
            "uri": "https://scontent-arn2-1.xx.fbcdn.net/v/2.png",
            "width": 128,
            "height": 128,
        },
    ) == graphql_to_attachment(data)


def test_graphql_to_attachment_image2():
    data = {
        "__typename": "MessageAnimatedImage",
        "attribution_app": None,
        "attribution_metadata": None,
        "filename": "gif-1234",
        "animated_image": {
            "uri": "https://cdn.fbsbx.com/v/1.gif",
            "height": 128,
            "width": 128,
        },
        "legacy_attachment_id": "1234",
        "preview_image": {
            "uri": "https://cdn.fbsbx.com/v/1.gif",
            "height": 128,
            "width": 128,
        },
        "original_dimensions": {"x": 128, "y": 128},
    }
    assert ImageAttachment(
        uid="1234",
        original_extension="gif",
        width=None,
        height=None,
        is_animated=True,
        preview={"uri": "https://cdn.fbsbx.com/v/1.gif", "width": 128, "height": 128},
        animated_preview={
            "uri": "https://cdn.fbsbx.com/v/1.gif",
            "width": 128,
            "height": 128,
        },
    ) == graphql_to_attachment(data)


def test_graphql_to_attachment_video():
    data = {
        "__typename": "MessageVideo",
        "attribution_app": None,
        "attribution_metadata": None,
        "filename": "video-4321.mp4",
        "playable_url": "https://video-arn2-1.xx.fbcdn.net/v/video-4321.mp4",
        "chat_image": {
            "height": 96,
            "width": 168,
            "uri": "https://scontent-arn2-1.xx.fbcdn.net/v/s168x128/1.jpg",
        },
        "legacy_attachment_id": "1234",
        "video_type": "FILE_ATTACHMENT",
        "original_dimensions": {"x": 640, "y": 368},
        "playable_duration_in_ms": 6000,
        "large_image": {
            "height": 368,
            "width": 640,
            "uri": "https://scontent-arn2-1.xx.fbcdn.net/v/2.jpg",
        },
        "inbox_image": {
            "height": 260,
            "width": 452,
            "uri": "https://scontent-arn2-1.xx.fbcdn.net/v/p261x260/3.jpg",
        },
    }
    assert VideoAttachment(
        uid="1234",
        width=None,
        height=None,
        duration=datetime.timedelta(seconds=6),
        preview_url="https://video-arn2-1.xx.fbcdn.net/v/video-4321.mp4",
        small_image={
            "uri": "https://scontent-arn2-1.xx.fbcdn.net/v/s168x128/1.jpg",
            "width": 168,
            "height": 96,
        },
        medium_image={
            "uri": "https://scontent-arn2-1.xx.fbcdn.net/v/p261x260/3.jpg",
            "width": 452,
            "height": 260,
        },
        large_image={
            "uri": "https://scontent-arn2-1.xx.fbcdn.net/v/2.jpg",
            "width": 640,
            "height": 368,
        },
    ) == graphql_to_attachment(data)


def test_graphql_to_subattachment_empty():
    assert None is graphql_to_subattachment({})


def test_graphql_to_subattachment_image():
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
        "source": None,
        "style_list": ["photo", "games_app", "fallback"],
        "title_with_entities": {"text": ""},
        "properties": [
            {"key": "photoset_reference_token", "value": {"text": "gm.4321"}},
            {"key": "layout_x", "value": {"text": "0"}},
            {"key": "layout_y", "value": {"text": "0"}},
            {"key": "layout_w", "value": {"text": "0"}},
            {"key": "layout_h", "value": {"text": "0"}},
        ],
        "url": "https://www.facebook.com/photo.php?fbid=1234&set=gm.4321&type=3",
        "deduplication_key": "8334...",
        "action_links": [],
        "messaging_attribution": None,
        "messenger_call_to_actions": [],
        "xma_layout_info": None,
        "target": {"__typename": "Photo"},
    }
    assert None is graphql_to_subattachment(data)


def test_graphql_to_subattachment_video():
    data = {
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
            {"key": "can_autoplay_result", "value": {"text": "ugc_default_allowed"}}
        ],
        "url": "https://www.facebook.com/some-username/videos/1234/",
        "deduplication_key": "ddb7...",
        "action_links": [],
        "messaging_attribution": None,
        "messenger_call_to_actions": [],
        "xma_layout_info": None,
        "target": {
            "__typename": "Video",
            "video_id": "1234",
            "video_messenger_cta_payload": None,
        },
    }
    assert VideoAttachment(
        uid="1234",
        duration=datetime.timedelta(seconds=24, microseconds=469000),
        preview_url="https://video-arn2-1.xx.fbcdn.net/v/t42.9040-2/vid.mp4",
        medium_image={
            "uri": "https://scontent-arn2-1.xx.fbcdn.net/v/t15.5256-10/p180x540/1.jpg",
            "width": 960,
            "height": 540,
        },
    ) == graphql_to_subattachment(data)
