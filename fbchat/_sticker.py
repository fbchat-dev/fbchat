import attr
from ._core import Image
from ._attachment import Attachment


@attr.s
class Sticker(Attachment):
    """Represents a Facebook sticker that has been sent to a thread as an attachment."""

    #: The sticker-pack's ID
    pack = attr.ib(None)
    #: Whether the sticker is animated
    is_animated = attr.ib(False)

    # If the sticker is animated, the following should be present
    #: URL to a medium spritemap
    medium_sprite_image = attr.ib(None)
    #: URL to a large spritemap
    large_sprite_image = attr.ib(None)
    #: The amount of frames present in the spritemap pr. row
    frames_per_row = attr.ib(None)
    #: The amount of frames present in the spritemap pr. column
    frames_per_col = attr.ib(None)
    #: The frame rate the spritemap is intended to be played in
    frame_rate = attr.ib(None)

    #: The sticker's image
    image = attr.ib(None)
    #: The sticker's label/name
    label = attr.ib(None)

    @classmethod
    def _from_graphql(cls, data):
        if not data:
            return None

        return cls(
            uid=data["id"],
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
            frame_rate=data.get("frame_rate"),
            image=Image._from_url_or_none(data),
            label=data["label"] if data.get("label") else None,
        )
