# -*- coding: UTF-8 -*-

from fbchat import Client
from fbchat.models import *

client = Client('<email>', '<password>')

print('Own id: {}'.format(client.id))

client.sendMessage('Hi me!', thread_id=self.id, thread_type=ThreadType.USER)

client.logout()
