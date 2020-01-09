import fbchat

# Change this to your group id
old_thread_id = "1234567890"

# Change these to match your liking
old_color = fbchat.ThreadColor.MESSENGER_BLUE
old_emoji = "👍"
old_title = "Old group chat name"
old_nicknames = {
    "12345678901": "User nr. 1's nickname",
    "12345678902": "User nr. 2's nickname",
    "12345678903": "User nr. 3's nickname",
    "12345678904": "User nr. 4's nickname",
}


class KeepBot(fbchat.Client):
    def on_color_change(self, author_id, new_color, thread, **kwargs):
        if old_thread_id == thread.id and old_color != new_color:
            print(
                "{} changed the thread color. It will be changed back".format(author_id)
            )
            thread.set_color(old_color)

    def on_emoji_change(self, author_id, new_emoji, thread, **kwargs):
        if old_thread_id == thread.id and new_emoji != old_emoji:
            print(
                "{} changed the thread emoji. It will be changed back".format(author_id)
            )
            thread.set_emoji(old_emoji)

    def on_people_added(self, added_ids, author_id, thread, **kwargs):
        if old_thread_id == thread.id and author_id != self.session.user_id:
            print("{} got added. They will be removed".format(added_ids))
            for added_id in added_ids:
                thread.remove_participant(added_id)

    def on_person_removed(self, removed_id, author_id, thread, **kwargs):
        # No point in trying to add ourself
        if (
            old_thread_id == thread.id
            and removed_id != self.session.user_id
            and author_id != self.session.user_id
        ):
            print("{} got removed. They will be re-added".format(removed_id))
            thread.add_participants(removed_id)

    def on_title_change(self, author_id, new_title, thread, **kwargs):
        if old_thread_id == thread.id and old_title != new_title:
            print(
                "{} changed the thread title. It will be changed back".format(author_id)
            )
            thread.set_title(old_title)

    def on_nickname_change(
        self, author_id, changed_for, new_nickname, thread, **kwargs
    ):
        if (
            old_thread_id == thread.id
            and changed_for in old_nicknames
            and old_nicknames[changed_for] != new_nickname
        ):
            print(
                "{} changed {}'s' nickname. It will be changed back".format(
                    author_id, changed_for
                )
            )
            thread.set_nickname(
                changed_for, old_nicknames[changed_for],
            )


session = fbchat.Session.login("<email>", "<password>")

keep_bot = KeepBot(session)
keep_bot.listen()
