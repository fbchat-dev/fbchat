Introduction
============

Welcome, this page will guide you through the basic concepts of using ``fbchat``.

The hardest, and most error prone part is logging in, and managing your login session, so that is what we will look at first.


Logging In
----------

Everything in ``fbchat`` starts with getting an instance of `Session`. Currently there are two ways of doing that, `Session.login` and `Session.from_cookies`.

The follow example will prompt you for you password, and use it to login::

    import getpass
    import fbchat
    session = fbchat.Session.login("<email/phone number>", getpass.getpass())
    # If your account requires a two factor authentication code:
    session = fbchat.Session.login(
        "<your email/phone number>",
        getpass.getpass(),
        lambda: getpass.getpass("2FA code"),
    )

However, **this is not something you should do often!** Logging in/out all the time *will* get your Facebook account locked!

Instead, you should start by using `Session.login`, and then store the cookies with `Session.get_cookies`, so that they can be used instead the next time your application starts.

Usability-wise, this is also better, since you won't have to re-type your password every time you want to login.

The following, quite lengthy, yet very import example, illustrates a way to do this:

.. literalinclude:: ../examples/session_handling.py

Assuming you have successfully completed the above, congratulations! Using ``fbchat`` should be mostly trouble free from now on!


Understanding Thread Ids
------------------------

At the core of any thread is its unique identifier, its ID.

A thread basically just means "something I can chat with", but more precisely, it can refer to a few things:
- A Messenger group thread (`Group`)
- The conversation between you and a single Facebook user (`User`)
- The conversation between you and a Facebook Page (`Page`)

You can get your own user ID from `Session.user` with ``session.user.id``.

Getting the ID of a specific group thread is fairly trivial, you only need to login to `<https://www.messenger.com/>`_, click on the group you want to find the ID of, and then read the id from the address bar.
The URL will look something like this: ``https://www.messenger.com/t/1234567890``, where ``1234567890`` would be the ID of the group.

The same method can be applied to some user accounts, though if they have set a custom URL, then you will have to use a different method.

An image to illustrate the process is shown below:

.. image:: /_static/find-group-id.png
    :alt: An image illustrating how to find the ID of a group

Once you have an ID, you can use it to create a `Group` or a `User` instance, which will allow you to do all sorts of things. To do this, you need a valid, logged in session::

    group = fbchat.Group(session=session, id="<The id you found>")
    # Or for user threads
    user = fbchat.User(session=session, id="<The id you found>")

Just like threads, every message, poll, plan, attachment, action etc. you send or do on Facebook has a unique ID.

Below is an example of using such a message ID to get a `Message` instance::

    # Provide the thread the message was created in, and it's ID
    message = fbchat.Message(thread=user, id="<The message id>")


Fetching Information
--------------------

Managing these ids yourself quickly becomes very cumbersome! Luckily, there are other, easier ways of getting `Group`/`User` instances.

You would start by creating a `Client` instance, which is basically just a helper on top of `Session`, that will allow you to do various things::

    client = fbchat.Client(session=session)

Now, you could search for threads using `Client.search_for_threads`, or fetch a list of them using `Client.fetch_threads`::

    # Fetch the 5 most likely search results
    # Uses Facebook's search functions, you don't have to specify the whole name, first names will usually be enough
    threads = list(client.search_for_threads("<name of the thread to search for>", limit=5))
    # Fetch the 5 most recent threads in your account
    threads = list(client.fetch_threads(limit=5))

Note the `list` statements; this is because the methods actually return `generators <https://wiki.python.org/moin/Generators>`__. If you don't know what that means, don't worry, it is just something you can use to make your code faster later.

The examples above will actually fetch `UserData`/`GroupData`, which are subclasses of `User`/`Group`. These model have extra properties, so you could for example print the names and ids of the fetched threads like this::

    for thread in threads:
        print(f"{thread.id}: {thread.name}")

Once you have a thread, you can use that to fetch the messages therein::

    for message in thread.fetch_messages(limit=20):
        print(message.text)


Interacting with Threads
------------------------

Once you have a `User`/`Group` instance, you can do things on them as described in `ThreadABC`, since they are subclasses of that.

Some functionality, like adding users to a `Group`, or blocking a `User`, logically only works the relevant threads, so see the full API documentation for that.

With that out of the way, let's see some examples!

The simplest way of interacting with a thread is by sending a message::

    # Send a message to the user
    message = user.send_text("test message")

There are many types of messages you can send, see the full API documentation for more.

Notice how we held on to the sent message? The return type i a `Message` instance, so you can interact with it afterwards::

    # React to the message with the 😍 emoji
    message.react("😍")

Besides sending messages, you can also interact with threads in other ways. An example is to change the thread color::

    # Will change the thread color to the default blue
    thread.set_color("#0084ff")


Listening & Events
------------------

Now, we are finally at the point we have all been waiting for: Creating an automatic Facebook bot!

To get started, you create the functions you want to call on certain events::

    def my_function(event: fbchat.MessageEvent):
        print(f"Message from {event.author.id}: {event.message.text}")

Then you create a `fbchat.Listener` object::

    listener = fbchat.Listener(session=session, chat_on=False, foreground=False)

Which you can then use to receive events, and send them to your functions::

    for event in listener.listen():
        if isinstance(event, fbchat.MessageEvent):
            my_function(event)

View the :ref:`examples` to see some more examples illustrating the event system.
