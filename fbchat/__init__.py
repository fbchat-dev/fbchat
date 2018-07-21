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

from .base import Base # noqa
from .get import Get # noqa
from .listener import Listener # noqa
from .message_management import MessageManagement # noqa
from .search import Search # noqa
from .send import Send # noqa
from .thread_control import ThreadControl # noqa
from .thread_interraction import ThreadInterraction # noqa
from .thread_options import ThreadOptions # noqa

from .client import Client

__title__ = 'fbchat'
__version__ = '2.0.0'
__description__ = 'Facebook Chat (Messenger) for Python'

__copyright__ = 'Copyright 2015 - 2018 by Taehoon Kim'
__license__ = 'BSD 3-Clause'

__author__ = 'Taehoon Kim; Moreels Pieter-Jan; Mads Marquart'
__email__ = 'carpedm20@gmail.com'

__all__ = [
    'Message',
    'Mention',

    'Size',
    'Colour',
    'Color',

    'FacebookError',

    'Thread',
    'User',
    'Group',
    'Page',

    'Client',
]

logging.getLogger(__name__).addHandler(logging.NullHandler())
