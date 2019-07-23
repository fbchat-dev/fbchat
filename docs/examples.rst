.. _examples:

Examples
========

These are a few examples on how to use ``fbchat``. Remember to swap out ``<email>`` and ``<password>`` for your email and password


Basic example
-------------

This will show basic usage of ``fbchat``

.. literalinclude:: ../examples/basic_usage.py


Interacting with Threads
------------------------

This will interact with the thread in every way ``fbchat`` supports

.. literalinclude:: ../examples/interract.py


Fetching Information
--------------------

This will show the different ways of fetching information about users and threads

.. literalinclude:: ../examples/fetch.py


``Echobot``
-----------

This will reply to any message with the same message

.. literalinclude:: ../examples/echobot.py


Remove Bot
----------

This will remove a user from a group if they write the message ``Remove me!``

.. literalinclude:: ../examples/removebot.py


"Prevent changes"-Bot
---------------------

This will prevent chat color, emoji, nicknames and chat name from being changed.
It will also prevent people from being added and removed

.. literalinclude:: ../examples/keepbot.py
