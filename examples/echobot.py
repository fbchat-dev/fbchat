# -*- coding: UTF-8 -*-

from fbchat import log, Client

# Subclass fbchat.Client and override required methods
class EchoBot(Client):
    def onMessage(self, author_id, message_object, thread_id, thread_type, **kwargs):
        self.markAsDelivered(author_id, thread_id)
        self.markAsRead(author_id)

        log.info("{} from {} in {}".format(message_object, thread_id, thread_type.name))

        # If you're not the author, and the message was a message containing text, echo
        if author_id != self.uid and message_object.text is not None:
            self.sendMessage(message_object.text, thread_id=thread_id, thread_type=thread_type)

client = EchoBot("<email>", "<password>")
client.listen()
