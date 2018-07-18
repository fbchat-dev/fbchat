# -*- coding: UTF-8 -*-

from time import sleep
from fbchat import Client, Group, Size, Sticker, Mention, Color

c = Client("<email>", "<password>")

# Get the thread from an ID
thread = c.get_threads_from_ids(1234567890)

user = c.get_threads_from_ids(12345678901)

# Send some text to the thread
c.send_text(thread, 'This is a message!')

# Send the thread's default emoji
c.send_emoji(thread)

# Send the thumbs up emoji, in large version
c.send_emoji(thread, '👍', size=Size.LARGE)

# Send the sticker with ID `767334476626295`
c.send_sticker(thread, Sticker(767334476626295))

# Send a message with a mention
c.send_text(thread, 'This is a @mention!',
            mentions=[Mention(thread, offset=10, length=8)])

# Send the image located at `<image path>`
c.send_file(thread, '<image path>', text='This is a local image')

# Only do these actions if the thread is a group
if isinstance(thread, Group):
    # Remove the from the thread
    c.remove_user(thread, user)

    # Add the user to the thread
    c.add_user(thread, user)

    # Make the user an admin
    c.add_admin(thread, user)

    # Make the user no longer an admin
    c.remove_admin(thread, user)

    # Set the nickname of the user
    c.set_nickname(thread, user, 'This is a nickname!')

# Set the title of the thread
c.set_title(thread, 'This is a title!')

# Make it look like you started typing, and then sent a message
c.start_typing(thread)
sleep(5)
c.send_text(thread, 'Some message')
c.stop_typing(thread)

# Set the thread color to `MESSENGER_BLUE`
c.set_colour(thread, Color.MESSENGER_BLUE)

# Set the thread emoji to `👍`
c.set_emoji(thread, '👍')

message = c.send_text(thread, 'A message')

# Will react to a message with a 😍 emoji
c.set_reaction(message, '😍')
