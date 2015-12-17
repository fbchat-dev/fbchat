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

# URLs
LoginURL     ="https://m.facebook.com/login.php?login_attempt=1"
SearchURL    ="https://www.facebook.com/ajax/typeahead/search.php"
SendURL      ="https://www.facebook.com/ajax/mercury/send_messages.php"
ThreadsURL   ="https://www.facebook.com/ajax/mercury/threadlist_info.php"
ThreadSyncURL="https://www.facebook.com/ajax/mercury/thread_sync.php"
MessagesURL  ="https://www.facebook.com/ajax/mercury/thread_info.php"
ReadStatusURL="https://www.facebook.com/ajax/mercury/change_read_status.php"
DeliveredURL ="https://www.facebook.com/ajax/mercury/delivery_receipts.php"
MarkSeenURL  ="https://www.facebook.com/ajax/mercury/mark_seen.php"
BaseURL      ="https://www.facebook.com"
MobileURL    ="https://m.facebook.com/"

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
        self.payloadDefault={}
        self.client = 'mercury'

        if not user_agent:
            user_agent = choice(USER_AGENTS)

        self._header = {
            'Content-Type' : 'application/x-www-form-urlencoded',
            'Referer' : BaseURL,
            'Origin' : BaseURL,
            'User-Agent' : user_agent,
            'Connection' : 'keep-alive',
        }

        self._console("Logging in...")

        if not self.login():
            raise Exception("id or password is wrong")

        self.threads = []

    def _console(self, msg):
        if self.debug: print(msg)

    def _setttstamp(self):
        for i in self.fb_dtsg:
            self.ttstamp += str(ord(i))
        self.ttstamp += '2'

    def _generatePayload(self, query):
        '''
        Adds the following defaults to the payload:
          __rev, __user, __a, ttstamp, fb_dtsg, __req
        '''
        if query:
            payload=self.payloadDefault.copy()
            payload.update(query)
            payload['__req'] = str_base(self.req_counter, 36)
        else:
            payload = None
        self.req_counter+=1
        return payload

    def _get(self, url, query=None, timeout=30):
        payload=self._generatePayload(query)
        return self._session.get(url, headers=self._header, params=payload, timeout=timeout)

    def _post(self, url, query=None, timeout=30):
        payload=self._generatePayload(query)
        return self._session.post(url, headers=self._header, data=payload, timeout=timeout)

    def _cleanPost(self, url, query=None, timeout=30):
        self.req_counter+=1
        return self._session.post(url, headers=self._header, data=query, timeout=timeout)

    def login(self):
        if not (self.email and self.password):
            raise Exception("id and password or config is needed")

        soup = bs(self._get(MobileURL).text, "lxml")
        data = dict((elem['name'], elem['value']) for elem in soup.findAll("input") if elem.has_attr('value') and elem.has_attr('name'))
        data['email'] = self.email
        data['pass'] = self.password
        data['login'] = 'Log In'

        r = self._cleanPost(LoginURL, data)

        if 'home' in r.url:
            self.client_id = hex(int(random()*2147483648))[2:]
            self.start_time = now()
            self.uid = int(self._session.cookies['c_user'])
            self.user_channel = "p_" + str(self.uid)
            self.ttstamp = ''

            r = self._get(BaseURL)
            soup = bs(r.text, "lxml")
            self.fb_dtsg = soup.find("input", {'name':'fb_dtsg'})['value']
            self._setttstamp()
            # Set default payload
            self.payloadDefault['__rev']= int(r.text.split('"revision":',1)[1].split(",",1)[0])
            self.payloadDefault['__user']= self.uid
            self.payloadDefault['__a']= '1'
            self.payloadDefault['ttstamp']= self.ttstamp
            self.payloadDefault['fb_dtsg']= self.fb_dtsg

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
        """Find and get user by his/her name

        :param name: name of a person
        """
        payload = {
            'value' : name.lower(),
            'viewer' : self.uid,
            'rsp' : "search",
            'context' : "search",
            'path' : "/home.php",
            'request_id' : str(uuid1()),
        }

        r = self._get(SearchURL, payload)
        self.j = j = get_json(r.text)
		
        users = []
        for entry in j['payload']['entries']:
            if entry['type'] == 'user':
                users.append(User(entry))
        return users # have bug TypeError: __repr__ returned non-string (type bytes)

    def sendMessage(self, message, thread_id):
        """Send a message with given thread id

        :param message: a text that you want to send
        :param thread_id: a thread id that you want to send a message
        """
        timestamp = now()
        date = datetime.now()
        data = {
            'client' : self.client,
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

        r = self._post(SendURL, data)
        return r.ok


    def getThreadInfo(self, userID, start, end=None):
        """Get the info of one Thread

        :param userID: ID of the user you want the messages from
        :param start: the start index of a thread
        :param end: (optional) the last index of a thread
        """
        if not end: end = start + 20
        if end <= start: end=start+end

        data={}
        data['messages[user_ids][%s][offset]'%userID]=    start
        data['messages[user_ids][%s][limit]'%userID]=     end
        data['messages[user_ids][%s][timestamp]'%userID]= now()

        r = self._post(MessagesURL, query=data)
        if not r.ok or len(r.text) == 0:
            return None

        j = get_json(r.text)
        if not j['payload']:
            return None
        messages=[]
        for message in j['payload']['actions']:
            messages.append(Message(**message))
        return list(reversed(messages))


    def getThreadList(self, start, end=None):
        """Get thread list of your facebook account.

        :param start: the start index of a thread
        :param end: (optional) the last index of a thread
        """
        if not end: end = start + 20
        if end <= start: end=start+end

        timestamp = now()
        date = datetime.now()
        data = {
            'client' : self.client,
            'inbox[offset]' : start,
            'inbox[limit]' : end,
        }

        r = self._post(ThreadsURL, data)
        if not r.ok or len(r.text) == 0:
            return None

        j = get_json(r.text)

        # Get names for people
        participants={}
        for participant in j['payload']['participants']:
            participants[participant["fbid"]] = participant["name"]

        # Prevent duplicates in self.threads
        threadIDs=[getattr(x, "thread_id") for x in self.threads]
        for thread in j['payload']['threads']:
            if thread["thread_id"] not in threadIDs:
                try:
                    thread["other_user_name"] = participants[int(thread["other_user_fbid"])]
                except:
                    thread["other_user_name"] = ""
                t = Thread(**thread)
                self.threads.append(t)

        return self.threads


    def getUnread(self):
        form = {
            'client': 'mercury_sync',
            'folders[0]': 'inbox',
            'last_action_timestamp': now() - 60*1000
            #'last_action_timestamp': 0
        }
        r = self._post(ThreadSyncURL, form)
        if not r.ok or len(r.text) == 0:
            return None

        j = get_json(r.text)
        result = {
            "message_counts": j['payload']['message_counts'],
            "unseen_threads": j['payload']['unseen_thread_ids']}
        return result


    def sendSticker(self):
        pass

    def markAsDelivered(self, userID, threadID):
        data={"message_ids[0]": threadID}
        data["thread_ids[%s][0]"%userID] = threadID
        r = self._post(DeliveredURL, data)
        return r.ok

    def markAsRead(self, userID):
        data={
            "watermarkTimestamp": now(),
            "shouldSendReadReceipt": True}
        data["ids[%s]"%userID] = True
        r = self._post(ReadStatusURL, data)
        return r.ok

    def markAsSeen(self):
        r = self._post(MarkSeenURL, {"seen_timestamp": 0})
        return r.ok

