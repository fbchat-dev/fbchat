import fbchat

# Log the user in
session = fbchat.Session.login("<email>", "<password>")

print("Own id: {}".format(session.user_id))

# Create helper User class
user = fbchat.Thread(session=session, id=session.user_id)

# Send a message to yourself
user.send(fbchat.Message(text="Hi me!"))

# Log the user out
session.logout()
