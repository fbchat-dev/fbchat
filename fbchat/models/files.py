# -*- coding: UTF-8 -*-

from __future__ import unicode_literals

import attr

from datetime import timedelta

from .core import Dimension


__all__ = ("File", "Audio", "Image", "AnimatedImage", "Video")


@attr.s(slots=True)
class File(object):
    """Represents a file / an attachment"""

    #: The unique identifier of the file
    id = attr.ib(type=int, converter=int)
    #: Name of the file
    name = attr.ib(type=str)
    #: The mimetype of the file
    mimetype = attr.ib(type=str)
    #: URL where you can download the file
    url = attr.ib(type=str)
    #: Size of the file, in bytes
    size = attr.ib(type=int, converter=int)
    #: Whether Facebook determines that this file may be harmful
    is_malicious = attr.ib(None, type=bool)

    @classmethod
    def from_pull(cls, attachment, blob, **kwargs):
        return cls(
            id=attachment["id"],
            name=attachment["filename"],
            mimetype=attachment["mimeType"],
            size=attachment["fileSize"],
            url=blob.get("url"),
            is_malicious=blob.get("is_malicious"),
            **kwargs
        )


@attr.s(slots=True)
class Audio(File):
    """Represents an audio file"""

    #: Duration of the audioclip
    duration = attr.ib(None, type=timedelta)
    #: Audio type
    audio_type = attr.ib(None, type=str)

    @classmethod
    def from_pull(cls, attachment, blob, **kwargs):
        file = super(Audio, cls).from_pull(
            attachment,
            blob,
            duration=timedelta(microseconds=blob["playable_duration_in_ms"] * 1000),
            audio_type=blob["audio_type"],
            **kwargs
        )
        file.url = blob["playable_url"]
        return file


@attr.s(slots=True)
class Image(File):
    """Represents an image"""

    #: The extension of the original image (e.g. 'png')
    extension = attr.ib(None, type=str)
    #: Dimensions of the original image
    dimensions = attr.ib(None, type=Dimension)

    #: URL to a 50x50 thumbnail of the image
    thumbnail_url = attr.ib(None, type=str)

    #: URL to a medium preview of the image
    preview_url = attr.ib(None, type=str)
    #: Dimensions of the medium preview
    preview_dimensions = attr.ib(None, type=Dimension)

    #: URL to a large preview of the image
    large_preview_url = attr.ib(None, type=str)
    #: Dimensions of the large preview
    large_preview_dimensions = attr.ib(None, type=Dimension)

    @classmethod
    def from_pull(cls, attachment, blob, **kwargs):
        preview = blob["preview"]
        large_preview = blob["large_preview"]
        return super(Image, cls).from_pull(
            attachment,
            blob,
            extension=blob["original_extension"],
            dimensions=Dimension.from_dict(attachment["imageMetadata"]),
            thumbnail_url=blob["thumbnail"]["uri"],
            preview_url=preview["uri"],
            preview_dimensions=Dimension.from_dict(preview),
            large_preview_url=large_preview["uri"],
            large_preview_dimensions=Dimension.from_dict(large_preview),
            **kwargs
        )


@attr.s(slots=True)
class AnimatedImage(Image):
    """Represents an image (e.g. "gif")"""

    #: URL to an animated preview of the image
    animated_preview_url = None
    #: Dimensions of the animated preview
    animated_preview_dimensions = attr.ib(None, type=Dimension)

    @classmethod
    def from_pull(cls, attachment, blob, **kwargs):
        animated = blob["animated_image"]
        return super(AnimatedImage, cls).from_pull(
            attachment,
            blob,
            animated_preview_url=animated["uri"],
            animated_preview_dimensions=Dimension.from_dict(animated),
            **kwargs
        )


@attr.s(slots=True)
class Video(File):
    """Represents a video"""

    #: Dimensions of the original image
    dimensions = attr.ib(None, type=Dimension)
    #: Duration of the video
    duration = attr.ib(None, type=timedelta)
    #: URL to very compressed preview video
    preview_url = attr.ib(None, type=str)

    #: URL to a small preview image of the video
    small_image_url = attr.ib(None, type=str)
    #: Dimensions of the small preview
    small_image_dimensions = attr.ib(None, type=Dimension)

    #: URL to a medium preview image of the video
    medium_image_url = attr.ib(None, type=str)
    #: Dimensions of the medium preview
    medium_image_dimensions = attr.ib(None, type=Dimension)

    #: URL to a large preview image of the video
    large_image_url = attr.ib(None, type=str)
    #: Dimensions of the large preview
    large_image_dimensions = attr.ib(None, type=Dimension)

    @classmethod
    def from_pull(cls, attachment, blob, **kwargs):
        small_image = blob["chat_image"]
        medium_image = blob["inbox_image"]
        large_image = blob["large_image"]
        return super(Video, cls).from_pull(
            attachment,
            blob,
            dimensions=Dimension.from_dict(blob["original_dimensions"]),
            duration=timedelta(microseconds=blob["playable_duration_in_ms"] * 1000),
            preview_url=blob["playable_url"],
            small_image_url=small_image["uri"],
            small_image_dimensions=Dimension.from_dict(small_image),
            medium_image_url=medium_image["uri"],
            medium_image_dimensions=Dimension.from_dict(medium_image),
            large_image_url=large_image["uri"],
            large_image_dimensions=Dimension.from_dict(large_image),
            **kwargs
        )
