# -*- coding: UTF-8 -*-

from fbchat import *


# Subclass the Client
class EchoBot(Client):

    # And override the on_message method
    def on_message(self, message):
        # If the author isn't you
        if message.author != self:
            # Send the message back to the thread
            self.send(message.thread, message)


# Login and initialize
bot = EchoBot("<email>", "<password>")

# Start listening for messages, and when a message is recieved, on_message
# will be called
bot.listen()
