import fbchat

# Subclass fbchat.Client and override required methods
class EchoBot(fbchat.Client):
    def on_message(self, author_id, message_object, thread_id, thread_type, **kwargs):
        self.mark_as_delivered(thread_id, message_object.uid)
        self.mark_as_read(thread_id)

        print("{} from {} in {}".format(message_object, thread_id, thread_type.name))

        # If you're not the author, echo
        if author_id != self.uid:
            self.send(message_object, thread_id=thread_id, thread_type=thread_type)


session = fbchat.Session.login("<email>", "<password>")

echo_bot = EchoBot(session)
echo_bot.listen()
