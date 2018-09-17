# -*- coding: UTF-8 -*-

from time import sleep
from fbchat import Client, Group, Emoji, Sticker, Mention

client = Client.login("<email>", "<password>")

# Get two threads from their IDs
thread, user = client.get_threads_from_ids([1234567890, 12345678901])

# Send some text to the thread
client.send_text(thread, "This is a message!")

# Send the thread's default emoji
client.send_emoji(thread)

# Send the thumbs up emoji, in large version
client.send_emoji(thread, "👍", size=Emoji.Size.LARGE)

# Send the sticker with ID `767334476626295`
client.send(thread, Sticker(767334476626295))

# Send a message with a mention
client.send_text(
    thread, "This is a @mention!", mentions=[Text.Mention(thread, offset=10, length=8)]
)

# Send the image located at `<image path>`
client.send_file(thread, "<image path>", text="This is a local image")

# Only do these actions if the thread is a group
if isinstance(thread, Group):
    # Remove the from the thread
    client.remove_user(thread, user)

    # Add the user to the thread
    client.add_user(thread, user)

    # Make the user an admin
    client.add_admin(thread, user)

    # Make the user no longer an admin
    client.remove_admin(thread, user)

    # Set the nickname of the user
    client.set_nickname(thread, user, "This is a nickname!")

# Set the title of the thread
client.set_title(thread, "This is a title!")

# Make it look like you started typing, and then sent a message
client.start_typing(thread)
sleep(5)
client.send_text(thread, "Some message")
client.stop_typing(thread)

# Set the thread color to `MESSENGER_BLUE`
client.set_colour(thread, Thread.Colour.MESSENGER_BLUE)

# Set the thread emoji to `👍`
client.set_emoji(thread, "👍")

message = client.send_text(thread, "A message")

# Will react to a message with a 😍 emoji
client.set_reaction(message, "😍")
