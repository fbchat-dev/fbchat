import fbchat

session = fbchat.Session.login("<email>", "<password>")

client = fbchat.Client(session=session)

# Fetches a list of all users you're currently chatting with, as `User` objects
users = client.fetch_all_users()

print("users' IDs: {}".format([user.id for user in users]))
print("users' names: {}".format([user.name for user in users]))


# If we have a user id, we can use `fetch_user_info` to fetch a `User` object
user = client.fetch_user_info("<user id>")["<user id>"]
# We can also query both mutiple users together, which returns list of `User` objects
users = client.fetch_user_info("<1st user id>", "<2nd user id>", "<3rd user id>")

print("user's name: {}".format(user.name))
print("users' names: {}".format([users[k].name for k in users]))


# `search_for_users` searches for the user and gives us a list of the results,
# and then we just take the first one, aka. the most likely one:
user = client.search_for_users("<name of user>")[0]

print("user ID: {}".format(user.id))
print("user's name: {}".format(user.name))
print("user's photo: {}".format(user.photo))
print("Is user client's friend: {}".format(user.is_friend))


# Fetches a list of the 20 top threads you're currently chatting with
threads = client.fetch_thread_list()
# Fetches the next 10 threads
threads += client.fetch_thread_list(offset=20, limit=10)

print("Threads: {}".format(threads))


# If we have a thread id, we can use `fetch_thread_info` to fetch a `Thread` object
thread = client.fetch_thread_info("<thread id>")["<thread id>"]
print("thread's name: {}".format(thread.name))


# Gets the last 10 messages sent to the thread
messages = thread.fetch_messages(limit=10)
# Since the message come in reversed order, reverse them
messages.reverse()

# Prints the content of all the messages
for message in messages:
    print(message.text)


# `search_for_threads` searches works like `search_for_users`, but gives us a list of threads instead
thread = client.search_for_threads("<name of thread>")[0]
print("thread's name: {}".format(thread.name))


# Here should be an example of `getUnread`


# Print image url for up to 20 last images from thread.
images = list(thread.fetch_images(limit=20))
for image in images:
    if isinstance(image, fbchat.ImageAttachment):
        url = client.fetch_image_url(image.id)
        print(url)
