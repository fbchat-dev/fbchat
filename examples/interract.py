# -*- coding: UTF-8 -*-

from fbchat import Client
from fbchat.models import *

client = Client("<email>", "<password>")

thread_id = "1234567890"
thread_type = ThreadType.GROUP

# Will send a message to the thread
client.send(Message(text="<message>"), thread_id=thread_id, thread_type=thread_type)

# Will send the default `like` emoji
client.send(
    Message(emoji_size=EmojiSize.LARGE), thread_id=thread_id, thread_type=thread_type
)

# Will send the emoji `👍`
client.send(
    Message(text="👍", emoji_size=EmojiSize.LARGE),
    thread_id=thread_id,
    thread_type=thread_type,
)

# Will send the sticker with ID `767334476626295`
client.send(
    Message(sticker=Sticker("767334476626295")),
    thread_id=thread_id,
    thread_type=thread_type,
)

# Will send a message with a mention
client.send(
    Message(
        text="This is a @mention", mentions=[Mention(thread_id, offset=10, length=8)]
    ),
    thread_id=thread_id,
    thread_type=thread_type,
)

# Will send the image located at `<image path>`
client.sendLocalImage(
    "<image path>",
    message=Message(text="This is a local image"),
    thread_id=thread_id,
    thread_type=thread_type,
)

# Will download the image at the URL `<image url>`, and then send it
client.sendRemoteImage(
    "<image url>",
    message=Message(text="This is a remote image"),
    thread_id=thread_id,
    thread_type=thread_type,
)


# Only do these actions if the thread is a group
if thread_type == ThreadType.GROUP:
    # Will remove the user with ID `<user id>` from the thread
    client.removeUserFromGroup("<user id>", thread_id=thread_id)

    # Will add the user with ID `<user id>` to the thread
    client.addUsersToGroup("<user id>", thread_id=thread_id)

    # Will add the users with IDs `<1st user id>`, `<2nd user id>` and `<3th user id>` to the thread
    client.addUsersToGroup(
        ["<1st user id>", "<2nd user id>", "<3rd user id>"], thread_id=thread_id
    )


# Will change the nickname of the user `<user_id>` to `<new nickname>`
client.changeNickname(
    "<new nickname>", "<user id>", thread_id=thread_id, thread_type=thread_type
)

# Will change the title of the thread to `<title>`
client.changeThreadTitle("<title>", thread_id=thread_id, thread_type=thread_type)

# Will set the typing status of the thread to `TYPING`
client.setTypingStatus(
    TypingStatus.TYPING, thread_id=thread_id, thread_type=thread_type
)

# Will change the thread color to `MESSENGER_BLUE`
client.changeThreadColor(ThreadColor.MESSENGER_BLUE, thread_id=thread_id)

# Will change the thread emoji to `👍`
client.changeThreadEmoji("👍", thread_id=thread_id)

# Will react to a message with a 😍 emoji
client.reactToMessage("<message id>", MessageReaction.LOVE)
