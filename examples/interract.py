import fbchat

session = fbchat.Session.login("<email>", "<password>")

client = fbchat.Client(session)

thread_id = "1234567890"
thread_type = fbchat.ThreadType.GROUP

# Will send a message to the thread
client.send(
    fbchat.Message(text="<message>"), thread_id=thread_id, thread_type=thread_type
)

# Will send the default `like` emoji
client.send(
    fbchat.Message(emoji_size=fbchat.EmojiSize.LARGE),
    thread_id=thread_id,
    thread_type=thread_type,
)

# Will send the emoji `👍`
client.send(
    fbchat.Message(text="👍", emoji_size=fbchat.EmojiSize.LARGE),
    thread_id=thread_id,
    thread_type=thread_type,
)

# Will send the sticker with ID `767334476626295`
client.send(
    fbchat.Message(sticker=fbchat.Sticker("767334476626295")),
    thread_id=thread_id,
    thread_type=thread_type,
)

# Will send a message with a mention
client.send(
    fbchat.Message(
        text="This is a @mention",
        mentions=[fbchat.Mention(thread_id, offset=10, length=8)],
    ),
    thread_id=thread_id,
    thread_type=thread_type,
)

# Will send the image located at `<image path>`
client.send_local_image(
    "<image path>",
    message=fbchat.Message(text="This is a local image"),
    thread_id=thread_id,
    thread_type=thread_type,
)

# Will download the image at the URL `<image url>`, and then send it
client.send_remote_image(
    "<image url>",
    message=fbchat.Message(text="This is a remote image"),
    thread_id=thread_id,
    thread_type=thread_type,
)


# Only do these actions if the thread is a group
if thread_type == fbchat.ThreadType.GROUP:
    # Will remove the user with ID `<user id>` from the thread
    client.remove_user_from_group("<user id>", thread_id=thread_id)

    # Will add the user with ID `<user id>` to the thread
    client.add_users_to_group("<user id>", thread_id=thread_id)

    # Will add the users with IDs `<1st user id>`, `<2nd user id>` and `<3th user id>` to the thread
    client.add_users_to_group(
        ["<1st user id>", "<2nd user id>", "<3rd user id>"], thread_id=thread_id
    )


# Will change the nickname of the user `<user_id>` to `<new nickname>`
client.change_nickname(
    "<new nickname>", "<user id>", thread_id=thread_id, thread_type=thread_type
)

# Will change the title of the thread to `<title>`
client.change_thread_title("<title>", thread_id=thread_id, thread_type=thread_type)

# Will set the typing status of the thread to `TYPING`
client.set_typing_status(
    fbchat.TypingStatus.TYPING, thread_id=thread_id, thread_type=thread_type
)

# Will change the thread color to `MESSENGER_BLUE`
client.change_thread_color(fbchat.ThreadColor.MESSENGER_BLUE, thread_id=thread_id)

# Will change the thread emoji to `👍`
client.change_thread_emoji("👍", thread_id=thread_id)

# Will react to a message with a 😍 emoji
client.react_to_message("<message id>", fbchat.MessageReaction.LOVE)
