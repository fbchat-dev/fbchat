# -*- coding: UTF-8 -*-

from fbchat import Client
from fbchat.models import *
import threading

# Subclass fbchat.Client and override required methods
class PrintMessage(Client):
    def onMessage(self, author_id, message_object, thread_id, thread_type, **kwargs):
        self.markAsDelivered(thread_id, message_object.uid)
        self.markAsRead(thread_id)

        print("\nIncoming message: {}".format(message_object.text))

    # Creating some feedback on login since we will disable INFO logging
    def onLoggedIn(self, email=None):
        print("Login of {} successful.".format(email))


# Logging in and setting logging level to WARNING to avoid some unessential output
client = PrintMessage("<email>", "<password>", logging_level=30)


def send():
    while True:
        payload = input("Message: ")
        if payload:
            client.send(
                Message(text=payload), thread_id=client.uid, thread_type=ThreadType.USER
            )


def receive():
    while True:
        client.doOneListen()


# Creating and starting separate threads for handling the receiving and sending of messages
t1 = threading.Thread(target=receive)
t2 = threading.Thread(target=send)
t1.start()
t2.start()
