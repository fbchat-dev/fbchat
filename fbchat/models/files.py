# -*- coding: UTF-8 -*-

import attr

from datetime import timedelta
from typing import Optional, Type, T

from .core import Dimension, ID, JSON


__all__ = ("File", "Audio", "Image", "AnimatedImage", "Video")


@attr.s(slots=True)
class File:
    """Represents a file / an attachment"""

    #: The unique identifier of the file
    id = attr.ib(type=ID)
    #: Name of the file
    name = attr.ib(type=str)
    #: The mimetype of the file
    mimetype = attr.ib(type=str)
    #: URL where you can download the file
    url = attr.ib(type=Optional[str])
    #: Size of the file, in bytes
    size = attr.ib(type=int)
    #: Whether Facebook determines that this file may be harmful
    is_malicious = attr.ib(type=Optional[bool])

    @classmethod
    def from_pull(cls: Type[T], attachment: JSON, blob: JSON, **kwargs) -> T:
        self = cls.__new__(cls)

        self.id = ID(attachment["id"])
        self.name = attachment["filename"]
        self.mimetype = attachment["mimeType"]
        self.size = attachment["fileSize"]
        self.url = blob.get("url")
        self.is_malicious = blob.get("is_malicious")

        return self


@attr.s(slots=True)
class Audio(File):
    """Represents an audio file"""

    #: Duration of the audioclip
    duration = attr.ib(type=timedelta)
    #: Audio type
    audio_type = attr.ib(type=str)

    @classmethod
    def from_pull(cls: Type[T], attachment: JSON, blob: JSON) -> T:
        self = super().from_pull(attachment, blob)

        self.duration = timedelta(microseconds=blob["playable_duration_in_ms"] * 1000)
        self.audio_type = blob["audio_type"]
        self.url = blob["playable_url"]

        return self


@attr.s(slots=True)
class Image(File):
    """Represents an image"""

    #: The extension of the original image (e.g. 'png')
    extension = attr.ib(type=str)
    #: Dimensions of the original image
    dimension = attr.ib(type=Dimension)

    #: URL to a 50x50 thumbnail of the image
    thumbnail_url = attr.ib(type=str)

    #: URL to a medium preview of the image
    preview_url = attr.ib(type=str)
    #: Dimensions of the medium preview
    preview_dimension = attr.ib(type=Dimension)

    #: URL to a large preview of the image
    large_preview_url = attr.ib(type=Optional[str])
    #: Dimensions of the large preview
    large_preview_dimension = attr.ib(type=Optional[Dimension])

    @classmethod
    def from_pull(cls: Type[T], attachment: JSON, blob: JSON) -> T:
        self = super().from_pull(attachment, blob)

        preview = blob["preview"]
        large_preview = blob["large_preview"]

        self.extension = blob["original_extension"]
        self.dimensions = Dimension.from_dict(attachment["imageMetadata"])
        self.thumbnail_url = blob["thumbnail"]["uri"]
        self.preview_url = preview["uri"]
        self.preview_dimensions = Dimension.from_dict(preview)
        self.large_preview_url = large_preview["uri"]
        self.large_preview_dimensions = Dimension.from_dict(large_preview)

        return self


@attr.s(slots=True)
class AnimatedImage(Image):
    """Represents an image (e.g. "gif")"""

    #: URL to an animated preview of the image
    animated_preview_url = attr.ib(type=str)
    #: Dimensions of the animated preview
    animated_preview_dimension = attr.ib(type=Dimension)

    @classmethod
    def from_pull(cls: Type[T], attachment: JSON, blob: JSON) -> T:
        self = super().from_pull(attachment, blob)

        animated = blob["animated_image"]

        self.animated_preview_url = animated["uri"]
        self.animated_preview_dimensions = Dimension.from_dict(animated)

        return self


@attr.s(slots=True)
class Video(File):
    """Represents a video"""

    #: Dimensions of the original image
    dimensions = attr.ib(type=Dimension)
    #: Duration of the video
    duration = attr.ib(type=timedelta)
    #: URL to very compressed preview video
    preview_url = attr.ib(type=str)

    #: URL to a small preview image of the video
    small_image_url = attr.ib(type=Optional[str])
    #: Dimensions of the small preview
    small_image_dimension = attr.ib(type=Optional[Dimension])

    #: URL to a medium preview image of the video
    medium_image_url = attr.ib(type=Optional[str])
    #: Dimensions of the medium preview
    medium_image_dimension = attr.ib(type=Dimension)

    #: URL to a large preview image of the video
    large_image_url = attr.ib(type=Optional[str])
    #: Dimensions of the large preview
    large_image_dimension = attr.ib(type=Optional[Dimension])

    @classmethod
    def from_pull(cls: Type[T], attachment: JSON, blob: JSON) -> T:
        self = super().from_pull(attachment, blob)

        small_image = blob["chat_image"]
        medium_image = blob["inbox_image"]
        large_image = blob["large_image"]

        self.dimensions = Dimension.from_dict(blob["original_dimensions"])
        self.duration = timedelta(microseconds=blob["playable_duration_in_ms"] * 1000)
        self.preview_url = blob["playable_url"]
        self.small_image_url = small_image["uri"]
        self.small_image_dimensions = Dimension.from_dict(small_image)
        self.medium_image_url = medium_image["uri"]
        self.medium_image_dimensions = Dimension.from_dict(medium_image)
        self.large_image_url = large_image["uri"]
        self.large_image_dimensions = Dimension.from_dict(large_image)

        return self
