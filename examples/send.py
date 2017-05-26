# -*- coding: UTF-8 -*-

from fbchat import Client
from fbchat.models import *

client = Client("<email>", "<password>")

# Change these to match your thread
thread_id = '1234567890'
thread_type = ThreadType.GROUP # Or ThreadType.USER

# This will send a message to the thread
client.sendMessage('Hey there', thread_id=thread_id, thread_type=thread_type)

# This will send the default emoji
client.sendEmoji(emoji=None, size=EmojiSize.LARGE, thread_id=thread_id, thread_type=thread_type)

# This will send the emoji `👍`
client.sendEmoji(emoji='👍', size=EmojiSize.LARGE, thread_id=thread_id, thread_type=thread_type)

# This will send the image called `image.png`
client.sendLocalImage('image.png', message='This is a local image', thread_id=thread_id, thread_type=thread_type)

# This will send the image at the url `https://example.com/image.png`
client.sendRemoteImage('https://example.com/image.png', message='This is a remote image', thread_id=thread_id, thread_type=thread_type)
