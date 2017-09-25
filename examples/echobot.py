# -*- coding: UTF-8 -*-

from fbchat import log, Client

# Subclass fbchat.Client and override required methods
class EchoBot(Client):
    def onMessage(self, author_id, message, thread_id, thread_type, **kwargs):
        self.markAsDelivered(author_id, thread_id)
        self.markAsRead(author_id)

        log.info("Message from {} in {} ({}): {}".format(author_id, thread_id, thread_type.name, message))

        # If you're not the author, echo
        if author_id != self.uid:
            self.sendMessage(message, thread_id=thread_id, thread_type=thread_type)

client = EchoBot("<email>", "<password>")
client.listen()
