# -*- coding: UTF-8 -*-

from fbchat import Client, Group, Message


class Bot(Client):

    def on_message(self, message):
        thread = message.thread

        # Prevent the bot from answering the bot's own messages
        if message in self.sent_messages:
            return

        # If the message-text contains the letters 'admin'
        if 'admin' in message.text.lower():
            # Send various messages, based on the thread and the admin-status
            if not isinstance(thread, Group):
                self.send_text(thread, "This isn't a group, no admins here!")
            elif self in thread.admins:
                self.send_text(thread, "Yup, I'm an admin")
            else:
                self.send_text(thread, "Nope :'(")

        # If the message-text contains the letters 'like'
        if 'like' in message.text.lower():
            # React to the message with a thumbs up
            self.set_reaction(message, reaction='👍')

        # If the message contains any images
        if message.images:
            # Send a message with the same images
            self.send(thread, Message(images=message.images,
                                      text='Here, have your images back!'))

        # If the message contains a video
        if message.video:
            print(message.video, dict(message.video))

        # If the message contains a file
        if message.file:
            print(message.file, dict(message.file))

        # If you're mentioned
        if self in (mention.thread for mention in message.mentions):
            print('{.name} tagged me!'.format(message.author))

    def on_user_removed(self, thread, actor, subject):
        # If you're the subject or the actor
        if self in [subject, actor]:
            return

        # If the subject is one of your friends
        if subject.is_friend:
            self.send_text(thread, 'Aww, this person was my friend!')

    def on_users_added(self, thread, actor, subject):
        # If you've been added to the thread
        if subject == self:
            self.send_text(thread, 'Thanks for adding me!')

    def on_reaction_set(self, actor, message, old_reaction):
        # If old_reaction is set, the reaction was changed
        if old_reaction:
            self.send_text(message.thread, 'Stop changing your reactions!')


bot = Bot("<email>", "<password>")
bot.listen()
