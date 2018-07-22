# -*- coding: UTF-8 -*-

from __future__ import unicode_literals


class FacebookError(Exception):
    """Thrown by fbchat when Facebook returns an error

    Attributes:
        fb_error_code (int): The error code that Facebook returned
        fb_error_message: A localized error message that Facebook returned
    """

    def __init__(self, message, fb_error_code=None, fb_error_message=None):
        super(FacebookError, self).__init__(message)
        self.fb_error_code = int(fb_error_code)
        self.fb_error_message = fb_error_message


class Thread(object):
    """Represents a Facebook chat-thread

    Attributes:
        id (int): The unique identifier of the thread
        name: The name of the thread
        image: A url to the thread's thumbnail/profile picture
        last_activity (`Time`): When the thread was last updated
        message_count: Number of `Message`\s in the thread
        nicknames (dict): `User`\s and `Page`\s, mapped to their nicknames
        colour (`Thread.Colour`): The thread colour
        emoji: The thread's default emoji
    """

    def __init__(self, id_):
        if not id_ or id_ < 1:
            raise ValueError("Invalid ID")
        self.id = int(id_)

    def __hash__(self):
        return self.id

    def __eq__(self, other):
        return isinstance(other, Thread) and self.id == other.id

    def __ne__(self, other):
        return not self.__eq__(other)


    class Colour(object):
        """Used to specify thread colours"""
        MESSENGER_BLUE = '#0084ff'
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
        participants (list): `User`\s, denoting the thread's participants
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


class Event(object):
    """Represents an event in a Facebook thread

    Attributes:
        thread (`Thread`): The thread the event was sent to
        author (`User` or `Page`): The person who sent the event
        time (`Time`): When the event was sent
        is_read (bool): Whether the event is read
    """


class Message(Event):
    """Represents a message

    Attributes:
        id (int): The unique identifier of the message
    """


class Action(Event):
    """Represents an action in a thread"""


class Sticker(Message):
    """Represents a sticker

    Attributes:
        sticker_id (int): The sticker's ID
        name: The sticker's label/name
        width (int): Width of the sticker
        height (int): Height of the sticker
        pack (`Sticker.Pack`): The sticker's pack
    """

    class Pack(object):
        """TODO: This"""


class AnimatedSticker(Sticker):
    """TODO: This"""


class Emoji(Message):
    """Represents a sent emoji

    Attributes:
        emoji: The actual emoji
        size (`Emoji.Size`): The size of the emoji
    """

    class Size(object):
        """Used to specify the size an emoji"""
        SMALL = 'small'
        MEDIUM = 'medium'
        LARGE = 'large'


class Text(Message):
    """Represents a text message

    Attributes:
        text: The text-contents
        mentions (list): `Mention`\s
        reactions (dict): `User`\s, mapped to their reaction.
            A reaction can be ``😍``, ``😆``, ``😮``, ``😢``, ``😠``, ``👍`` or ``👎``
    """

    class Mention(object):
        """Represents a @mention

        Attributes:
            thread (`Thread`): Person/thread that the mention is pointing at
            offset (int): The character in the message where the mention starts
            length (int): The length of the mention
        """


class FileMessage(Text):
    """Represents a text message with files / attachments

    Attributes:
        files (list): `File`\s
    """


class File(object):
    """Represents a file / an attachment

    Attributes:
        id (int): The file ID
        name: Name of the file
        url: URL to download the attachment
        size (int): Size of the file in bytes
        is_malicious (bool): True if Facebook determines that this file may be harmful
    """


class Audio(File):
    """Todo: This"""


class Image(File):
    """Todo: This"""


class AnimatedImage(Image):
    """Todo: This"""


class Video(File):
    """Todo: This"""


class UsersAdded(Action):
    """Represents an action where a person was added to a group

    Attributes:
        users (list): The added `User`\s
    """


class UserRemoved(Action):
    """Represents an action where a person was removed from a group

    Attributes:
        user (`User`): The removed user
    """


class AdminAdded(Action):
    """Represents an action where a group admin was added

    Attributes:
        user (`User`): The promoted user
    """


class AdminRemoved(Action):
    """Represents an action where a group admin was removed

    Attributes:
        user (`User`): The demoted user
    """


class ThreadAdded(Action):
    """Represents an action where a thread was created"""


class ImageSet(Action):
    """Represents an action where a group image was changed

    Attributes:
        image (`Image`): The new image
    """


class TitleSet(Action):
    """Represents an action where the group title was changed

    Attributes:
        title: The new title
    """


class NicknameSet(Action):
    """Represents an action where a nickname was changed

    Attributes:
        actor (`User` or `Page`): Person whose nickname was changed
        nickname: User's new nickname
    """


class ColourSet(Action):
    """Represents an action where the thread colour was changed

    Attributes:
        colour (`Thread.Colour`): The new colour
    """


class EmojiSet(Action):
    """Represents an action where the thread emoji was changed

    Attributes:
        emoji: The new emoji
    """
