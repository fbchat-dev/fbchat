Contributing to ``fbchat``
==========================

Thanks for reading this, all contributions are very much welcome!

Please be aware that ``fbchat`` uses `Scemantic Versioning <https://semver.org/>`__
That means that if you're submitting a breaking change, it will probably take a while before it gets considered.

In that case, you can point your PR to the ``2.0.0-dev`` branch, where the API is being properly developed.
Otherwise, just point it to ``master``.

Development Environment
-----------------------

You can use `flit` to install the package as a symlink:

.. code-block::

    $ # *nix:
    $ flit install --symlink
    $ # Windows:
    $ flit install --pth-file

After that, you can ``import`` the module as normal.

Before committing, you should run ``black .`` in the main directory, to format your code.

Testing Environment
-------------------

The tests use `pytest <https://docs.pytest.org/>`__, and to work they need two Facebook accounts, and a group thread between these.
To set these up, you should export the following environment variables:

``client1_email``, ``client1_password``, ``client2_email``, ``client2_password`` and ``group_id``

If you're not able to do this, consider simply running ``pytest -m offline``.

And if you're adding new functionality, if possible, make sure to create a new test for it.
