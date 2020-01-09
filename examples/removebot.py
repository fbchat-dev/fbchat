import fbchat


class RemoveBot(fbchat.Client):
    def on_message(self, author_id, message_object, thread, **kwargs):
        # We can only kick people from group chats, so no need to try if it's a user chat
        if message_object.text == "Remove me!" and isinstance(thread, fbchat.Group):
            print("{} will be removed from {}".format(author_id, thread))
            thread.remove_participant(author_id)
        else:
            # Sends the data to the inherited on_message, so that we can still see when a message is recieved
            super(RemoveBot, self).on_message(
                author_id=author_id,
                message_object=message_object,
                thread=thread,
                **kwargs,
            )


session = fbchat.Session.login("<email>", "<password>")

remove_bot = RemoveBot(session)
remove_bot.listen()
