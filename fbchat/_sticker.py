# -*- coding: UTF-8 -*-
from __future__ import unicode_literals

import attr
from ._attachment import Attachment


@attr.s(cmp=False, init=False)
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

    #: URL to the sticker's image
    url = attr.ib(None)
    #: Width of the sticker
    width = attr.ib(None)
    #: Height of the sticker
    height = attr.ib(None)
    #: The sticker's label/name
    label = attr.ib(None)

    def __init__(self, uid=None):
        super(Sticker, self).__init__(uid=uid)

    @classmethod
    def _from_graphql(cls, data):
        if not data:
            return None
        self = cls(uid=data["id"])
        if data.get("pack"):
            self.pack = data["pack"].get("id")
        if data.get("sprite_image"):
            self.is_animated = True
            self.medium_sprite_image = data["sprite_image"].get("uri")
            self.large_sprite_image = data["sprite_image_2x"].get("uri")
            self.frames_per_row = data.get("frames_per_row")
            self.frames_per_col = data.get("frames_per_column")
            self.frame_rate = data.get("frame_rate")
        self.url = data.get("url")
        self.width = data.get("width")
        self.height = data.get("height")
        if data.get("label"):
            self.label = data["label"]
        return self
