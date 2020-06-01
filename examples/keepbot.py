# This example uses the `blinker` library to dispatch events. See echobot.py for how
# this could be done differenly. The decision is entirely up to you!
import fbchat
import blinker

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

# Create a blinker signal
events = blinker.Signal()

# Register various event handlers on the signal
@events.connect_via(fbchat.ColorSet)
def on_color_set(sender, event: fbchat.ColorSet):
    if old_thread_id != event.thread.id:
        return
    if old_color != event.color:
        print(f"{event.author.id} changed the thread color. It will be changed back")
        event.thread.set_color(old_color)


@events.connect_via(fbchat.EmojiSet)
def on_emoji_set(sender, event: fbchat.EmojiSet):
    if old_thread_id != event.thread.id:
        return
    if old_emoji != event.emoji:
        print(f"{event.author.id} changed the thread emoji. It will be changed back")
        event.thread.set_emoji(old_emoji)


@events.connect_via(fbchat.TitleSet)
def on_title_set(sender, event: fbchat.TitleSet):
    if old_thread_id != event.thread.id:
        return
    if old_title != event.title:
        print(f"{event.author.id} changed the thread title. It will be changed back")
        event.thread.set_title(old_title)


@events.connect_via(fbchat.NicknameSet)
def on_nickname_set(sender, event: fbchat.NicknameSet):
    if old_thread_id != event.thread.id:
        return
    old_nickname = old_nicknames.get(event.subject.id)
    if old_nickname != event.nickname:
        print(
            f"{event.author.id} changed {event.subject.id}'s' nickname."
            " It will be changed back"
        )
        event.thread.set_nickname(event.subject.id, old_nickname)


@events.connect_via(fbchat.PeopleAdded)
def on_people_added(sender, event: fbchat.PeopleAdded):
    if old_thread_id != event.thread.id:
        return
    if event.author.id != session.user.id:
        print(f"{', '.join(x.id for x in event.added)} got added. They will be removed")
        for added in event.added:
            event.thread.remove_participant(added.id)


@events.connect_via(fbchat.PersonRemoved)
def on_person_removed(sender, event: fbchat.PersonRemoved):
    if old_thread_id != event.thread.id:
        return
    # No point in trying to add ourself
    if event.removed.id == session.user.id:
        return
    if event.author.id != session.user.id:
        print(f"{event.removed.id} got removed. They will be re-added")
        event.thread.add_participants([event.removed.id])


# Login, and start listening for events
session = fbchat.Session.login("<email>", "<password>")
listener = fbchat.Listener(session=session, chat_on=False, foreground=False)

for event in listener.listen():
    # Dispatch the event to the subscribed handlers
    events.send(type(event), event=event)
