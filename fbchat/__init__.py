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

    'Client',
    #'AsyncClient',
)

logging.getLogger(__name__).addHandler(logging.NullHandler())
