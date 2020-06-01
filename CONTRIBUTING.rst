Contributing to ``fbchat``
==========================

Thanks for reading this, all contributions are very much welcome!

Please be aware that ``fbchat`` uses `Scemantic Versioning <https://semver.org/>`__ quite rigorously!
That means that if you're submitting a breaking change, it will probably take a while before it gets considered.

Development Environment
-----------------------

This project uses ``flit`` to configure development environments. You can install it using:

.. code-block:: sh

    $ pip install flit

And now you can install ``fbchat`` as a symlink:

.. code-block:: sh

    $ git clone https://github.com/carpedm20/fbchat.git
    $ cd fbchat
    $ # *nix:
    $ flit install --symlink
    $ # Windows:
    $ flit install --pth-file

This will also install required development tools like ``black``, ``pytest`` and ``sphinx``.

After that, you can ``import`` the module as normal.

Checklist
---------

Once you're done with your work, please follow the steps below:

- Run ``black .`` to format your code.
- Run ``pytest`` to test your code.
- Run ``make -C docs html``, and view the generated docs, to verify that the docs still work.
- Run ``make -C docs spelling`` to check your spelling in docstrings.
- Create a pull request, and point it to ``master`` `here <https://github.com/carpedm20/fbchat/pulls/new>`__.
