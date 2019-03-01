# -*- coding: UTF-8 -*-

from fbchat import Client, logging
from fbchat.models import *
import threading
import sys

user = "<email>"
password = "<password>"


# Subclass fbchat.Client and override required methods
class MessagePrinter(Client):
    def onMessage(self, author_id, message_object, thread_id, thread_type, **kwargs):
        self.markAsDelivered(thread_id, message_object.uid)
        self.markAsRead(thread_id)

        print("\nIncoming message: {}".format(message_object.text))

    # Creating some feedback on login since we will disable INFO logging
    def onLoggedIn(self, email=None):
        print("Login of {} successful.".format(email))


# Login and set logging level to WARNING to avoid some unessential output
client1 = Client(user, password, logging_level=logging.WARNING)
client2 = MessagePrinter(user, password, logging_level=logging.WARNING)


# Creating and starting a separate thread for receiving messages
t1 = threading.Thread(target=client2.listen, daemon=True)
t1.start()


# Loop checking for, and sending messages
try:
    while True:
        payload = input("Message: ")
        if payload:
            client1.send(
                Message(text=payload),
                thread_id=client1.uid,
                thread_type=ThreadType.USER,
            )

# Clean-up on exit
except KeyboardInterrupt:
    client1.logout()
    client2.logout()
    sys.exit(0)
