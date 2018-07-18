# -*- coding: UTF-8 -*-

from __future__ import unicode_literals
import enum


class Enum(enum.Enum):
    """Used internally by fbchat to support enumerations"""
    def __repr__(self):
        # For documentation:
        return '{}.{}'.format(type(self).__name__, self.name)


class FacebookError(Exception):
    """Thrown by fbchat when Facebook returns an error

    Attributes:
        fb_error_code (int): The error code that Facebook returned
        fb_error_message: A localized error message that Facebook returned
    """


class Thread(object):
    """Represents a Facebook chat-thread

    Attributes:
        id (int): The unique identifier of the thread
        image: A url to the thread's thumbnail/profile picture
        name: The name of the thread
        last_message_timestamp: Timestamp of last message
        message_count: Number of messages in the thread
        nicknames: A dict, containing `User`\s and `Page`\s, mapped to their
            nicknames
        participants: Unique list of `User`\s and `Page`\s, denoting the
            thread's participants
        colour (`Colour`): The thread colour
        color: Alias of :attr:`colour`
        emoji: The thread's default emoji
    """


class User(Thread):
    """Represents a user and the chat-thread the client has with the user

    Attributes:
        first_name: The user's first name
        last_name: The user's last name
        is_friend (bool): Whether the user and the client are friends
        gender: The user's gender
        affinity (float): From 0 to 1. How close the client is to the user
    """


class Group(Thread):
    """Represents a group-thread

    Attributes:
        admins (list): Unique list of `User`\s, denoting the group's admins
        title: The group's custom title
    """


class Page(Thread):
    """Represents a Facebook page

    Attributes:
        city: The name of the page's location city
        likes: Amount of likes that the page has
        sub_title: Some extra information about the page
        category: The page's category
    """


class Message(object):
    """Represents a message

    Attributes:
        id (int): The unique identifier of the message
        text: The text-contents
        mentions (list of `Mention`\s):
        size (`Size`): The size of a sent emoji
        author (`User` or `Page`): The person who sent the message
        timestamp: Unix timestamp of when the message was sent
        is_read: Whether the message is read
        reactions (dict): A dict with `User`\s, mapped to their reaction
        sticker (`Sticker` or ``None``):
        files (list of `File`\s):
        images (list of `Image`\s): Subset of :attr:`files`
        videos (list of `Video`\s): Subset of :attr:`files`
    """


class Mention(object):
    """Represents a @mention

    Attributes:
        thread (`Thread`): Person that the mention is pointing at
        offset (int): The character in the message where the mention starts
        length (int): The length of the mention
    """


class Attachment(object):
    """Represents a Facebook attachment

    Attributes:
        id (int): The attachment ID
        url: URL to download the attachment
    """


class Sticker(Attachment):
    """Represents a sticker

    Attributes:
        pack (`StickerPack`): The sticker's pack
        width (int): Width of the sticker
        height (int): Height of the sticker
        name: The sticker's label/name
    """


class AnimatedSticker(Sticker):
    """Todo: This"""


class StickerPack(object):
    """Todo: This"""


class File(Attachment):
    """Represents a file-attachment

    Attributes:
        size (int): Size of the file in bytes
        name: Name of the file
        is_malicious (bool): True if Facebook determines that this file may be
            harmful
    """


class Audio(File):
    """Todo: This"""


class Image(File):
    """Todo: This"""


class AnimatedImage(Image):
    """Todo: This"""


class Video(File):
    """Todo: This"""


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
