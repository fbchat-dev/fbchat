# -*- coding: UTF-8 -*-

from fbchat import *

c = Client('<email>', '<password>')

# Display the first 10 threads in your chat window, newly updated first
threads = c.get_threads(limit=10)
print(threads)

# Do some action for a while
sleep(10)

# Update the internal cache with the new messages that may have been
# sent/recieved in the meantime
c.update()

# Update the threads
threads = c.get_threads(limit=10)

# If we found any threads
if len(threads) > 0:
    # Select the lastest thread
    t = threads[0]

    # Display the type of the thread
    print(type(t))

    # Display the last 10 messages in that thread, newest first
    for m in c.get_messages(t, limit=10):
        print(m)

    # Same as above, alternate method using iterables
    from itertools import islice
    for m in islice(c.get_messages(t), 10):
        print(m)

    # If the message contains an attachment, for example an image, we can
    # retrieve the full url to that attachment
    m, = c.get_messages(t, limit=1)
    if m.images:
        print(c.get_url(m.images[0]))

# Display the name of all your friends
print([f.name for f in c.get_friends()])

# If we have the name of a thread in advance
thread = c.get_threads_from_ids(1234567890)

# Otherwise we could try a search
possible_threads = c.search_for_thread('<thread name>', limit=10)
print(possible_threads)
