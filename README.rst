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
    # IMAGES
    client.sendLocalImage(friend.uid,message='<message text>',image='<path/to/image/file>') # send local image
    imgurl = "http://i.imgur.com/LDQ2ITV.jpg"
    client.sendRemoteImage(friend.uid,message='<message text>', image=imgurl) # send image from image url


Getting user info from user id
==============================

.. code-block:: python

    friend1 = client.getUsers('<friend name 1>')[0]
    friend2 = client.getUsers('<friend name 2>')[0]
    friend1_info = client.getUserInfo(friend1.uid) # returns dict with details
    both_info = client.getUserInfo(friend1.uid,friend2.uid) # query both together, returns list of dicts
    friend1_name = friend1_info['name'] 


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
    
    bot = EchoBot("<email>", "<password>")
    bot.listen()


Saving session
==========================

.. code-block:: python
    
    client.saveSession(sessionfile)


Loading session
==========================

.. code-block:: python
    
    client = fbchat.Client(None, None, do_login=False)
    client.loadSession(sessionfile)


Authors
=======

Taehoon Kim / `@carpedm20 <http://carpedm20.github.io/about/>`__
