# -*- coding: UTF-8 -*-
from __future__ import unicode_literals

import attr
from ._attachment import Attachment


@attr.s(cmp=False)
class FileAttachment(Attachment):
    """Represents a file that has been sent as a Facebook attachment"""

    #: Url where you can download the file
    url = attr.ib(None)
    #: Size of the file in bytes
    size = attr.ib(None)
    #: Name of the file
    name = attr.ib(None)
    #: Whether Facebook determines that this file may be harmful
    is_malicious = attr.ib(None)

    # Put here for backwards compatibility, so that the init argument order is preserved
    uid = attr.ib(None)


@attr.s(cmp=False)
class AudioAttachment(Attachment):
    """Represents an audio file that has been sent as a Facebook attachment"""

    #: Name of the file
    filename = attr.ib(None)
    #: Url of the audio file
    url = attr.ib(None)
    #: Duration of the audioclip in milliseconds
    duration = attr.ib(None)
    #: Audio type
    audio_type = attr.ib(None)

    # Put here for backwards compatibility, so that the init argument order is preserved
    uid = attr.ib(None)


@attr.s(cmp=False, init=False)
class ImageAttachment(Attachment):
    """Represents an image that has been sent as a Facebook attachment

    To retrieve the full image url, use: :func:`fbchat.Client.fetchImageUrl`, and pass
    it the uid of the image attachment
    """

    #: The extension of the original image (eg. 'png')
    original_extension = attr.ib(None)
    #: Width of original image
    width = attr.ib(None, converter=lambda x: None if x is None else int(x))
    #: Height of original image
    height = attr.ib(None, converter=lambda x: None if x is None else int(x))

    #: Whether the image is animated
    is_animated = attr.ib(None)

    #: URL to a thumbnail of the image
    thumbnail_url = attr.ib(None)

    #: URL to a medium preview of the image
    preview_url = attr.ib(None)
    #: Width of the medium preview image
    preview_width = attr.ib(None)
    #: Height of the medium preview image
    preview_height = attr.ib(None)

    #: URL to a large preview of the image
    large_preview_url = attr.ib(None)
    #: Width of the large preview image
    large_preview_width = attr.ib(None)
    #: Height of the large preview image
    large_preview_height = attr.ib(None)

    #: URL to an animated preview of the image (eg. for gifs)
    animated_preview_url = attr.ib(None)
    #: Width of the animated preview image
    animated_preview_width = attr.ib(None)
    #: Height of the animated preview image
    animated_preview_height = attr.ib(None)

    def __init__(
        self,
        original_extension=None,
        width=None,
        height=None,
        is_animated=None,
        thumbnail_url=None,
        preview=None,
        large_preview=None,
        animated_preview=None,
        **kwargs
    ):
        super(ImageAttachment, self).__init__(**kwargs)
        self.original_extension = original_extension
        if width is not None:
            width = int(width)
        self.width = width
        if height is not None:
            height = int(height)
        self.height = height
        self.is_animated = is_animated
        self.thumbnail_url = thumbnail_url

        if preview is None:
            preview = {}
        self.preview_url = preview.get("uri")
        self.preview_width = preview.get("width")
        self.preview_height = preview.get("height")

        if large_preview is None:
            large_preview = {}
        self.large_preview_url = large_preview.get("uri")
        self.large_preview_width = large_preview.get("width")
        self.large_preview_height = large_preview.get("height")

        if animated_preview is None:
            animated_preview = {}
        self.animated_preview_url = animated_preview.get("uri")
        self.animated_preview_width = animated_preview.get("width")
        self.animated_preview_height = animated_preview.get("height")


@attr.s(cmp=False, init=False)
class VideoAttachment(Attachment):
    """Represents a video that has been sent as a Facebook attachment"""

    #: Size of the original video in bytes
    size = attr.ib(None)
    #: Width of original video
    width = attr.ib(None)
    #: Height of original video
    height = attr.ib(None)
    #: Length of video in milliseconds
    duration = attr.ib(None)
    #: URL to very compressed preview video
    preview_url = attr.ib(None)

    #: URL to a small preview image of the video
    small_image_url = attr.ib(None)
    #: Width of the small preview image
    small_image_width = attr.ib(None)
    #: Height of the small preview image
    small_image_height = attr.ib(None)

    #: URL to a medium preview image of the video
    medium_image_url = attr.ib(None)
    #: Width of the medium preview image
    medium_image_width = attr.ib(None)
    #: Height of the medium preview image
    medium_image_height = attr.ib(None)

    #: URL to a large preview image of the video
    large_image_url = attr.ib(None)
    #: Width of the large preview image
    large_image_width = attr.ib(None)
    #: Height of the large preview image
    large_image_height = attr.ib(None)

    def __init__(
        self,
        size=None,
        width=None,
        height=None,
        duration=None,
        preview_url=None,
        small_image=None,
        medium_image=None,
        large_image=None,
        **kwargs
    ):
        super(VideoAttachment, self).__init__(**kwargs)
        self.size = size
        self.width = width
        self.height = height
        self.duration = duration
        self.preview_url = preview_url

        if small_image is None:
            small_image = {}
        self.small_image_url = small_image.get("uri")
        self.small_image_width = small_image.get("width")
        self.small_image_height = small_image.get("height")

        if medium_image is None:
            medium_image = {}
        self.medium_image_url = medium_image.get("uri")
        self.medium_image_width = medium_image.get("width")
        self.medium_image_height = medium_image.get("height")

        if large_image is None:
            large_image = {}
        self.large_image_url = large_image.get("uri")
        self.large_image_width = large_image.get("width")
        self.large_image_height = large_image.get("height")
