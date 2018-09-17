# -*- coding: UTF-8 -*-

"""Facebook Chat (Messenger) for Python

Copyright:
    (c) 2015 - 2018 by Taehoon Kim

License:
    BSD 3-Clause, see LICENSE for more details
"""

from __future__ import unicode_literals

import logging

from .models import *
from .clients import *

# from .async import AsyncClient

__title__ = 'fbchat'
__version__ = '2.0.0'
__description__ = "Facebook Chat (Messenger) for Python"

__copyright__ = "Copyright 2015 - 2018 by Taehoon Kim"
__license__ = "BSD 3-Clause"

__author__ = "Taehoon Kim"
__email__ = "carpedm20@gmail.com"


class Client(object):
    def __init__(self, *args, **kwargs):
        raise Exception("""You've updated to version %s of the library, \
which contains a lot of API changes and breaking changes. \
Please update your code or downgrade to a previous version. \
You can downgrade to a specific version using eg. `pip install fbchat=1.3.9`.\
""" % __version__)


__all__ = (
    #'Event',
    #'Action',
    #'Message',

    'Thread',
    'User',
    'Group',
    'Page',

    'Sticker',
    'Emoji',
    'Text',

    'FacebookError',
    'FacebookSession',

    'FacebookClient',
    #'AsyncClient',

    'Client',
)

logging.getLogger(__name__).addHandler(logging.NullHandler())
