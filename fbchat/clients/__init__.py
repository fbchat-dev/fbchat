# -*- coding: UTF-8 -*-

from __future__ import unicode_literals

from .base import BaseClient
from .fetch import FetcherClient
from .cache import CacherClient
from .listen import ListenerClient
from .get import GetterClient
from .search import SearcherClient
from .send import SenderClient
from .control import GroupControllerClient
from .interraction import ThreadInterracterClient
from .config import ThreadConfigurerClient


class FacebookClient(
        ThreadConfigurerClient,
        ThreadInterracterClient,
        GroupControllerClient,
        SenderClient,
        SearcherClient,
        GetterClient,
        ListenerClient,
        CacherClient,
        FetcherClient,
        BaseClient
    ):
    pass
