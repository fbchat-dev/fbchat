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
import logging
from uuid import uuid1
import warnings
from random import choice
from datetime import datetime
from bs4 import BeautifulSoup as bs
from mimetypes import guess_type
from .utils import *
from .models import *
from .stickers import *
import time
import sys

# Python 3 does not have raw_input, whereas Python 2 has and it's more secure
try:
    input = raw_input
except NameError:
    pass

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
ConnectURL   ="https://www.facebook.com/ajax/add_friend/action.php?dpr=1"
RemoveUserURL="https://www.facebook.com/chat/remove_participants/"
LogoutURL    ="https://www.facebook.com/logout.php"
AllUsersURL  ="https://www.facebook.com/chat/user_info_all"
SaveDeviceURL="https://m.facebook.com/login/save-device/cancel/"
CheckpointURL="https://m.facebook.com/login/checkpoint/"
facebookEncoding = 'UTF-8'

# Log settings
log = logging.getLogger("client")
log.setLevel(logging.DEBUG)


class Client(object):
    """A client for the Facebook Chat (Messenger).

    See http://github.com/carpedm20/fbchat for complete
    documentation for the API.
    """

    def __init__(self, email, password, debug=True, info_log=True, user_agent=None, max_retries=5, session_cookies=None):
        """A client for the Facebook Chat (Messenger).

        :param email: Facebook `email` or `id` or `phone number`
        :param password: Facebook account password
        :param debug: Configures the logger to `debug` logging_level
        :param info_log: Configures the logger to `info` logging_level
        :param user_agent: Custom user agent to use when sending requests. If `None`, user agent will be chosen from a premade list (see utils.py)
        :param max_retries: Maximum number of times to retry login
        :param session_cookies: Cookie dict from a previous session (Will default to login if these are invalid)
        """

        self.sticky, self.pool = (None, None)
        self._session = requests.session()
        self.req_counter = 1
        self.seq = "0"
        self.payloadDefault = {}
        self.client = 'mercury'
        self.listening = False
        self.is_def_thread_set = False
        self.def_thread_id = None
        self.def_thread_type = None
        self.threads = []

        if not user_agent:
            user_agent = choice(USER_AGENTS)

        self._header = {
            'Content-Type' : 'application/x-www-form-urlencoded',
            'Referer' : BaseURL,
            'Origin' : BaseURL,
            'User-Agent' : user_agent,
            'Connection' : 'keep-alive',
        }

        # Configure the logger differently based on the 'debug' and 'info_log' parameters
        if debug:
            logging_level = logging.DEBUG
        elif info_log:
            logging_level = logging.INFO
        else:
            logging_level = logging.WARNING

        # Creates the console handler
        handler = logging.StreamHandler()
        handler.setLevel(logging_level)
        log.addHandler(handler)

        # If session cookies aren't set, not properly loaded or gives us an invalid session, then do the login
        if not session_cookies or not self.setSession(session_cookies) or not self.is_logged_in():
            self.login(email, password, max_retries)

    def _generatePayload(self, query):
        """Adds the following defaults to the payload:
          __rev, __user, __a, ttstamp, fb_dtsg, __req
        """
        payload = self.payloadDefault.copy()
        if query:
            payload.update(query)
        payload['__req'] = str_base(self.req_counter, 36)
        payload['seq'] = self.seq
        self.req_counter += 1
        return payload

    def _get(self, url, query=None, timeout=30):
        payload = self._generatePayload(query)
        return self._session.get(url, headers=self._header, params=payload, timeout=timeout)

    def _post(self, url, query=None, timeout=30):
        payload = self._generatePayload(query)
        return self._session.post(url, headers=self._header, data=payload, timeout=timeout)

    def _cleanGet(self, url, query=None, timeout=30):
        return self._session.get(url, headers=self._header, params=query, timeout=timeout)

    def _cleanPost(self, url, query=None, timeout=30):
        self.req_counter += 1
        return self._session.post(url, headers=self._header, data=query, timeout=timeout)

    def _postFile(self, url, files=None, timeout=30):
        payload=self._generatePayload(None)
        return self._session.post(url, data=payload, timeout=timeout, files=files)

    def _post_login(self):
        self.payloadDefault = {}
        self.client_id = hex(int(random()*2147483648))[2:]
        self.start_time = now()
        self.uid = str(self._session.cookies['c_user'])
        self.user_channel = "p_" + str(self.uid)
        self.ttstamp = ''

        r = self._get(BaseURL)
        soup = bs(r.text, "lxml")
        log.debug(r.text)
        log.debug(r.url)
        self.fb_dtsg = soup.find("input", {'name':'fb_dtsg'})['value']
        self.fb_h = soup.find("input", {'name':'h'})['value']
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

    def _login(self):
        if not (self.email and self.password):
            raise Exception("Email and password not found.")

        soup = bs(self._get(MobileURL).text, "lxml")
        data = dict((elem['name'], elem['value']) for elem in soup.findAll("input") if elem.has_attr('value') and elem.has_attr('name'))
        data['email'] = self.email
        data['pass'] = self.password
        data['login'] = 'Log In'

        r = self._cleanPost(LoginURL, data)

        # Usually, 'Checkpoint' will refer to 2FA
        if 'checkpoint' in r.url and 'Enter Security Code to Continue' in r.text:
            r = self._2FA(r)

        # Sometimes Facebook tries to show the user a "Save Device" dialog
        if 'save-device' in r.url:
            r = self._cleanGet(SaveDeviceURL)

        if 'home' in r.url:
            self._post_login()
            return True
        else:
            return False

    def _2FA(self, r):
        soup = bs(r.text, "lxml")
        data = dict()

        s = input('Please enter your 2FA code --> ')
        data['approvals_code'] = s
        data['fb_dtsg'] = soup.find("input", {'name':'fb_dtsg'})['value']
        data['nh'] = soup.find("input", {'name':'nh'})['value']
        data['submit[Submit Code]'] = 'Submit Code'
        data['codes_submitted'] = 0
        log.info('Submitting 2FA code.')

        r = self._cleanPost(CheckpointURL, data)

        if 'home' in r.url:
            return r

        del(data['approvals_code'])
        del(data['submit[Submit Code]'])
        del(data['codes_submitted'])

        data['name_action_selected'] = 'save_device'
        data['submit[Continue]'] = 'Continue'
        log.info('Saving browser.')  # At this stage, we have dtsg, nh, name_action_selected, submit[Continue]
        r = self._cleanPost(CheckpointURL, data)

        if 'home' in r.url:
            return r

        del(data['name_action_selected'])
        log.info('Starting Facebook checkup flow.')  # At this stage, we have dtsg, nh, submit[Continue]
        r = self._cleanPost(CheckpointURL, data)

        if 'home' in r.url:
            return r

        del(data['submit[Continue]'])
        data['submit[This was me]'] = 'This Was Me'
        log.info('Verifying login attempt.')  # At this stage, we have dtsg, nh, submit[This was me]
        r = self._cleanPost(CheckpointURL, data)

        if 'home' in r.url:
            return r

        del(data['submit[This was me]'])
        data['submit[Continue]'] = 'Continue'
        data['name_action_selected'] = 'save_device'
        log.info('Saving device again.')  # At this stage, we have dtsg, nh, submit[Continue], name_action_selected
        r = self._cleanPost(CheckpointURL, data)
        return r

    def is_logged_in(self):
        # Send a request to the login url, to see if we're directed to the home page.
        r = self._cleanGet(LoginURL)
        if 'home' in r.url:
            return True
        else:
            return False

    def getSession(self):
        """Returns the session cookies"""
        return self._session.cookies.get_dict()

    def setSession(self, session_cookies):
        """Loads session cookies

        :param session_cookies: dictionary containing session cookies
        Return false if session_cookies does not contain proper cookies
        """

        # Quick check to see if session_cookies is formatted properly
        if not session_cookies or 'c_user' not in session_cookies:
            return False
        
        # Load cookies into current session
        self._session.cookies = requests.cookies.merge_cookies(self._session.cookies, session_cookies)
        self._post_login()
        return True

    def login(self, email, password, max_retries=5):
        self.onLoggingIn(email=email)
        
        if not (email and password):
            raise Exception("Email and password not set.")

        self.email = email
        self.password = password

        for i in range(1, max_retries+1):
            if not self._login():
                log.warning("Attempt #{} failed{}".format(i,{True:', retrying'}.get(i < max_retries, '')))
                time.sleep(1)
                continue
            else:
                self.onLoggedIn(email=email)
                break
        else:
            raise Exception("Login failed. Check email/password.")

    def logout(self, timeout=30):
        data = {
            'ref': "mb",
            'h': self.fb_h
        }

        payload=self._generatePayload(data)
        r = self._session.get(LogoutURL, headers=self._header, params=payload, timeout=timeout)
        # reset value
        self.payloadDefault={}
        self._session = requests.session()
        self.req_counter = 1
        self.seq = "0"
        return r

    def setDefaultThreadId(self, thread_id=str, thread_type=ThreadType):
        """Sets default recipient to send messages and images to.
        
        :param thread_id: user/group ID to default to
        :param thread_type: type of thread_id
        """
        self.def_thread_id = thread_id
        self.def_thread_type = thread_type
        self.is_def_thread_set = True

    def _adapt_user_in_chat_to_user_model(self, user_in_chat):
        """ Adapts user info from chat to User model acceptable initial dict

        :param user_in_chat: user info from chat

        'dir': None,
        'mThumbSrcSmall': None,
        'is_friend': False,
        'is_nonfriend_messenger_contact': True,
        'alternateName': '',
        'i18nGender': 16777216,
        'vanity': '',
        'type': 'friend',
        'searchTokens': ['Voznesenskij', 'Sergej'],
        'thumbSrc': 'https://fb-s-b-a.akamaihd.net/h-ak-xfa1/v/t1.0-1/c9.0.32.32/p32x32/10354686_10150004552801856_220367501106153455_n.jpg?oh=71a87d76d4e4d17615a20c43fb8dbb47&oe=59118CE4&__gda__=1493753268_ae75cef40e9785398e744259ccffd7ff',
        'mThumbSrcLarge': None,
        'firstName': 'Sergej',
        'name': 'Sergej Voznesenskij',
        'uri': 'https://www.facebook.com/profile.php?id=100014812758264',
        'id': '100014812758264',
        'gender': 2
        """

        return {
            'type': 'user',
            'uid': user_in_chat['id'],
            'photo': user_in_chat['thumbSrc'],
            'path': user_in_chat['uri'],
            'text': user_in_chat['name'],
            'score': '',
            'data': user_in_chat,
        }

    def getAllUsers(self):
        """ Gets all users from chat with info included """

        data = {
            'viewer': self.uid,
        }
        r = self._post(AllUsersURL, query=data)
        if not r.ok or len(r.text) == 0:
            return None
        j = get_json(r.text)
        if not j['payload']:
            return None
        payload = j['payload']
        users = []

        for k in payload.keys():
            try:
                user = self._adapt_user_in_chat_to_user_model(payload[k])
            except KeyError:
                continue

            users.append(User(user))

        return users

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

    """
    SEND METHODS
    """

    def _send(self, thread_id=None, message=None, thread_type=None, emoji_size=None, image_id=None, add_user_ids=None, new_title=None):
        """Send a message with given thread id

        :param thread_id: the user id or thread id that you want to send a message to
        :param message: a text that you want to send
        :param thread_type: determines if the recipient_id is for user or thread
        :param emoji_size: size of the like sticker you want to send
        :param image_id: id for the image to send, gotten from the UploadURL
        :param add_user_ids: a list of user ids to add to a chat
        :return: a list of message ids of the sent message(s)
        """

        if thread_id is None and self.is_def_thread_set:
            thread_id = self.def_thread_id
            thread_type = self.def_thread_type
        elif thread_id is None and not self.is_def_thread_set:
            raise ValueError('Default Thread ID is not set.')

        messageAndOTID = generateOfflineThreadingID()
        timestamp = now()
        date = datetime.now()
        data = {
            'client': self.client,
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
            'html_body' : False,
            'ui_push_phase' : 'V3',
            'status' : '0',
            'offline_threading_id':messageAndOTID,
            'message_id' : messageAndOTID,
            'threading_id': generateMessageID(self.client_id),
            'ephemeral_ttl_mode:': '0',
            'manual_retry_cnt' : '0',
            'signatureID' : getSignatureID()
        }

        # Set recipient
        if thread_type == ThreadType.USER:
            data["other_user_fbid"] = thread_id
        elif thread_type == ThreadType.GROUP:
            data["thread_fbid"] = thread_id

        # Set title
        if new_title:
            data['action_type'] = 'ma-type:log-message'
            data['log_message_data[name]'] = new_title
            data['log_message_type'] = 'log:thread-name'

        # Set users to add
        if add_user_ids:
            data['action_type'] = 'ma-type:log-message'
            # It's possible to add multiple users
            for i, add_user_id in enumerate(add_user_ids):
                data['log_message_data[added_participants][' + str(i) + ']'] = "fbid:" + str(add_user_id)
            data['log_message_type'] = 'log:subscribe'

        # Sending a simple message
        if not add_user_ids and not new_title:
            data['action_type'] = 'ma-type:user-generated-message'
            data['body'] = message or ''
            data['has_attachment'] = image_id is not None
            data['specific_to_list[0]'] = 'fbid:' + str(thread_id)
            data['specific_to_list[1]'] = 'fbid:' + str(self.uid)

        # Set image to send
        if image_id:
            data['image_ids[0]'] = image_id

        # Set emoji to send
        if emoji_size:
            data["sticker_id"] = emoji_size.value

        r = self._post(SendURL, data)
        
        if not r.ok:
            log.warning('Error when sending message: Got {} response'.format(r.status_code))
            return False

        response_content = {}
        if isinstance(r.content, str) is False:
            response_content = r.content.decode(facebookEncoding)
        j = get_json(response_content)
        if 'error' in j:
            # 'errorDescription' is in the users own language!
            log.warning('Error #{} when sending message: {}'.format(j['error'], j['errorDescription']))
            return False
        
        message_ids = []
        try:
            message_ids += [action['message_id'] for action in j['payload']['actions'] if 'message_id' in action]
            message_ids[0] # Try accessing element
        except (KeyError, IndexError) as e:
            log.warning('Error when sending message: No message ids could be found')
            return False

        log.info('Message sent.')
        log.debug("Sending {}".format(r))
        log.debug("With data {}".format(data))
        return message_ids

    def sendMessage(self, message: str, thread_id: str = None, thread_type: ThreadType = None):
        """
        Sends a message to given (or default, if not) thread with an additional image.
        :param message: message to send
        :param thread_id: user/group chat ID
        :param thread_type: specify whether thread_id is user or group chat
        :return: a list of message ids of the sent message(s)
        """
        return self._send(thread_id, message, thread_type, None, None, None, None)

    def sendEmoji(self, emoji_size: EmojiSize, thread_id: str = None, thread_type: ThreadType = None):
        """
        Sends an emoji to given (or default, if not) thread.
        :param emoji_size: size of emoji to send
        :param thread_id: user/group chat ID
        :param thread_type: specify whether thread_id is user or group chat 
        :return: a list of message ids of the sent message(s)
        """
        return self._send(thread_id, None, thread_type, emoji_size, None, None, None)

    def sendRemoteImage(self, image_url: str, message: str = None, thread_id: str = None, thread_type: ThreadType = None):
        """
        Sends an image from given URL to given (or default, if not) thread.        
        :param image_url: URL of an image to upload and send
        :param message: additional message
        :param thread_id: user/group chat ID
        :param thread_type: specify whether thread_id is user or group chat 
        :return: a list of message ids of the sent message(s)
        """
        mimetype = guess_type(image_url)[0]
        remote_image = requests.get(image_url).content
        image_id = self._uploadImage({'file': (image_url, remote_image, mimetype)})
        return self._send(thread_id, message, thread_type, None, image_id, None, None)

    # Doesn't upload properly
    def sendLocalImage(self, image_path: str, message: str = None, thread_id: str = None, thread_type: ThreadType = None):
        """
        Sends an image from given URL to given (or default, if not) thread.
        :param image_path: path of an image to upload and send
        :param message: additional message
        :param thread_id: user/group chat ID
        :param thread_type: specify whether thread_id is user or group chat
        :return: a list of message ids of the sent message(s)
        """
        mimetype = guess_type(image_path)[0]
        image_id = self._uploadImage({'file': (image_path, open(image_path, 'rb'), mimetype)})
        return self._send(thread_id, message, thread_type, None, image_id, None, None)

    def addUsersToChat(self, user_list: list, thread_id: str = None):
        """
        Adds users to given (or default, if not) thread.
        :param user_list: list of users to add
        :param thread_id: group chat ID
        :return: a list of message ids of the sent message(s)
        """
        return self._send(thread_id, None, ThreadType.GROUP, None, None, user_list, None)

    def removeUserFromChat(self, user_id: str, thread_id: str = None):
        """
        Adds users to given (or default, if not) thread.
        :param user_id: user ID to remove
        :param thread_id: group chat ID
        :return: true if user was removed
        """

        if thread_id is None and self.def_thread_type == ThreadType.GROUP:
            thread_id = self.def_thread_id
        elif thread_id is None:
            raise ValueError('Default Thread ID is not set.')

        data = {
            "uid": user_id,
            "tid": thread_id
        }

        r = self._post(RemoveUserURL, data)

        return r.ok

    def changeThreadTitle(self, new_title: str, thread_id: str = None):
        """
        Change title of a group conversation.
        :param new_title: new group chat title
        :param thread_id: group chat ID
        :return: a list of message ids of the sent message(s)
        """
        if thread_id is None and self.def_thread_type == ThreadType.GROUP:
            thread_id = self.def_thread_id
        elif thread_id is None:
            raise ValueError('Default Thread ID is not set.')
        return self._send(thread_id, None, ThreadType.GROUP, None, None, None, new_title)

    """
    END SEND METHODS    
    """

    def _uploadImage(self, image):
        """Upload an image and get the image_id for sending in a message

        :param image: a tuple of (file name, data, mime type) to upload to facebook
        """

        r = self._postFile(UploadURL, image)
        response_content = {}
        if isinstance(r.content, str) is False:
            response_content = r.content.decode(facebookEncoding)
        # Strip the start and parse out the returned image_id
        return json.loads(response_content[9:])['payload']['metadata'][0]['image_id']

    def getThreadInfo(self, last_n=20, thread_id: str = None, thread_type: ThreadType = None):
        """Get the info of one Thread

        :param last_n: number of retrieved messages from start (default 20)
        :param thread_id: user/group chat ID
        :param thread_type: specify whether thread_id is user or group chat 
        :return: a list of messages
        """

        if thread_id is None and self.is_def_thread_set:
            thread_id = self.def_thread_id
            thread_type = self.def_thread_type
        elif thread_id is None and not self.is_def_thread_set:
            raise ValueError('Default Thread ID is not set.')

        assert last_n > 0, 'length must be positive integer, got %d' % last_n

        if thread_type == ThreadType.USER:
            key = 'user_ids'
        elif thread_type == ThreadType.GROUP:
            key = 'thread_fbids'

        data = {'messages[{}][{}][offset]'.format(key, thread_id): 0,
                'messages[{}][{}][limit]'.format(key, thread_id): last_n - 1,
                'messages[{}][{}][timestamp]'.format(key, thread_id): now()}

        r = self._post(MessagesURL, query=data)
        if not r.ok or len(r.text) == 0:
            return None

        j = get_json(r.text)
        if not j['payload']:
            return None

        messages = []
        for message in j['payload'].get('actions'):
            messages.append(Message(**message))
        return list(reversed(messages))


    def getThreadList(self, start, length=20):
        """Get thread list of your facebook account.

        :param start: the start index of a thread
        :param length: (optional) the length of a thread
        """

        assert length < 21, '`length` is deprecated, max. last 20 threads are returned'

        data = {
            'client' : self.client,
            'inbox[offset]' : start,
            'inbox[limit]' : length,
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
            log.warning(str(j))

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
            # 'last_action_timestamp': 0
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
        data = {
            "message_ids[0]": threadID,
            "thread_ids[%s][0]" % userID: threadID
        }

        r = self._post(DeliveredURL, data)
        return r.ok


    def markAsRead(self, userID):
        data = {
            "watermarkTimestamp": now(),
            "shouldSendReadReceipt": True,
            "ids[%s]" % userID: True
        }

        r = self._post(ReadStatusURL, data)
        return r.ok


    def markAsSeen(self):
        r = self._post(MarkSeenURL, {"seen_timestamp": 0})
        return r.ok


    def friend_connect(self, friend_id):
        data = {
            "to_friend": friend_id,
            "action": "confirm"
        }

        r = self._post(ConnectURL, data)

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
        """Call pull api to get sticky and pool parameter,
        newer api needs these parameter to work.
        """

        data = {
            "msgs_recv": 0,
            "channel": self.user_channel,
            "clientid": self.client_id
        }

        r = self._get(StickyURL, data)
        j = get_json(r.text)

        if 'lb_info' not in j:
            raise Exception('Get sticky pool error')

        sticky = j['lb_info']['sticky']
        pool = j['lb_info']['pool']
        return sticky, pool


    def _pullMessage(self, sticky, pool):
        """Call pull api with seq value to get message data."""

        data = {
            "msgs_recv": 0,
            "sticky_token": sticky,
            "sticky_pool": pool,
            "clientid": self.client_id,
        }

        r = self._get(StickyURL, data)
        r.encoding = facebookEncoding
        j = get_json(r.text)

        self.seq = j.get('seq', '0')
        return j


    def _parseMessage(self, content):
        """Get message and author name from content.
        May contains multiple messages in the content.
        """

        if 'ms' not in content: return

        log.debug("Received {}".format(content["ms"]))
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
                    if 'leftParticipantFbId' in m['delta']:
                        user_id = m['delta']['leftParticipantFbId']
                        actor_id = m['delta']['messageMetadata']['actorFbId']
                        thread_id = m['delta']['messageMetadata']['threadKey']['threadFbId']
                        self.on_person_removed(user_id, actor_id, thread_id)
                    elif 'addedParticipants' in m['delta']:
                        user_ids = [x['userFbId'] for x in m['delta']['addedParticipants']]
                        actor_id = m['delta']['messageMetadata']['actorFbId']
                        thread_id = m['delta']['messageMetadata']['threadKey']['threadFbId']
                        self.on_people_added(user_ids, actor_id, thread_id)
                    elif 'messageMetadata' in m['delta']:
                        recipient_id = 0
                        thread_type = None
                        if 'threadKey' in m['delta']['messageMetadata']:
                            if 'threadFbId' in m['delta']['messageMetadata']['threadKey']:
                                recipient_id = m['delta']['messageMetadata']['threadKey']['threadFbId']
                                thread_type = 'group'
                            elif 'otherUserFbId' in m['delta']['messageMetadata']['threadKey']:
                                recipient_id = m['delta']['messageMetadata']['threadKey']['otherUserFbId']
                                thread_type = 'user'
                        mid =     m['delta']['messageMetadata']['messageId']
                        message = m['delta'].get('body','')
                        fbid =    m['delta']['messageMetadata']['actorFbId']
                        self.on_message_new(mid, fbid, message, m, recipient_id, thread_type)
                elif m['type'] in ['jewel_requests_add']:
                    from_id = m['from']
                    self.on_friend_request(from_id)
                else:
                    self.on_unknown_type(m)
            except Exception as e:
                # ex_type, ex, tb = sys.exc_info()
                self.on_message_error(sys.exc_info(), m)


    def start_listening(self):
        """Start listening from an external event loop."""
        self.listening = True
        self.sticky, self.pool = self._getSticky()


    def do_one_listen(self, markAlive=True):
        """Does one cycle of the listening loop.
        This method is only useful if you want to control fbchat from an
        external event loop."""
        try:
            if markAlive: self.ping(self.sticky)
            try:
                content = self._pullMessage(self.sticky, self.pool)
                if content: self._parseMessage(content)
            except requests.exceptions.RequestException as e:
                pass
        except KeyboardInterrupt:
            self.listening = False
        except requests.exceptions.Timeout:
            pass


    def stop_listening(self):
        """Cleans up the variables from start_listening."""
        self.listening = False
        self.sticky, self.pool = (None, None)


    def listen(self, markAlive=True):
        self.start_listening()

        log.info("Listening...")
        while self.listening:
            self.do_one_listen(markAlive)

        self.stop_listening()


    def getUserInfo(self, *user_ids):
        """Get user info from id. Unordered.

        :param user_ids: one or more user id(s) to query
        """

        def fbidStrip(_fbid):
            # Stripping of `fbid:` from author_id
            if type(_fbid) == int:
                return _fbid

            if type(_fbid) in [str, unicode] and 'fbid:' in _fbid:
                return int(_fbid[5:])

        user_ids = [fbidStrip(uid) for uid in user_ids]


        data = {"ids[{}]".format(i):uid for i,uid in enumerate(user_ids)}
        r = self._post(UserInfoURL, data)
        info = get_json(r.text)
        full_data= [details for profile,details in info['payload']['profiles'].items()]
        if len(full_data)==1:
            full_data=full_data[0]
        return full_data
