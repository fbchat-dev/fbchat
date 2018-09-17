# -*- coding: UTF-8 -*-

from __future__ import unicode_literals

from .core import *
from .fetch import *
from .cache import *
from .listen import *
from .get import *
from .search import *
from .send import *
from .control import *
from .interraction import *
from .config import *


class Client(
    ThreadConfigurerClient,
    ThreadInterracterClient,
    GroupControllerClient,
    SenderClient,
    SearcherClient,
    GetterClient,
    ListenerClient,
    CacherClient,
    FetcherClient,
    CoreClient,
):
    pass
