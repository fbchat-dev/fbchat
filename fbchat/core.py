# -*- coding: UTF-8 -*-


"""
Core components for fbchat
"""


import requests
import time

class Client:
    """A client for the Facebook Chat (Messenger).

    See http://github.com/carpedm20/fbchat for complete
    documentation for the API.

    """

    def __init__(self, email, password):
        """A client for the Facebook Chat (Messenger).

        :param email: Facebook `email` or `id` or `phone number`
        :param password: Facebook account password

            import fbchat
            chat = fbchat.Client(email, password)

        """

        if not (email and password):
            raise Exception("id and password or config is needed")

        
        self.email = email
        self.password = password

    def listen(self):
        pass

    def getUserId(self):
        pass

    def sendMessage(self):
        pass

    def sendSticker(self):
        pass

    def markAsRead(self):
        pass
