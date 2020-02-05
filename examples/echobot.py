import fbchat

session = fbchat.Session.login("<email>", "<password>")
listener = fbchat.Listener(session=session, chat_on=False, foreground=False)


@listener.register
def on_message(event: fbchat.MessageEvent):
    print(f"{event.message.text} from {event.author.id} in {event.thread.id}")
    # If you're not the author, echo
    if event.author.id != session.user.id:
        event.thread.send_text(event.message.text)


listener.run()
