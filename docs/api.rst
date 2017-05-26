.. module:: fbchat
.. highlight:: python
.. _api:

Full API
========

If you are looking for information on a specific function, class, or method, this part of the documentation is for you.


.. _api_client:

Client
------

.. todo::
    Write introduction text about `Client`, and add documentation for all events

.. autoclass:: Client(email, password, user_agent=None, max_retries=5, session_cookies=None, logging_level=logging.INFO, set_default_events=True)
    :members:

    .. automethod:: sendRemoteImage(image_url, message=None, thread_id=None, thread_type=ThreadType.USER)
    .. automethod:: sendLocalImage(image_path, message=None, thread_id=None, thread_type=ThreadType.USER)


.. _api_models:

Models
------

These models are used in various functions, both as inputs and return values.
A good tip is to write ``from fbchat.models import *`` at the start of your source, so you can use these models freely

.. automodule:: fbchat.models
    :members:


.. _api_utils:

Utils
-----

These functions and values are used internally by fbchat, and are subject to change. Do **NOT** rely on these to be backwards compatible!

.. automodule:: fbchat.utils
    :members:
