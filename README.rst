======
fbchat
======

.. image:: https://pypip.in/v/fbchat/badge.png?style=flat
    :target: https://pypi.python.org/pypi/fbchat

.. image:: https://pypip.in/d/fbchat/badge.png?style=flat
    :target: https://pypi.python.org/pypi/fbchat

.. image:: https://pypip.in/status/fbchat/badge.svg?style=flat
    :target: https://pypi.python.org/pypi/fbchat

.. image:: https://pypip.in/license/fbchat/badge.svg?style=flat
    :target: https://pypi.python.org/pypi/fbchat

Facebook Chat (`Messenger <https://www.messenger.com/>`__) for Python. No XMPP or API key is needed. Just use your ID and PASSWORD.

This project was inspired by `facebook-chat-api <https://github.com/Schmavery/facebook-chat-api>`__.


Documentation
=============




Installation
============

To install fbchat, simply: 

.. code-block:: console

    $ pip install fbchat

Or, you can use:

.. code-block:: console

    $ pip install fbchat

Or, you can also install manually:

.. code-block:: console

    $ git clone git://github.com/carpedm20/fbchat.git
    $ cd fbchat
    $ python setup.py install


Echo bot example
================

.. code-block:: console

    import fbchat

    client = fbchat.Client("YOUR_ID", "YOUR_PASSWORD")
    for op in client.listen():
         client.sendMessage(op.message, op.sender)


Authors
=======

Taehoon Kim / `@carpedm20 <http://carpedm20.github.io/about/>`__
