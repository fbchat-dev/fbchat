# -*- coding: UTF-8 -*-

"""
    fbchat
    ~~~~~~

    Facebook Chat (Messenger) for Python

    :copyright: (c) 2015      by Taehoon Kim.
    :copyright: (c) 2015-2016 by PidgeyL.
    :license: BSD, see LICENSE for more details.
"""

import requests
import json
from uuid import uuid1
from random import random, choice
from datetime import datetime
from bs4 import BeautifulSoup as bs
from mimetypes import guess_type
from .utils import *
from .models import *
from .stickers import *
import time
import sys
# URLs
LoginURL     ="https://m.facebook.com/login.php?login_attempt=1"
SearchURL    ="https://www.facebook.com/ajax/typeahead/search.php"
SendURL      ="https://www.facebook.com/messaging/send/"
ThreadsURL   ="https://www.facebook.com/ajax/mercury/threadlist_info.php"
ThreadSyncURL="https://www.facebook.com/ajax/mercury/thread_sync.php"
MessagesURL  ="https://www.facebook.com/ajax/mercury/thread_info.php"
ReadStatusURL="https://www.facebook.com/ajax/mercury/change_read_status.php"
DeliveredURL ="https://www.facebook.com/ajax/mercury/delivery_receipts.php"
MarkSeenURL  ="https://www.facebook.com/ajax/mercury/mark_seen.php"
BaseURL      ="https://www.facebook.com"
MobileURL    ="https://m.facebook.com/"
StickyURL    ="https://0-edge-chat.facebook.com/pull"
PingURL      ="https://0-channel-proxy-06-ash2.facebook.com/active_ping"
UploadURL    ="https://upload.facebook.com/ajax/mercury/upload.php"
UserInfoURL  ="https://www.facebook.com/chat/user_info/"

