# -*- coding: UTF-8 -*-

from fbchat import log, Client
from fbchat.models import *


class RemoveBot(Client):
    def onMessage(self, author_id, message_object, thread_id, thread_type, **kwargs):
        # We can only kick people from group chats, so no need to try if it's a user chat
        if message_object.text == "Remove me!" and thread_type == ThreadType.GROUP:
            log.info("{} will be removed from {}".format(author_id, thread_id))
            self.removeUserFromGroup(author_id, thread_id=thread_id)
        else:
            # Sends the data to the inherited onMessage, so that we can still see when a message is recieved
            super(RemoveBot, self).onMessage(
                author_id=author_id,
                message_object=message_object,
                thread_id=thread_id,
                thread_type=thread_type,
                **kwargs
            )


client = RemoveBot("<email>", "<password>")
client.listen()
