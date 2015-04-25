# -*- coding: UTF-8 -*-

"""
    fbchat
    ~~~~~~

    Facebook Chat (Messenger) for Python

    :copyright: (c) 2015 by Taehoon Kim.
    :license: BSD, see LICENSE for more details.
"""

import requests
from uuid import uuid1
from random import random, choice
from datetime import datetime
from bs4 import BeautifulSoup as bs

from .utils import *
from .models import *

class Client(object):
    """A client for the Facebook Chat (Messenger).

    See http://github.com/carpedm20/fbchat for complete
    documentation for the API.

    """

    def __init__(self, email, password, debug=True, user_agent=None):
        """A client for the Facebook Chat (Messenger).

        :param email: Facebook `email` or `id` or `phone number`
        :param password: Facebook account password

            import fbchat
            chat = fbchat.Client(email, password)

        """

        if not (email and password):
            raise Exception("id and password or config is needed")

        self.email = email
        self.password = password
        self.debug = debug
        self._session = requests.session()
        self.req_counter = 1;

        if not user_agent:
            user_agent = choice(USER_AGENTS)

        self._header = {
            'Content-Type' : 'application/x-www-form-urlencoded',
            'Referer' : 'https://www.facebook.com/',
            'Origin' : 'https://www.facebook.com',
            'User-Agent' : user_agent,
            'Connection' : 'keep-alive',
        }

        self._console("Logging in...")

        if not self.login():
            raise Exception("id or password is wrong")

        self.threads = []
        self.threads = []
        self.data = data

    def _console(self, msg):
        if self.debug: print(msg)

    def _get(self, url, query=None, timeout=30):
        self.req_counter += 1
        return self._session.get(url, headers=self._header, params=query, timeout=timeout)

    def _post(self, url, query=None, timeout=30):
        self.req_counter += 1
        return self._session.post(url, headers=self._header, data=query, timeout=timeout)

    def login(self):
        if not (self.email and self.password):
            raise Exception("id and password or config is needed")

        soup = bs(self._get("https://m.facebook.com/").text)
        data = dict((elem['name'], elem['value']) for elem in soup.findAll("input") if elem.has_attr('value'))
        data['email'] = self.email
        data['pass'] = self.password
        data['login'] = 'Log In'

        r = self._post("https://m.facebook.com/login.php?login_attempt=1", data)
        self.r = r

        if 'home' in r.url:
            self.client_id = hex(int(random()*2147483648))[2:]
            self.start_time = now()
            self.uid = int(self._session.cookies['c_user'])
            self.user_channel = "p_" + str(self.uid)
            self.ttstamp = ''

            r = self._get('https://www.facebook.com/')
            self.rev = int(r.text.split('"revision":',1)[1].split(",",1)[0])
            #self.rev = int(random()*100000)

            soup = bs(r.text)
            self.fb_dtsg = soup.find("input", {'name':'fb_dtsg'})['value']

            for i in self.fb_dtsg:
                self.ttstamp += str(ord(i))
            self.ttstamp += '2'

            self.form = {
                'channel' : self.user_channel,
                'seq' : '0',
                'partition' : '-2',
                'clientid' : self.client_id,
                'viewer_uid' : self.uid,
                'uid' : self.uid,
                'state' : 'active',
                'format' : 'json',
                'idle' : 0,
                'cap' : '8'
            }

            self.prev = now()
            self.tmp_prev = now()
            self.last_sync = now()

            return True
        else:
            return False

    def listen(self):
        pass

    def getUsers(self, name):
        payload = {
            'value' : name.lower(),
            'viewer' : self.uid,
            'rsp' : "search",
            'context' : "search",
            'path' : "/home.php",
            'request_id' : str(uuid1()),
            '__a' : '1',
            '__user' : self.uid,
            '__req' : str_base(self.req_counter, 36),
            '__rev' : self.rev,
        }

        r = self._get("https://www.facebook.com/ajax/typeahead/search.php", payload)
        self.j = j = get_json(r.text)
        self.r = r

        users = []
        for entry in j['payload']['entries']:
            if entry['type'] == 'user':
                users.append(User(entry))
        return users

    def sendMessage(self, message, thread_id):
        timestamp = now()
        date = datetime.now()
        data = {
            'client' : 'mercury',
            'fb_dtsg' : self.fb_dtsg,
            'ttstamp' : self.ttstamp,
            '__a' : '1',
            '__user' : self.uid,
            '__req' : str_base(self.req_counter, 36),
            '__rev' : self.rev,
            'message_batch[0][action_type]' : 'ma-type:user-generated-message',
            'message_batch[0][author]' : 'fbid:' + str(self.uid),
            'message_batch[0][specific_to_list][0]' : 'fbid:' + str(thread_id),
            'message_batch[0][specific_to_list][1]' : 'fbid:' + str(self.uid),
            'message_batch[0][timestamp]' : timestamp,
            'message_batch[0][timestamp_absolute]' : 'Today',
            'message_batch[0][timestamp_relative]' : str(date.hour) + ":" + str(date.minute).zfill(2),
            'message_batch[0][timestamp_time_passed]' : '0',
            'message_batch[0][is_unread]' : False,
            'message_batch[0][is_cleared]' : False,
            'message_batch[0][is_forward]' : False,
            'message_batch[0][is_filtered_content]' : False,
            'message_batch[0][is_spoof_warning]' : False,
            'message_batch[0][source]' : 'source:chat:web',
            'message_batch[0][source_tags][0]' : 'source:chat',
            'message_batch[0][body]' : message,
            'message_batch[0][html_body]' : False,
            'message_batch[0][ui_push_phase]' : 'V3',
            'message_batch[0][status]' : '0',
            'message_batch[0][message_id]' : generateMessageID(self.client_id),
            'message_batch[0][manual_retry_cnt]' : '0',
            'message_batch[0][thread_fbid]' : thread_id,
            'message_batch[0][has_attachment]' : False
        }

        r = self._post("https://www.facebook.com/ajax/mercury/send_messages.php", form)
        return r.ok

    def getThreadList(self, start, end=None):
        if not end:
            end = start + 20

        timestamp = now()
        date = datetime.now()
        data = {
            'client' : 'web_messenger',
            'fb_dtsg' : self.fb_dtsg,
            'ttstamp' : self.ttstamp,
            '__a' : '1',
            '__user' : self.uid,
            '__req' : str_base(self.req_counter, 36),
            '__rev' : self.rev,
            'inbox[offset]' : start,
            'inbox[limit]' : end,
        }

        r = self._post("https://www.facebook.com/ajax/mercury/threadlist_info.php", data)
        if not r.ok:
            return None

        j = get_json(r.text)

        for thread in j['payload']['threads']:
            t = Thread(thread)
            self.threads.append(t)

        return self.threads

    def sendSticker(self):
        pass

    def markAsRead(self):
        pass
