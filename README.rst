======
fbchat
======


Facebook Chat (`Messenger <https://www.messenger.com/>`__) for Python. This project was inspired by `facebook-chat-api <https://github.com/Schmavery/facebook-chat-api>`__.

**No XMPP or API key is needed**. Just use your ID and PASSWORD.


Installation
============

Simple:

.. code-block:: console

    $ pip install fbchat


Example
=======

.. code-block:: console

    import fbchat

    client = fbchat.Client("YOUR_ID", "YOUR_PASSWORD")


Sending a Message
=================

.. code-block:: python
    
    friends = client.getUsers("FRIEND'S NAME")  # return a list of names
    friend = friends[0]
    sent = client.send(friend.uid, "Your Message")
    if sent:
        print("Message sent successfully")


Getting last messages sent
==========================

.. code-block:: python
    
    last_messages = client.getThreadInfo(friend.uid,0)
    # messages come in reversed order
    last_messages.reverse()
    
    for message in last_messages:
        print(message.body)


Authors
=======

Taehoon Kim / `@carpedm20 <http://carpedm20.github.io/about/>`__
