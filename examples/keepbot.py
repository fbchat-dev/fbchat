import fbchat

# Change this to your group id
old_thread_id = "1234567890"

# Change these to match your liking
old_color = "#0084ff"
old_emoji = "👍"
old_title = "Old group chat name"
old_nicknames = {
    "12345678901": "User nr. 1's nickname",
    "12345678902": "User nr. 2's nickname",
    "12345678903": "User nr. 3's nickname",
    "12345678904": "User nr. 4's nickname",
}

session = fbchat.Session.login("<email>", "<password>")

listener = fbchat.Listener.connect(session, chat_on=False, foreground=False)


def on_color_set(event: fbchat.ColorSet):
    if old_thread_id != event.thread.id:
        return
    if old_color != event.color:
        print(f"{event.author.id} changed the thread color. It will be changed back")
        event.thread.set_color(old_color)


def on_emoji_set(event: fbchat.EmojiSet):
    if old_thread_id != event.thread.id:
        return
    if old_emoji != event.emoji:
        print(f"{event.author.id} changed the thread emoji. It will be changed back")
        event.thread.set_emoji(old_emoji)


def on_title_set(event: fbchat.TitleSet):
    if old_thread_id != event.thread.id:
        return
    if old_title != event.title:
        print(f"{event.author.id} changed the thread title. It will be changed back")
        event.thread.set_title(old_title)


def on_nickname_set(event: fbchat.NicknameSet):
    if old_thread_id != event.thread.id:
        return
    old_nickname = old_nicknames.get(event.subject.id)
    if old_nickname != event.nickname:
        print(
            f"{event.author.id} changed {event.subject.id}'s' nickname."
            " It will be changed back"
        )
        event.thread.set_nickname(event.subject.id, old_nickname)


def on_people_added(event: fbchat.PeopleAdded):
    if old_thread_id != event.thread.id:
        return
    if event.author.id != session.user.id:
        print(f"{', '.join(x.id for x in event.added)} got added. They will be removed")
        for added in event.added:
            event.thread.remove_participant(added.id)


def on_person_removed(event: fbchat.PersonRemoved):
    if old_thread_id != event.thread.id:
        return
    # No point in trying to add ourself
    if event.removed.id == session.user.id:
        return
    if event.author.id != session.user.id:
        print(f"{event.removed.id} got removed. They will be re-added")
        event.thread.add_participants([removed.id])


for event in listener.listen():
    if isinstance(event, fbchat.ColorSet):
        on_color_set(event)
    elif isinstance(event, fbchat.EmojiSet):
        on_emoji_set(event)
    elif isinstance(event, fbchat.TitleSet):
        on_title_set(event)
    elif isinstance(event, fbchat.NicknameSet):
        on_nickname_set(event)
    elif isinstance(event, fbchat.PeopleAdded):
        on_people_added(event)
    elif isinstance(event, fbchat.PersonRemoved):
        on_person_removed(event)
