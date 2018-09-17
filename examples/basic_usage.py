# -*- coding: UTF-8 -*-

# Import the main class
from fbchat import Client

# Login, using your email and credentials
client = Client.login("<email>", "<password>")

# Display data about you
print(client.user)

# Send a message to yourself
message = client.send_text(client.user, "Hi me!")

# Display data about the sent message
print(message)
