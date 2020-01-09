import fbchat

# Subclass fbchat.Client and override required methods
class EchoBot(fbchat.Client):
    def on_message(self, author_id, message_object, thread, **kwargs):
        self.mark_as_delivered(thread.id, message_object.id)
        self.mark_as_read(thread.id)

        print("{} from {} in {}".format(message_object, thread))

        # If you're not the author, echo
        if author_id != self.session.user_id:
            thread.send(message_object)


session = fbchat.Session.login("<email>", "<password>")

echo_bot = EchoBot(session)
echo_bot.listen()
