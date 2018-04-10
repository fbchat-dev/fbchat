# -*- coding: UTF-8 -*-

from __future__ import unicode_literals
import enum


class Enum(enum.Enum):
    """Used internally by fbchat to support enumerations"""
    def __repr__(self):
        # For documentation:
        return '{}.{}'.format(type(self).__name__, self.name)


class Thread(object):
    """Represents a Facebook thread"""

    #: The unique identifier of the thread
    id = None
    #: The thread's Facebook url
    url = None
    #: A url to the thread's picture
    image = None
    #: The name of the thread
    name = None
    #: Timestamp of last message
    last_message_timestamp = None
    #: Number of messages in the thread
    message_count = None
    #: A dict, containing `User`\s and `Page`\s, mapped to their nicknames
    nicknames = None
    #: Unique list of `User`\s and `Page`\s, denoting the thread's participants
    participants = None
    #: The thread `Colour`
    colour = None
    #: Alias of :attr:`colour`
    color = None
    #: The thread's default emoji
    emoji = None


class User(Thread):
    """Represents a Facebook user"""

    #: The user's first name
    first_name = None
    #: The user's last name
    last_name = None
    #: Whether the user and the client are friends
    is_friend = None
    #: The user's gender
    gender = None
    #: From 0 to 1. How close the client is to the user
    affinity = None


class Group(Thread):
    """Represents a Facebook group-thread"""

    #: Unique list of `User`\s, denoting the group's admins
    admins = None


class Page(Thread):
    """Represents a Facebook page"""

    #: The name of the page's location city
    city = None
    #: Amount of likes that the page has
    likes = None
    #: Some extra information about the page
    sub_title = None
    #: The page's category
    category = None


class Message(object):
    """Represents a Facebook message"""

    #: The unique identifier of the message
    id = None
    #: The text-contents
    text = None
    #: A list of `Mention`\s
    mentions = None
    #: `Size` of a sent emoji
    size = None
    #: `User` or `Page`, denoting the sender
    author = None
    #: Float unix timestamp of when the message was sent
    timestamp = None
    #: Whether the message is read
    is_read = None
    #: A dict with `User`\s, mapped to their reaction
    reactions = None
    #: A `Sticker`
    sticker = None
    #: A list of `File`\s
    files = None
    #: A list of `Image`s. Subset of :attr:`files`
    images = None
    #: A list of `Video`s. Subset of :attr:`files`
    videos = None


class Mention(object):
    """Represents a @mention"""

    #: `Thread` that the mention is pointing at
    thread = None
    #: The character where the mention starts
    offset = None
    #: The length of the mention
    length = None


class Attachment(object):
    """"""

    #: The attachment ID
    id = None
    #: URL to the attachment
    url = None


class Sticker(Attachment):
    """"""

    #: The sticker-pack's ID
    pack = None
    #: Width of the sticker
    width = None
    #: Height of the sticker
    height = None
    #: The sticker's label/name
    label = None


class AnimatedSticker(Sticker):
    """"""

    # If the sticker is animated, the following should be present
    #: URL to a medium spritemap
    medium_sprite = None
    #: URL to a large spritemap
    large_sprite = None
    #: The amount of frames present in the spritemap pr. row
    frames_per_row = None
    #: The amount of frames present in the spritemap pr. coloumn
    frames_per_col = None
    #: The frame rate the spritemap is intended to be played in
    frame_rate = None


class File(Attachment):
    """"""

    #: Url where you can download the file
    url = None
    #: Size of the file in bytes
    size = None
    #: Name of the file
    name = None
    #: Whether Facebook determines that this file may be harmful
    is_malicious = None


class Audio(File):
    """"""

    #: Name of the file
    filename = None
    #: Url of the audio file
    url = None
    #: Duration of the audioclip in milliseconds
    duration = None
    #: Audio type
    audio_type = None


class Image(File):
    """"""

    #: Width of original image
    width = None
    #: Height of original image
    height = None
    #: URL to a thumbnail of the image
    thumbnail = None
    #: URL to a medium preview of the image
    preview = None
    #: URL to a large preview of the image
    large_preview = None
    #: The extension of the original image (eg. 'png')
    original_extension = None


class AnimatedImage(Image):
    """"""

    #: URL to an animated preview of the image
    animated_preview = None


class Video(File):
    """"""

    #: Width of original video
    width = None
    #: Height of original video
    height = None
    #: Length of video in milliseconds
    duration = None
    #: URL to very compressed preview video
    preview = None
    #: URL to a small preview image of the video
    small_image = None
    #: URL to a medium preview image of the video
    medium_image = None
    #: URL to a large preview image of the video
    large_image = None


class Size(Enum):
    """Used to specify the size an emoji"""
    SMALL = 1
    MEDIUM = 2
    LARGE = 3


class Colour(Enum):
    """Used to specify thread colours

    See #220 before implementing this
    """
    MESSENGER_BLUE = ''
    VIKING = '#44bec7'
    GOLDEN_POPPY = '#ffc300'
    RADICAL_RED = '#fa3c4c'
    SHOCKING = '#d696bb'
    PICTON_BLUE = '#6699cc'
    FREE_SPEECH_GREEN = '#13cf13'
    PUMPKIN = '#ff7e29'
    LIGHT_CORAL = '#e68585'
    MEDIUM_SLATE_BLUE = '#7646ff'
    DEEP_SKY_BLUE = '#20cef5'
    FERN = '#67b868'
    CAMEO = '#d4a88c'
    BRILLIANT_ROSE = '#ff5ca1'
    BILOBA_FLOWER = '#a695c7'


Color = Colour