class Client(object):
    """A client for the Facebook Chat (Messenger).

    See http://github.com/carpedm20/fbchat for complete
    documentation for the API.

    """

    def __init__(self, email, password, debug=True, user_agent=None , max_retries=5):
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
        self.req_counter = 1
        self.seq = "0"
        self.payloadDefault={}
        self.client = 'mercury'
        self.listening = False

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

        for i in range(1,max_retries+1):
            if not self.login():
                self._console("Attempt #{} failed{}".format(i,{True:', retrying'}.get(i<5,'')))
                time.sleep(1)
                continue
            else:
                self._console("login successful")
                break
        else:
            raise Exception("login failed. Check id/password")


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
        payload = self.payloadDefault.copy()
        if query:
            payload.update(query)
        payload['__req'] = str_base(self.req_counter, 36)
        payload['seq'] = self.seq
        self.req_counter += 1
        return payload

    def _get(self, url, query=None, timeout=30):
        payload=self._generatePayload(query)
        return self._session.get(url, headers=self._header, params=payload, timeout=timeout)

    def _post(self, url, query=None, timeout=30):
        payload=self._generatePayload(query)
        return self._session.post(url, headers=self._header, data=payload, timeout=timeout)

    def _cleanPost(self, url, query=None, timeout=30):
        self.req_counter += 1
        return self._session.post(url, headers=self._header, data=query, timeout=timeout)
        
    def _postFile(self, url, files=None, timeout=30):
        payload=self._generatePayload(None)
        return self._session.post(url, data=payload, timeout=timeout, files=files)
        
        
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
            self.payloadDefault['__rev'] = int(r.text.split('"revision":',1)[1].split(",",1)[0])
            self.payloadDefault['__user'] = self.uid
            self.payloadDefault['__a'] = '1'
            self.payloadDefault['ttstamp'] = self.ttstamp
            self.payloadDefault['fb_dtsg'] = self.fb_dtsg

            self.form = {
                'channel' : self.user_channel,
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

    def send(self, recipient_id, message=None, message_type='user', like=None, image_id=None):
        """Send a message with given thread id

        :param recipient_id: the user id or thread id that you want to send a message to
        :param message: a text that you want to send
        :param message_type: determines if the recipient_id is for user or thread
        :param like: size of the like sticker you want to send
        :param image_id: id for the image to send, gotten from the UploadURL
        """

        if message_type.lower() == 'group':
            thread_id = recipient_id
            user_id = None
        else:
            thread_id = None
            user_id = recipient_id

        messageAndOTID=generateOfflineThreadingID()
        timestamp = now()
        date = datetime.now()
        data = {
            'client': self.client,
            'action_type' : 'ma-type:user-generated-message',
            'author' : 'fbid:' + str(self.uid),
            'timestamp' : timestamp,
            'timestamp_absolute' : 'Today',
            'timestamp_relative' : str(date.hour) + ":" + str(date.minute).zfill(2),
            'timestamp_time_passed' : '0',
            'is_unread' : False,
            'is_cleared' : False,
            'is_forward' : False,
            'is_filtered_content' : False,
            'is_filtered_content_bh': False,
            'is_filtered_content_account': False,
            'is_filtered_content_quasar': False,
            'is_filtered_content_invalid_app': False,
            'is_spoof_warning' : False,
            'source' : 'source:chat:web',
            'source_tags[0]' : 'source:chat',
            'body' : message,
            'html_body' : False,
            'ui_push_phase' : 'V3',
            'status' : '0',
            'offline_threading_id':messageAndOTID,
            'message_id' : messageAndOTID,
            'threading_id':generateMessageID(self.client_id),
            'ephemeral_ttl_mode:': '0',
            'manual_retry_cnt' : '0',
            'signatureID' : getSignatureID(),
            'has_attachment' : image_id != None,
            'other_user_fbid' : recipient_id,
            'specific_to_list[0]' : 'fbid:' + str(recipient_id),
            'specific_to_list[1]' : 'fbid:' + str(self.uid),            

        }


        


        if image_id:
            data['image_ids[0]'] = image_id

        if like:
            try:
                sticker = LIKES[like.lower()]
            except KeyError:
                # if user doesn't enter l or m or s, then use the large one
                sticker = LIKES['l']
            data["sticker_id"] = sticker

        r = self._post(SendURL, data)

        if self.debug:
            print(r)
            print(data)
        return r.ok

    def sendRemoteImage(self, recipient_id, message=None, message_type='user', image=''):
        """Send an image from a URL
        
        :param recipient_id: the user id or thread id that you want to send a message to
        :param message: a text that you want to send
        :param message_type: determines if the recipient_id is for user or thread
        :param image: URL for an image to download and send
        """
        mimetype = guess_type(image)[0]
        remote_image = requests.get(image).content
        image_id = self.uploadImage({'file': (image, remote_image, mimetype)})
        return self.send(recipient_id, message, message_type, None, image_id)
        
    def sendLocalImage(self, recipient_id, message=None, message_type='user', image=''):
        """Send an image from a file path
        
        :param recipient_id: the user id or thread id that you want to send a message to
        :param message: a text that you want to send
        :param message_type: determines if the recipient_id is for user or thread
        :param image: path to a local image to send
        """
        mimetype = guess_type(image)[0]
        image_id = self.uploadImage({'file': (image, open(image), mimetype)})
        return self.send(recipient_id, message, message_type, None, image_id)
        
    def uploadImage(self, image):
        """Upload an image and get the image_id for sending in a message
        
        :param image: a tuple of (file name, data, mime type) to upload to facebook
        """
        r = self._postFile(UploadURL, image)
        # Strip the start and parse out the returned image_id
        return json.loads(r._content[9:])['payload']['metadata'][0]['image_id']
        
    def getThreadInfo(self, userID, start, end=None):
        """Get the info of one Thread

        :param userID: ID of the user you want the messages from
        :param start: the start index of a thread
        :param end: (optional) the last index of a thread
        """

        if not end: end = start + 20
        if end <= start: end = start + end

        data = {}
        data['messages[user_ids][%s][offset]'%userID] =    start
        data['messages[user_ids][%s][limit]'%userID] =     end
        data['messages[user_ids][%s][timestamp]'%userID] = now()

        r = self._post(MessagesURL, query=data)
        if not r.ok or len(r.text) == 0:
            return None

        j = get_json(r.text)
        if not j['payload']:
            return None

        messages = []
        for message in j['payload']['actions']:
            messages.append(Message(**message))
        return list(reversed(messages))


    def getThreadList(self, start, end=None):
        """Get thread list of your facebook account.

        :param start: the start index of a thread
        :param end: (optional) the last index of a thread
        """

        if not end: end = start + 20
        if end <= start: end = start + end

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
        participants = {}
        try:
            for participant in j['payload']['participants']:
                participants[participant["fbid"]] = participant["name"]
        except Exception as e:
            print(j)

        # Prevent duplicates in self.threads
        threadIDs = [getattr(x, "thread_id") for x in self.threads]
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
            "unseen_threads": j['payload']['unseen_thread_ids']
        }
        return result

    def markAsDelivered(self, userID, threadID):
        data = {"message_ids[0]": threadID}
        data["thread_ids[%s][0]"%userID] = threadID
        r = self._post(DeliveredURL, data)
        return r.ok

    def markAsRead(self, userID):
        data = {
            "watermarkTimestamp": now(),
            "shouldSendReadReceipt": True
        }
        data["ids[%s]"%userID] = True
        r = self._post(ReadStatusURL, data)
        return r.ok


    def markAsSeen(self):
        r = self._post(MarkSeenURL, {"seen_timestamp": 0})
        return r.ok


    def ping(self, sticky):
        data = {
            'channel': self.user_channel,
            'clientid': self.client_id,
            'partition': -2,
            'cap': 0,
            'uid': self.uid,
            'sticky': sticky,
            'viewer_uid': self.uid
        }
        r = self._get(PingURL, data)
        return r.ok


    def _getSticky(self):
        '''
        Call pull api to get sticky and pool parameter,
        newer api needs these parameter to work.
        '''

        data = {"msgs_recv": 0}

        r = self._get(StickyURL, data)
        j = get_json(r.text)

        if 'lb_info' not in j:
            raise Exception('Get sticky pool error')

        sticky = j['lb_info']['sticky']
        pool = j['lb_info']['pool']
        return sticky, pool


    def _pullMessage(self, sticky, pool):
        '''
        Call pull api with seq value to get message data.
        '''

        data = {
            "msgs_recv": 0,
            "sticky_token": sticky,
            "sticky_pool": pool,
            "clientid": self.client_id,
        }

        r = self._get(StickyURL, data)
        j = get_json(r.text)

        self.seq = j.get('seq', '0')
        return j


    def _parseMessage(self, content):
        '''
        Get message and author name from content.
        May contains multiple messages in the content.
        '''

        if 'ms' not in content: return
        for m in content['ms']:
            try:
                if m['type'] in ['m_messaging', 'messaging']:
                    if m['event'] in ['deliver']:
                        mid =     m['message']['mid']
                        message = m['message']['body']
                        fbid =    m['message']['sender_fbid']
                        name =    m['message']['sender_name']
                        self.on_message(mid, fbid, name, message, m)
                elif m['type'] in ['typ']:
                    self.on_typing(m.get("from"))
                elif m['type'] in ['m_read_receipt']:
                    self.on_read(m.get('realtime_viewer_fbid'), m.get('reader'), m.get('time'))
                elif m['type'] in ['inbox']:
                    viewer = m.get('realtime_viewer_fbid')
                    unseen = m.get('unseen')
                    unread = m.get('unread')
                    other_unseen = m.get('other_unseen')
                    other_unread = m.get('other_unread')
                    timestamp = m.get('seen_timestamp')
                    self.on_inbox(viewer, unseen, unread, other_unseen, other_unread, timestamp)
                elif m['type'] in ['qprimer']:
                    self.on_qprimer(m.get('made'))
                elif m['type'] in ['delta']:
                    if 'messageMetadata' in m['delta']:
                        mid =     m['delta']['messageMetadata']['messageId']
                        message = m['delta'].get('body','')
                        fbid =    m['delta']['messageMetadata']['actorFbId']
                        name =    None
                        self.on_message(mid, fbid, name, message, m)
                else:
                    if self.debug:
                        print(m)
            except Exception as e:
                # ex_type, ex, tb = sys.exc_info()
                self.on_message_error(sys.exc_info(), m)


    def listen(self, markAlive=True):
        self.listening = True
        sticky, pool = self._getSticky()

        if self.debug:
            print("Listening...")

        while self.listening:
            try:
                if markAlive: self.ping(sticky)
                try:
                    content = self._pullMessage(sticky, pool)
                    if content: self._parseMessage(content)
                except requests.exceptions.RequestException as e:
                    continue
            except KeyboardInterrupt:
                break
            except requests.exceptions.Timeout:
              pass
    
    def getUserInfo(self,*user_ids):
        """Get user info from id. Unordered.

        :param user_ids: one or more user id(s) to query 
        """
        
        data = {"ids[{}]".format(i):user_id for i,user_id in enumerate(user_ids)}
        r = self._post(UserInfoURL, data)
        info = get_json(r.text)
        full_data= [details for profile,details in info['payload']['profiles'].items()]
        if len(full_data)==1:
            full_data=full_data[0]
        return full_data





    def on_message(self, mid, author_id, author_name, message, metadata):
        '''
        subclass Client and override this method to add custom behavior on event
        '''
        self.markAsDelivered(author_id, mid)
        self.markAsRead(author_id)
        print("%s said: %s"%(author_name, message))


    def on_typing(self, author_id):
        '''
        subclass Client and override this method to add custom behavior on event
        '''
        pass


    def on_read(self, author, reader, time):
        '''
        subclass Client and override this method to add custom behavior on event
        '''
        pass


    def on_inbox(self, viewer, unseen, unread, other_unseen, other_unread, timestamp):
        '''
        subclass Client and override this method to add custom behavior on event
        '''
        pass


    def on_message_error(self, exception, message):
        '''
        subclass Client and override this method to add custom behavior on event
        '''
        print("Exception: ")
        print(exception)


    def on_qprimer(self, timestamp):
        pass
