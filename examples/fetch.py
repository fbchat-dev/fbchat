# -*- coding: UTF-8 -*-

from fbchat import Client
from fbchat.models import *

client = Client("<email>", "<password>")

# Fetches a list of all users you're currently chatting with, as `User` objects
users = client.getAllUsers()

print('user IDs: {}'.format(user.uid for user in users))
print("user's names: {}".format(user.name for user in users))


# If we have a user id, we can use `getUserInfo` to fetch a `User` object
user = client.getUserInfo('<user id>')
# We can also query both mutiple users together, which returns list of `User` objects
users = client.getUserInfo('<1st user id>', '<2nd user id>', '<3rd user id>')

print('User INFO: {}'.format(user))
print("User's INFO: {}".format(users))


# `getUsers` searches for the user and gives us a list of the results,
# and then we just take the first one, aka. the most likely one:
user = client.getUsers('<name of user>')[0]

print('user ID: {}'.format(user.uid))
print("user's name: {}".format(user.name))


# Fetches a list of all threads you're currently chatting with
threads = client.getThreadList()
# Fetches the next 10 threads
threads += client.getThreadList(start=20, length=10)

print("Thread's INFO: {}".format(threads))


# Gets the last 10 messages sent to the thread
messages = client.getThreadInfo(last_n=10, thread_id='<thread id>', thread_type=ThreadType)
# Since the message come in reversed order, reverse them
messages.reverse()

# Prints the content of all the messages
for message in messages:
    print(message.body)


# Here should be an example of `getUnread`
