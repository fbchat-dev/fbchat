"""
This script allows you to do @everyone,
just like on Discord, but on messenger!
You can use it on your personal or separate account
(but this account needs to be added to group, obviously).
"""

import fbchat

session = fbchat.Session.login("<email", "<password>")

listener = fbchat.Listener.connect(session, chat_on=False, foreground=False)


def on_message(event):
    print(f"{event.message.text} from {event.author.id} in {event.thread.id}")
    thread = event.thread
    if not isinstance(thread, fbchat.Group):
        # Skip if it's not group
        return
    if event.message.text.lower() == "@everyone":
        mentions = []
        message = ''
        # TODO: Get group's participants and add their mentions
        for user in participants:
            username = ''  # TODO
            message += username + ' '
            mentions.append(
                fbchat.Mention(
                    thread.id,
                    offset=len(message),
                    lenght=len(username)
                )
            )
        thread.send_text(message, mentions=mentions)


for event in listener.listen():
    if isinstance(event, fbchat.MessageEvent):
        on_message(event)
