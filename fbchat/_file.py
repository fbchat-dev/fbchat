import attr
from ._core import attrs_default, Image
from . import _util
from ._attachment import Attachment


@attrs_default
class FileAttachment(Attachment):
    """Represents a file that has been sent as a Facebook attachment."""

    #: URL where you can download the file
    url = attr.ib(None)
    #: Size of the file in bytes
    size = attr.ib(None)
    #: Name of the file
    name = attr.ib(None)
    #: Whether Facebook determines that this file may be harmful
    is_malicious = attr.ib(None)

    @classmethod
    def _from_graphql(cls, data, size=None):
        return cls(
            url=data.get("url"),
            size=size,
            name=data.get("filename"),
            is_malicious=data.get("is_malicious"),
            uid=data.get("message_file_fbid"),
        )


@attrs_default
class AudioAttachment(Attachment):
    """Represents an audio file that has been sent as a Facebook attachment."""

    #: Name of the file
    filename = attr.ib(None)
    #: URL of the audio file
    url = attr.ib(None)
    #: Duration of the audio clip as a timedelta
    duration = attr.ib(None)
    #: Audio type
    audio_type = attr.ib(None)

    @classmethod
    def _from_graphql(cls, data):
        return cls(
            filename=data.get("filename"),
            url=data.get("playable_url"),
            duration=_util.millis_to_timedelta(data.get("playable_duration_in_ms")),
            audio_type=data.get("audio_type"),
        )


@attrs_default
class ImageAttachment(Attachment):
    """Represents an image that has been sent as a Facebook attachment.

    To retrieve the full image URL, use: `Client.fetch_image_url`, and pass it the id of
    the image attachment.
    """

    #: The extension of the original image (e.g. ``png``)
    original_extension = attr.ib(None)
    #: Width of original image
    width = attr.ib(None, converter=lambda x: None if x is None else int(x))
    #: Height of original image
    height = attr.ib(None, converter=lambda x: None if x is None else int(x))

    #: Whether the image is animated
    is_animated = attr.ib(None)

    #: A thumbnail of the image
    thumbnail = attr.ib(None)
    #: A medium preview of the image
    preview = attr.ib(None)
    #: A large preview of the image
    large_preview = attr.ib(None)
    #: An animated preview of the image (e.g. for GIFs)
    animated_preview = attr.ib(None)

    @classmethod
    def _from_graphql(cls, data):
        return cls(
            original_extension=data.get("original_extension")
            or (data["filename"].split("-")[0] if data.get("filename") else None),
            width=data.get("original_dimensions", {}).get("width"),
            height=data.get("original_dimensions", {}).get("height"),
            is_animated=data["__typename"] == "MessageAnimatedImage",
            thumbnail=Image._from_uri_or_none(data.get("thumbnail")),
            preview=Image._from_uri_or_none(
                data.get("preview") or data.get("preview_image")
            ),
            large_preview=Image._from_uri_or_none(data.get("large_preview")),
            animated_preview=Image._from_uri_or_none(data.get("animated_image")),
            uid=data.get("legacy_attachment_id"),
        )

    @classmethod
    def _from_list(cls, data):
        data = data["node"]
        return cls(
            width=data["original_dimensions"].get("x"),
            height=data["original_dimensions"].get("y"),
            thumbnail=Image._from_uri_or_none(data["image"]),
            large_preview=Image._from_uri(data["image2"]),
            preview=Image._from_uri(data["image1"]),
            uid=data["legacy_attachment_id"],
        )


@attrs_default
class VideoAttachment(Attachment):
    """Represents a video that has been sent as a Facebook attachment."""

    #: Size of the original video in bytes
    size = attr.ib(None)
    #: Width of original video
    width = attr.ib(None)
    #: Height of original video
    height = attr.ib(None)
    #: Length of video as a timedelta
    duration = attr.ib(None)
    #: URL to very compressed preview video
    preview_url = attr.ib(None)

    #: A small preview image of the video
    small_image = attr.ib(None)
    #: A medium preview image of the video
    medium_image = attr.ib(None)
    #: A large preview image of the video
    large_image = attr.ib(None)

    @classmethod
    def _from_graphql(cls, data, size=None):
        return cls(
            size=size,
            width=data.get("original_dimensions", {}).get("width"),
            height=data.get("original_dimensions", {}).get("height"),
            duration=_util.millis_to_timedelta(data.get("playable_duration_in_ms")),
            preview_url=data.get("playable_url"),
            small_image=Image._from_uri_or_none(data.get("chat_image")),
            medium_image=Image._from_uri_or_none(data.get("inbox_image")),
            large_image=Image._from_uri_or_none(data.get("large_image")),
            uid=data.get("legacy_attachment_id"),
        )

    @classmethod
    def _from_subattachment(cls, data):
        media = data["media"]
        return cls(
            duration=_util.millis_to_timedelta(media.get("playable_duration_in_ms")),
            preview_url=media.get("playable_url"),
            medium_image=Image._from_uri_or_none(media.get("image")),
            uid=data["target"].get("video_id"),
        )

    @classmethod
    def _from_list(cls, data):
        data = data["node"]
        return cls(
            width=data["original_dimensions"].get("x"),
            height=data["original_dimensions"].get("y"),
            small_image=Image._from_uri(data["image"]),
            medium_image=Image._from_uri(data["image1"]),
            large_image=Image._from_uri(data["image2"]),
            uid=data["legacy_attachment_id"],
        )


def graphql_to_attachment(data, size=None):
    _type = data["__typename"]
    if _type in ["MessageImage", "MessageAnimatedImage"]:
        return ImageAttachment._from_graphql(data)
    elif _type == "MessageVideo":
        return VideoAttachment._from_graphql(data, size=size)
    elif _type == "MessageAudio":
        return AudioAttachment._from_graphql(data)
    elif _type == "MessageFile":
        return FileAttachment._from_graphql(data, size=size)

    return Attachment(uid=data.get("legacy_attachment_id"))


def graphql_to_subattachment(data):
    target = data.get("target")
    type_ = target.get("__typename") if target else None

    if type_ == "Video":
        return VideoAttachment._from_subattachment(data)

    return None
