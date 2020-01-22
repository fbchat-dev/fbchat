``fbchat`` - Facebook Messenger for Python
==========================================

.. image:: https://badgen.net/pypi/v/fbchat
    :target: https://pypi.python.org/pypi/fbchat
    :alt: Project version

.. image:: https://badgen.net/badge/python/3.5,3.6,3.7,3.8,pypy?list=|
    :target: https://pypi.python.org/pypi/fbchat
    :alt: Supported python versions: 3.5, 3.6, 3.7, 3.8 and pypy

.. image:: https://badgen.net/pypi/license/fbchat
    :target: https://github.com/carpedm20/fbchat/tree/master/LICENSE
    :alt: License: BSD 3-Clause

.. image:: https://readthedocs.org/projects/fbchat/badge/?version=stable
    :target: https://fbchat.readthedocs.io
    :alt: Documentation

.. image:: https://badgen.net/travis/carpedm20/fbchat
    :target: https://travis-ci.org/carpedm20/fbchat
    :alt: Travis CI

.. image:: https://badgen.net/badge/code%20style/black/black
    :target: https://github.com/ambv/black
    :alt: Code style

A powerful and efficient library to interact with
`Facebook's Messenger <https://www.facebook.com/messages/>`__, using just your email and password.

This is *not* an official API, Facebook has that `over here <https://developers.facebook.com/docs/messenger-platform>`__ for chat bots. This library differs by using a normal Facebook account instead.

``fbchat`` currently support:

- Sending many types of messages, with files, stickers, mentions, etc.
- Fetching all messages, threads and images in threads.
- Searching for messages and threads.
- Creating groups, setting the group emoji, changing nicknames, creating polls, etc.
- Listening for, an reacting to messages and other events in real-time.
- Type hints, and it has a modern codebase (e.g. only Python 3.5 and upwards).
- ``async``/``await`` (COMING).

Essentially, everything you need to make an amazing Facebook bot!


Version Warning
---------------
``v2`` is currently being developed at the ``master`` branch and it's highly unstable. If you want to view the old ``v1``, go `here <https://github.com/carpedm20/fbchat/tree/v1>`__.

Additionally, you can view the project's progress `here <https://github.com/carpedm20/fbchat/projects/2>`__.


Caveats
-------

``fbchat`` works by imitating what the browser does, and thereby tricking Facebook into thinking it's accessing the website normally.

However, there's a catch! **Using this library may not comply with Facebook's Terms Of Service!**, so be responsible Facebook citizens! We are not responsible if your account gets banned!

Additionally, **the APIs the library is calling is undocumented!** In theory, this means that your code could break tomorrow, without the slightest warning!
If this happens to you, please report it, so that we can fix it as soon as possible!

.. inclusion-marker-intro-end
.. This message doesn't make sense in the docs at Read The Docs, so we exclude it

With that out of the way, you may go to `Read The Docs <https://fbchat.readthedocs.io/>`__ to see the full documentation!

.. inclusion-marker-installation-start


Installation
------------

.. code-block::

    $ pip install fbchat

If you don't have `pip <https://pip.pypa.io/>`_, `this guide <http://docs.python-guide.org/en/latest/starting/installation/>`_ can guide you through the process.

You can also install directly from source, provided you have ``pip>=19.0``:

.. code-block::

    $ pip install git+https://github.com/carpedm20/fbchat.git

.. inclusion-marker-installation-end


Example Usage
-------------

.. code-block::

    import getpass
    import fbchat
    session = fbchat.Session.login("<email/phone number>", getpass.getpass())
    user = fbchat.User(session=session, id=session.user_id)
    user.send_text("Test message!")

More examples are available `here <https://github.com/carpedm20/fbchat/tree/master/examples>`__.


Maintainer
----------

- Mads Marquart / `@madsmtm <https://github.com/madsmtm>`__


Acknowledgements
----------------

This project was originally inspired by `facebook-chat-api <https://github.com/Schmavery/facebook-chat-api>`__.
