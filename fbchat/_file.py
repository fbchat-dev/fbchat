# -*- coding: UTF-8 -*-
from __future__ import unicode_literals

from ._attachment import Attachment


class FileAttachment(Attachment):
    #: Url where you can download the file
    url = None
    #: Size of the file in bytes
    size = None
    #: Name of the file
    name = None
    #: Whether Facebook determines that this file may be harmful
    is_malicious = None

    def __init__(self, url=None, size=None, name=None, is_malicious=None, **kwargs):
        """Represents a file that has been sent as a Facebook attachment"""
        super(FileAttachment, self).__init__(**kwargs)
        self.url = url
        self.size = size
        self.name = name
        self.is_malicious = is_malicious


class AudioAttachment(Attachment):
    #: Name of the file
    filename = None
    #: Url of the audio file
    url = None
    #: Duration of the audioclip in milliseconds
    duration = None
    #: Audio type
    audio_type = None

    def __init__(
        self, filename=None, url=None, duration=None, audio_type=None, **kwargs
    ):
        """Represents an audio file that has been sent as a Facebook attachment"""
        super(AudioAttachment, self).__init__(**kwargs)
        self.filename = filename
        self.url = url
        self.duration = duration
        self.audio_type = audio_type


class ImageAttachment(Attachment):
    #: The extension of the original image (eg. 'png')
    original_extension = None
    #: Width of original image
    width = None
    #: Height of original image
    height = None

    #: Whether the image is animated
    is_animated = None

    #: URL to a thumbnail of the image
    thumbnail_url = None

    #: URL to a medium preview of the image
    preview_url = None
    #: Width of the medium preview image
    preview_width = None
    #: Height of the medium preview image
    preview_height = None

    #: URL to a large preview of the image
    large_preview_url = None
    #: Width of the large preview image
    large_preview_width = None
    #: Height of the large preview image
    large_preview_height = None

    #: URL to an animated preview of the image (eg. for gifs)
    animated_preview_url = None
    #: Width of the animated preview image
    animated_preview_width = None
    #: Height of the animated preview image
    animated_preview_height = None

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
        """
        Represents an image that has been sent as a Facebook attachment
        To retrieve the full image url, use: :func:`fbchat.Client.fetchImageUrl`,
        and pass it the uid of the image attachment
        """
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


class VideoAttachment(Attachment):
    #: Size of the original video in bytes
    size = None
    #: Width of original video
    width = None
    #: Height of original video
    height = None
    #: Length of video in milliseconds
    duration = None
    #: URL to very compressed preview video
    preview_url = None

    #: URL to a small preview image of the video
    small_image_url = None
    #: Width of the small preview image
    small_image_width = None
    #: Height of the small preview image
    small_image_height = None

    #: URL to a medium preview image of the video
    medium_image_url = None
    #: Width of the medium preview image
    medium_image_width = None
    #: Height of the medium preview image
    medium_image_height = None

    #: URL to a large preview image of the video
    large_image_url = None
    #: Width of the large preview image
    large_image_width = None
    #: Height of the large preview image
    large_image_height = None

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
        """Represents a video that has been sent as a Facebook attachment"""
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
