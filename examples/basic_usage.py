import fbchat

# Log the user in
session = fbchat.Session.login("<email>", "<password>")

print("Own id: {}".format(sesion.user_id))

# Create helper client class
client = fbchat.Client(session)

# Send a message to yourself
client.send(
    fbchat.Message(text="Hi me!"),
    thread_id=session.user_id,
    thread_type=fbchat.ThreadType.USER,
)

# Log the user out
session.logout()
