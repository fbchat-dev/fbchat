.. highlight:: python
.. fbchat documentation master file, created by
   sphinx-quickstart on Thu May 25 15:43:01 2017.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

.. This documentation's layout is heavily inspired by requests' layout: https://requests.readthedocs.io
   Some documentation is also partially copied from facebook-chat-api: https://github.com/Schmavery/facebook-chat-api

fbchat: Facebook Chat (Messenger) for Python
============================================

Release v\ |version|. (:ref:`install`)

.. generated with: https://img.shields.io/badge/license-BSD-blue.svg

.. image:: /_static/license.svg
    :target: https://github.com/carpedm20/fbchat/blob/master/LICENSE.txt

.. generated with: https://img.shields.io/badge/python-2.7%2C%203.4%2C%203.5%2C%203.6-blue.svg

.. image:: /_static/python-versions.svg
    :target: https://pypi.python.org/pypi/fbchat

Facebook Chat (`Messenger <https://www.facebook.com/messages/>`__) for Python. This project was inspired by `facebook-chat-api <https://github.com/Schmavery/facebook-chat-api>`__.

**No XMPP or API key is needed**. Just use your email and password.

Currently `fbchat` support Python 2.7, 3.4, 3.5 and 3.6:

`fbchat` works by emulating the browser. This means doing the exact same GET/POST requests and tricking Facebook into thinking we're accessing the website normally.
Because we're doing it this way, this API requires the credentials of a Facebook account.

.. warning::
    We are not responsible if your account gets banned for spammy activities such as sending lots of messages to people you don't know, sending messages very quickly, sending spammy looking URLs, logging in and out very quickly... Be responsible Facebook citizens.

.. note::
    Facebook now has an `official API <https://developers.facebook.com/docs/messenger-platform>`_ for chat bots, so if you're familiar with node.js, this might be what you're looking for.

Overview
--------

.. toctree::
    :maxdepth: 2

    install
    intro
    examples
    testing
    api
    todo
