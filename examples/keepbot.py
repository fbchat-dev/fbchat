# -*- coding: UTF-8 -*-

from fbchat import log, Client
from fbchat.models import *

# Change this to your group id
old_thread_id = '1234567890'

# Change these to match your liking
old_color = ThreadColor.MESSENGER_BLUE
old_emoji = '👍'
old_title = 'Old school'
old_nicknames = {
    '12345678901': 'Old School user nr. 1',
    '12345678902': 'Old School user nr. 2',
    '12345678903': 'Old School user nr. 3',
    '12345678904': 'Old School user nr. 4'
}

class KeepBot(Client):
    def onColorChange(self, mid, author_id, new_color, thread_id, thread_type, ts, metadata, msg):
        if old_thread_id == thread_id and old_color != new_color:
            log.info("{} changed the thread color. It will be changed back".format(author_id))
            self.changeThreadColor(old_color, thread_id=thread_id)

    def onEmojiChange(self, mid, author_id, new_emoji, thread_id, thread_type, ts, metadata, msg):
        if old_thread_id == thread_id and new_emoji != old_emoji:
            log.info("{} changed the thread emoji. It will be changed back".format(author_id))
            # Not currently possible in `fbchat`
            # self.changeThreadEmoji(old_emoji, thread_id=thread_id)

    def onPeopleAdded(self, added_ids, author_id, thread_id, msg):
        if old_thread_id == thread_id and author_id != self.uid:
            log.info("{} got added. They will be removed".format(added_ids))
            for added_id in added_ids:
                self.removeUserFromGroup(added_id, thread_id=thread_id)

    def onPersonRemoved(self, removed_id, author_id, thread_id, msg):
        # No point in trying to add ourself
        if old_thread_id == thread_id and removed_id != self.uid and author_id != self.uid:
            log.info("{} got removed. They will be re-added".format(removed_id))
            self.addUsersToGroup(removed_id, thread_id=thread_id)

    def onTitleChange(self, mid, author_id, new_title, thread_id, thread_type, ts, metadata, msg):
        if old_thread_id == thread_id and old_title != new_title:
            log.info("{} changed the thread title. It will be changed back".format(author_id))
            self.changeGroupTitle(old_title, thread_id=thread_id)

    def onNicknameChange(self, mid, author_id, changed_for, new_nickname, thread_id, thread_type, ts, metadata, msg):
        if old_thread_id == thread_id and changed_for in old_nicknames:
            log.info("{} changed {}'s' nickname. It will be changed back".format(author_id, changed_for))
            # Not currently possible in `fbchat`
            # self.changeNickname(old_nicknames[changed_for], changed_for, thread_id=thread_id, thread_type=thread_type)

client = KeepBot("<email>", "<password>")
client.listen()
