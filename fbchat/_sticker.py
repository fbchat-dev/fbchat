# -*- coding: UTF-8 -*-
from __future__ import unicode_literals

from ._attachment import Attachment


class Sticker(Attachment):
    #: The sticker-pack's ID
    pack = None
    #: Whether the sticker is animated
    is_animated = False

    # If the sticker is animated, the following should be present
    #: URL to a medium spritemap
    medium_sprite_image = None
    #: URL to a large spritemap
    large_sprite_image = None
    #: The amount of frames present in the spritemap pr. row
    frames_per_row = None
    #: The amount of frames present in the spritemap pr. coloumn
    frames_per_col = None
    #: The frame rate the spritemap is intended to be played in
    frame_rate = None

    #: URL to the sticker's image
    url = None
    #: Width of the sticker
    width = None
    #: Height of the sticker
    height = None
    #: The sticker's label/name
    label = None

    def __init__(self, *args, **kwargs):
        """Represents a Facebook sticker that has been sent to a Facebook thread as an attachment"""
        super(Sticker, self).__init__(*args, **kwargs)
