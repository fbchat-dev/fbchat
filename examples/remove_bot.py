# -*- coding: UTF-8 -*-

from fbchat import *


class RemoveBot(Client):
    def on_text(self, thread, author, text, mentions):
        # We can only kick people from group chats, so no need to try if it's a
        # user chat
        if text == "Remove me!" and isinstance(thread, Group):
            print("{.name} asked to be removed from {.name}".format(author, thread))
            self.remove_user(thread, author)


bot = RemoveBot("<email>", "<password>")
bot.listen()
