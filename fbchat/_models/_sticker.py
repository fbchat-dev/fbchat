import attr
from . import Image, Attachment
from .._common import attrs_default

from typing import Optional


@attrs_default
class Sticker(Attachment):
    """Represents a Facebook sticker that has been sent to a thread as an attachment."""

    #: The sticker-pack's ID
    pack = attr.ib(None, type=Optional[str])
    #: Whether the sticker is animated
    is_animated = attr.ib(False, type=bool)

    # If the sticker is animated, the following should be present
    #: URL to a medium spritemap
    medium_sprite_image = attr.ib(None, type=Optional[str])
    #: URL to a large spritemap
    large_sprite_image = attr.ib(None, type=Optional[str])
    #: The amount of frames present in the spritemap pr. row
    frames_per_row = attr.ib(None, type=Optional[int])
    #: The amount of frames present in the spritemap pr. column
    frames_per_col = attr.ib(None, type=Optional[int])
    #: The total amount of frames in the spritemap
    frame_count = attr.ib(None, type=Optional[int])
    #: The frame rate the spritemap is intended to be played in
    frame_rate = attr.ib(None, type=Optional[int])

    #: The sticker's image
    image = attr.ib(None, type=Optional[Image])
    #: The sticker's label/name
    label = attr.ib(None, type=Optional[str])

    @classmethod
    def _from_graphql(cls, data):
        if not data:
            return None

        return cls(
            id=data["id"],
            pack=data["pack"].get("id") if data.get("pack") else None,
            is_animated=bool(data.get("sprite_image")),
            medium_sprite_image=data["sprite_image"].get("uri")
            if data.get("sprite_image")
            else None,
            large_sprite_image=data["sprite_image_2x"].get("uri")
            if data.get("sprite_image_2x")
            else None,
            frames_per_row=data.get("frames_per_row"),
            frames_per_col=data.get("frames_per_column"),
            frame_count=data.get("frame_count"),
            frame_rate=data.get("frame_rate"),
            image=Image._from_url_or_none(data),
            label=data["label"] if data.get("label") else None,
        )
