# -*- coding: UTF-8 -*-

from fbchat import Client

# Change this to your group id
my_thread_id = 1234567890


class KeepBot(Client):
    def on_image_set(self, thread, actor, old_image):
        if my_thread_id == thread.id and self != actor:
            print('{.name} changed the thread image'.format(actor))
            self.image_set(thread, old_image)

    def on_title_set(self, thread, actor, old_title):
        if my_thread_id == thread.id and self != actor:
            print("{.name} changed the thread title".format(actor))
            self.set_title(thread, old_title)

    def on_nickname_set(self, thread, actor, subject, old_nickname):
        if my_thread_id == thread.id and self != actor:
            print("{.name}'s nickname was changed".format(subject))
            self.set_nickname(thread, subject, old_nickname)

    def on_colour_set(self, thread, actor, old_colour):
        if my_thread_id == thread.id and self != actor:
            print('{.name} changed the thread color'.format(actor))
            self.colour_set(thread, old_colour)

    def on_emoji_set(self, thread, actor, old_emoji):
        if my_thread_id == thread.id and self != actor:
            print('{.name} changed the thread emoji'.format(actor))
            self.emoji_set(thread, old_emoji)


    def on_user_added(self, thread, actor, subject):
        if my_thread_id == thread.id and self not in [actor, subject]:
            print('{.name} got added'.format(subject))
            self.remove_user(thread, subject)

    def on_user_removed(self, thread, actor, subject):
        if my_thread_id == thread.id and self not in [actor, subject]:
            print("{.name} got removed".format(subject))
            self.add_user(thread, subject)


    def on_admin_added(self, thread, actor, subject):
        if my_thread_id == thread.id and self not in [actor, subject]:
            print('{.name} got added'.format(subject))
            self.remove_admin(thread, subject)

    def on_admin_removed(self, thread, actor, subject):
        if my_thread_id == thread.id and self not in [actor, subject]:
            print("{.name} got removed".format(subject))
            self.add_admin(thread, subject)


bot = KeepBot("<email>", "<password>")
bot.listen()
