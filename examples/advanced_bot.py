# -*- coding: UTF-8 -*-

from fbchat import Client, Group, FileMessage, Image, Video


class Bot(FacebookClient):
    def on_message(self, message):
        # Prevent the bot from recieving `on_` events bot's own messages
        if message in self.sent_messages:
            return
        return super(self, Bot).on_message(message)

        # If the message-text contains the letters 'admin'
        if "admin" in message.text.lower():
            # Send various messages, based on the thread and the admin-status
            if not isinstance(thread, Group):
                self.send_text(thread, "This isn't a group, no admins here!")
            elif self in thread.admins:
                self.send_text(thread, "Yup, I'm an admin")
            else:
                self.send_text(thread, "Nope :'(")

        # If the message contains the letters 'like'
        if "like" in message.text.lower():
            # React to the message with a thumbs up
            self.set_reaction(message, reaction="👍")

        if message.files:
            # If the message contains any images
            images = [x for x in message.files if isinstance(x, Image)]
            if images:
                pass
                # Send a message with the same images
                # self.send_files(thread, text='Here, have your images back!', files=images)

            # If the message contains a video
            videos = [x for x in message.files if isinstance(x, Video)]
            if videos:
                print(videos[0], vars(videos[0]))

        # If you're mentioned
        if self in (mention.thread for mention in message.mentions):
            print("{.name} tagged me!".format(message.author))

    def on_user_removed(self, thread, actor, subject):
        # If you're the subject or the actor
        if self in [subject, actor]:
            return

        # If the subject is one of your friends
        if subject.is_friend:
            self.send_text(thread, "Aww, this person was my friend!")

    def on_users_added(self, thread, actor, subject):
        # If you've been added to the thread
        if subject == self:
            self.send_text(thread, "Thanks for adding me!")

    def on_reaction_set(self, actor, message, old_reaction):
        # If old_reaction is set, the reaction was changed
        if old_reaction:
            self.send_text(message.thread, "Stop changing your reactions!")


bot = Bot("<email>", "<password>")
bot.listen()
