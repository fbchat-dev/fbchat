# -*- coding: UTF-8 -*-

from __future__ import unicode_literals
from .base import Base
from .get import Get
from .listener import Listener
from .message_management import MessageManagement
from .search import Search
from .send import Send
from .thread_control import ThreadControl
from .thread_interraction import ThreadInterraction
from .thread_options import ThreadOptions


# Actual order here is still to be determined
class Client(ThreadOptions, ThreadInterraction, ThreadControl, Send, Search,
             MessageManagement, Get, Listener, Base):
    pass
