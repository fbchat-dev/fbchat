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

.. code-block:: python

    import fbchat

    client = fbchat.Client("YOUR_ID", "YOUR_PASSWORD")


Sending a Message
=================

.. code-block:: python
    
    friends = client.getUsers("FRIEND'S NAME")  # return a list of names
    friend = friends[0]
    sent = client.send(friend.uid, "Your Message")
    if sent:
        print("Message sent successfully!")


Getting last messages sent
==========================

.. code-block:: python
    
    last_messages = client.getThreadInfo(friend.uid,0)
    last_messages.reverse()  # messages come in reversed order
    
    for message in last_messages:
        print(message.body)


Example Echobot
===============

.. code-block:: python

    import fbchat
    #subclass fbchat.Client and override required methods
    class EchoBot(fbchat.Client): 

        def __init__(self,email, password, debug=True, user_agent=None):            
            fbchat.Client.__init__(self,email, password, debug, user_agent)

        def on_message(self, mid, author_id, author_name, message, metadata):
            self.markAsDelivered(author_id, mid) #mark delivered
            self.markAsRead(author_id) #mark read

            print("%s said: %s"%(author_id, message))

            #if you are not the author, echo
            if str(author_id) != str(self.uid):
                self.send(author_id,message)
    
    bot=EchoBot("<email>", "<password>")
    bot.listen()



Authors
=======

Taehoon Kim / `@carpedm20 <http://carpedm20.github.io/about/>`__
