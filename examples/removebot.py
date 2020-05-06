import fbchat


def on_message(event):
    # We can only kick people from group chats, so no need to try if it's a user chat
    if not isinstance(event.thread, fbchat.Group):
        return
    if event.message.text == "Remove me!":
        print(f"{event.author.id} will be removed from {event.thread.id}")
        event.thread.remove_participant(event.author.id)


session = fbchat.Session.login("<email>", "<password>")
listener = fbchat.Listener(session=session, chat_on=False, foreground=False)
for event in listener.listen():
    if isinstance(event, fbchat.MessageEvent):
        on_message(event)
