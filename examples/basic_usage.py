import fbchat

# Log the user in
session = fbchat.Session.login("<email>", "<password>")

print("Own id: {}".format(session.user.id))

# Send a message to yourself
session.user.send_text("Hi me!")

# Log the user out
session.logout()
