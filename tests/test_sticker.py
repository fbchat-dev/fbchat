import pytest
from fbchat._sticker import Sticker


def test_from_graphql_none():
    assert None == Sticker._from_graphql(None)


def test_from_graphql_minimal():
    assert Sticker(uid=1) == Sticker._from_graphql({"id": 1})


def test_from_graphql_normal():
    assert Sticker(
        uid="369239383222810",
        pack="227877430692340",
        is_animated=False,
        medium_sprite_image=None,
        large_sprite_image=None,
        frames_per_row=None,
        frames_per_col=None,
        frame_rate=None,
        url="https://scontent-arn2-1.xx.fbcdn.net/v/redacted.png",
        width=274,
        height=274,
        label="Like, thumbs up",
    ) == Sticker._from_graphql(
        {
            "id": "369239383222810",
            "pack": {"id": "227877430692340"},
            "label": "Like, thumbs up",
            "frame_count": 1,
            "frame_rate": 83,
            "frames_per_row": 1,
            "frames_per_column": 1,
            "sprite_image_2x": None,
            "sprite_image": None,
            "padded_sprite_image": None,
            "padded_sprite_image_2x": None,
            "url": "https://scontent-arn2-1.xx.fbcdn.net/v/redacted.png",
            "height": 274,
            "width": 274,
        }
    )


def test_from_graphql_animated():
    assert Sticker(
        uid="144885035685763",
        pack="350357561732812",
        is_animated=True,
        medium_sprite_image="https://scontent-arn2-1.xx.fbcdn.net/v/redacted2.png",
        large_sprite_image="https://scontent-arn2-1.fbcdn.net/v/redacted3.png",
        frames_per_row=2,
        frames_per_col=2,
        frame_rate=142,
        url="https://scontent-arn2-1.fbcdn.net/v/redacted1.png",
        width=240,
        height=293,
        label="Love, cat with heart",
    ) == Sticker._from_graphql(
        {
            "id": "144885035685763",
            "pack": {"id": "350357561732812"},
            "label": "Love, cat with heart",
            "frame_count": 4,
            "frame_rate": 142,
            "frames_per_row": 2,
            "frames_per_column": 2,
            "sprite_image_2x": {
                "uri": "https://scontent-arn2-1.fbcdn.net/v/redacted3.png"
            },
            "sprite_image": {
                "uri": "https://scontent-arn2-1.xx.fbcdn.net/v/redacted2.png"
            },
            "padded_sprite_image": {
                "uri": "https://scontent-arn2-1.xx.fbcdn.net/v/unused1.png"
            },
            "padded_sprite_image_2x": {
                "uri": "https://scontent-arn2-1.xx.fbcdn.net/v/unused2.png"
            },
            "url": "https://scontent-arn2-1.fbcdn.net/v/redacted1.png",
            "height": 293,
            "width": 240,
        }
    )
