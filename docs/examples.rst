.. highlight:: python
.. _examples:

Examples
========

These are a few examples on how to use `fbchat`. Remember to swap out `<email>` and `<password>` for your email and password


Sending messages
----------------

This will send one of each message type to the specified thread

.. literalinclude:: ../examples/send.py
    :language: python


Getting information
-------------------

This will show the different ways of fetching information about users and threads

.. literalinclude:: ../examples/get.py
    :language: python


Echobot
-------

This will reply to any message with the same message

.. literalinclude:: ../examples/echobot.py
    :language: python


Remove bot
----------

This will remove a user from a group if they write the message `Remove me!`

.. literalinclude:: ../examples/removebot.py
    :language: python


"Keep it"-bot
-------------

This will prevent chat color, emoji, nicknames and chat name from being changed. It will also prevent people from being added and removed

.. literalinclude:: ../examples/keepbot.py
    :language: python
