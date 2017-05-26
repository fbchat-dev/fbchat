# -*- coding: UTF-8 -*-

from fbchat import log, Client
from fbchat.models import *

class RemoveBot(Client):
    def onMessage(self, author_id, message, thread_id, thread_type, **kwargs):
        # We can only kick people from group chats, so no need to try if it's a user chat
        if message == 'Remove me!' and thread_type == ThreadType.GROUP:
            log.info("{} will be removed from {}".format(author_id, thread_id))
            self.removeUserFromGroup(author_id, thread_id=thread_id)
        else:
            log.info("Message from {} in {} ({}): {}".format(author_id, thread_id, thread_type.name, message))

client = RemoveBot("<email>", "<password>")
client.listen()
