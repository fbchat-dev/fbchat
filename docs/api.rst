.. module:: fbchat
.. _api:

.. Note: we're using () to hide the __init__ method where relevant

Full API
========

If you are looking for information on a specific function, class, or method, this part of the documentation is for you.

Client
------

.. autoclass:: Client

Threads
-------

.. autoclass:: Thread()
.. autoclass:: ThreadType(Enum)
    :undoc-members:
.. autoclass:: Page()
.. autoclass:: User()
.. autoclass:: Group()

Messages
--------

.. autoclass:: Message
.. autoclass:: Mention
.. autoclass:: EmojiSize(Enum)
    :undoc-members:
.. autoclass:: MessageReaction(Enum)
    :undoc-members:

Exceptions
----------

.. autoexception:: FBchatException()
.. autoexception:: FBchatFacebookError()

Attachments
-----------

.. autoclass:: Attachment()
.. autoclass:: ShareAttachment()
.. autoclass:: Sticker()
.. autoclass:: LocationAttachment()
.. autoclass:: LiveLocationAttachment()
.. autoclass:: FileAttachment()
.. autoclass:: AudioAttachment()
.. autoclass:: ImageAttachment()
.. autoclass:: VideoAttachment()
.. autoclass:: ImageAttachment()

Miscellaneous
-------------

.. autoclass:: ThreadLocation(Enum)
    :undoc-members:
.. autoclass:: ThreadColor(Enum)
    :undoc-members:
.. autoclass:: ActiveStatus()
.. autoclass:: TypingStatus(Enum)
    :undoc-members:

.. autoclass:: QuickReply
.. autoclass:: QuickReplyText
.. autoclass:: QuickReplyLocation
.. autoclass:: QuickReplyPhoneNumber
.. autoclass:: QuickReplyEmail

.. autoclass:: Poll
.. autoclass:: PollOption

.. autoclass:: Plan
.. autoclass:: GuestStatus(Enum)
    :undoc-members:
