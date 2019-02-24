# -*- coding: UTF-8 -*-
from __future__ import unicode_literals

import attr
from ._attachment import Attachment


@attr.s(cmp=False, init=False)
class Sticker(Attachment):
    """Represents a Facebook sticker that has been sent to a thread as an attachment"""

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
    #: The amount of frames present in the spritemap pr. coloumn
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
