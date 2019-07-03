.. _testing:

Testing
=======

To use the tests, copy ``tests/data.json`` to ``tests/my_data.json`` or type the information manually in the terminal prompts.

- email: Your (or a test user's) email / phone number
- password: Your (or a test user's) password
- group_thread_id: A test group that will be used to test group functionality
- user_thread_id: A person that will be used to test kick/add functionality (This user should be in the group)

Please remember to test all supported python versions.
If you've made any changes to the 2FA functionality, test it with a 2FA enabled account.

If you only want to execute specific tests, pass the function names in the command line (not including the ``test_`` prefix). Example:

.. code-block:: sh

    $ python tests.py sendMessage sessions sendEmoji

.. warning::

    Do not execute the full set of tests in too quick succession. This can get your account temporarily blocked for spam!
    (You should execute the script at max about 10 times a day)
