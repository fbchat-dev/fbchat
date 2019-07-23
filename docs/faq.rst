.. _faq:

FAQ
===

Version X broke my installation
-------------------------------

We try to provide backwards compatibility where possible, but since we're not part of Facebook,
most of the things may be broken at any point in time

Downgrade to an earlier version of ``fbchat``, run this command

.. code-block:: sh

    $ pip install fbchat==<X>

Where you replace ``<X>`` with the version you want to use


Will you be supporting creating posts/events/pages and so on?
-------------------------------------------------------------

We won't be focusing on anything else than chat-related things. This API is called ``fbCHAT``, after all ;)


Submitting Issues
-----------------

If you're having trouble with some of the snippets, or you think some of the functionality is broken,
please feel free to submit an issue on `GitHub <https://github.com/carpedm20/fbchat>`_.
You should first login with ``logging_level`` set to ``logging.DEBUG``::

    from fbchat import Client
    import logging
    client = Client('<email>', '<password>', logging_level=logging.DEBUG)

Then you can submit the relevant parts of this log, and detailed steps on how to reproduce

.. warning::
    Always remove your credentials from any debug information you may provide us.
    Preferably, use a test account, in case you miss anything
