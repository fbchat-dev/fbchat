# -*- coding: UTF-8 -*-

from itertools import islice
from fbchat import Client
from fbchat.models import *

client = Client("<email>", "<password>")

# Fetches a list of all users you're currently chatting with, as `User` objects
users = client.fetchAllUsers()

print("users' IDs: {}".format([user.uid for user in users]))
print("users' names: {}".format([user.name for user in users]))


# If we have a user id, we can use `fetchUserInfo` to fetch a `User` object
user = client.fetchUserInfo("<user id>")["<user id>"]
# We can also query both mutiple users together, which returns list of `User` objects
users = client.fetchUserInfo("<1st user id>", "<2nd user id>", "<3rd user id>")

print("user's name: {}".format(user.name))
print("users' names: {}".format([users[k].name for k in users]))


# `searchForUsers` searches for the user and gives us a list of the results,
# and then we just take the first one, aka. the most likely one:
user = client.searchForUsers("<name of user>")[0]

print("user ID: {}".format(user.uid))
print("user's name: {}".format(user.name))
print("user's photo: {}".format(user.photo))
print("Is user client's friend: {}".format(user.is_friend))


# Fetches a list of the 20 top threads you're currently chatting with
threads = client.fetchThreadList()
# Fetches the next 10 threads
threads += client.fetchThreadList(offset=20, limit=10)

print("Threads: {}".format(threads))


# Gets the last 10 messages sent to the thread
messages = client.fetchThreadMessages(thread_id="<thread id>", limit=10)
# Since the message come in reversed order, reverse them
messages.reverse()

# Prints the content of all the messages
for message in messages:
    print(message.text)


# If we have a thread id, we can use `fetchThreadInfo` to fetch a `Thread` object
thread = client.fetchThreadInfo("<thread id>")["<thread id>"]
print("thread's name: {}".format(thread.name))
print("thread's type: {}".format(thread.type))


# `searchForThreads` searches works like `searchForUsers`, but gives us a list of threads instead
thread = client.searchForThreads("<name of thread>")[0]
print("thread's name: {}".format(thread.name))
print("thread's type: {}".format(thread.type))


# Here should be an example of `getUnread`


# Print image url for 20 last images from thread.
images = client.fetchThreadImages("<thread id>")
for image in islice(images, 20):
    print(image.large_preview_url)
