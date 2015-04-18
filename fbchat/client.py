# -*- coding: UTF-8 -*-


"""
Core components for fbchat
"""


import re
import json
import random
import requests

from time import time
from uuid import uuid1
from random import random
from bs4 import BeautifulSoup as bs

from .utils import *

CHROME = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.90 Safari/537.36"
SAFARI = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_3) AppleWebKit/601.1.10 (KHTML, like Gecko) Version/8.0.5 Safari/601.1.10"

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

        if not user_agent:
            user_agent = CHROME

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

    def _console(self, msg):
        if self.debug: print(msg)

    def _get(self, url, query=None, timeout=30):
        return self._session.get(url, headers=self._header, params=query, timeout=timeout)

    def _post(self, url, query=None, timeout=30):
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

        if 'home' in r.url:
            self.client_id = hex(int(random()*2147483648))[2:]
            self.start_time = now()
            self.user_id = self._session.cookies['c_user']
            self.user_channel = "p_" + self.user_id
            self.ttstamp = ''

            r = self._get('https://www.facebook.com/')
            self.rev = int(r.text.split('"revision":',1)[1].split(",",1)[0])

            soup = bs(r.text)
            fb_dtsg = soup.find("input", {'name':'fb_dtsg'})['value']

            for i in fb_dtsg:
                self.ttstamp += str(ord(i))
            self.ttstamp += '2'

            self.form = {
                'channel' : self.user_channel,
                'seq' : '0',
                'partition' : '-2',
                'clientid' : self.client_id,
                'viewer_uid' : self.user_id,
                'uid' : self.user_id,
                'state' : 'active',
                'format' : 'json',
                'idle' : 0,
                'cap' : '8'
            }

            self.prev = now()
            self.tmp_prev = now()
            self.last_sync = now()
            self.req_counter = 1;

            return True
        else:
            return False

    def listen(self):
        pass

    def getUserId(self, name):
        payload = {
            'value' : name.lower(),
            'viewer' : self.user_id,
            'rsp' : "search",
            'context' : "search",
            'path' : "/home.php",
            'request_id' : str(uuid1()),
            '__user' : self.user_id,
            '__a' : '1',
            '__req' : str_base(self.req_counter, 36),
            '__rev' : self.rev,
        }
        self.req_counter += 1

        r = self._get("https://www.facebook.com/ajax/typeahead/search.php", payload)
        self.j = get_json(r.text)
        self.r = r

    def sendMessage(self):
        pass

    def sendSticker(self):
        pass

    def markAsRead(self):
        pass
