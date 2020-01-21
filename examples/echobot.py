import fbchat

session = fbchat.Session.login("<email>", "<password>")

listener = fbchat.Listener.connect(session, chat_on=False, foreground=False)


def on_message(event):
    print(f"{event.message.text} from {event.author.id} in {event.thread.id}")
    # If you're not the author, echo
    if event.author.id != session.user_id:
        event.thread.send_text(event.message.text)


for event in listener.listen():
    if isinstance(event, fbchat.MessageEvent):
        on_message(event)
