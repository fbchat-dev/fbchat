Frequently Asked Questions
==========================

The new version broke my application
------------------------------------

``fbchat`` follows `Scemantic Versioning <https://semver.org/>`__ quite rigorously!

That means that breaking changes can *only* occur in major versions (e.g. ``v1.9.6`` -> ``v2.0.0``).

If you find that something breaks, and you didn't update to a new major version, then it is a bug, and we would be grateful if you reported it!

In case you're stuck with an old codebase, you can downgrade to a previous version of ``fbchat``, e.g. version ``1.9.6``:

.. code-block:: sh

    $ pip install fbchat==1.9.6


Will you be supporting creating posts/events/pages and so on?
-------------------------------------------------------------

We won't be focusing on anything else than chat-related things. This library is called ``fbCHAT``, after all!
