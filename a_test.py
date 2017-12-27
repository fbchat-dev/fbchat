#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import logging
from os import environ
from fbchat import Client
from fbchat.models import *

logging.basicConfig(level=logging.DEBUG)

print('Attempting a login {}, password: {} (Will be changed!)...'.format(environ['FBCHAT_EMAIL'], environ['FBCHAT_PASSWORD']))
client = Client(environ['FBCHAT_EMAIL'], environ['FBCHAT_PASSWORD'], logging_level=logging.DEBUG)

client.send(Message(text='Test'), thread_id=self.uid, thread_type=ThreadType.USER)

client.logout()
