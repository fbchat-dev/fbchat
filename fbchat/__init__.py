# -*- coding: UTF-8 -*-

"""
    fbchat
    ~~~~~~

    Facebook Chat (Messenger) for Python

    :copyright: (c) 2015 by Taehoon Kim.
    :license: BSD, see LICENSE for more details.
"""

from datetime import datetime
from .client import *

__copyright__ = 'Copyright 2015 - {} by Taehoon Kim'.format(datetime.now().year)
__version__ = '1.0.1'
__license__ = 'BSD'
__author__ = 'Taehoon Kim; Moreels Pieter-Jan; Mads Marquart'
__email__ = 'carpedm20@gmail.com'
__source__ = 'https://github.com/carpedm20/fbchat/'
__description__ = 'Facebook Chat (Messenger) for Python'

__all__ = [
    'Client',
]
