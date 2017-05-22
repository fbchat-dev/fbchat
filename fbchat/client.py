# -*- coding: UTF-8 -*-

"""
    fbchat
    ~~~~~~

    Facebook Chat (Messenger) for Python

    :copyright: (c) 2015      by Taehoon Kim.
    :copyright: (c) 2015-2016 by PidgeyL.
    :license: BSD, see LICENSE for more details.
"""

from __future__ import unicode_literals
import requests
import logging
import urllib
from uuid import uuid1
from random import choice
from datetime import datetime
from bs4 import BeautifulSoup as bs
from mimetypes import guess_type
from .utils import *
from .models import *
from .event_hook import *
import time
import sys

# Python 2's `input` executes the input, whereas `raw_input` just returns the input
try:
    input = raw_input
except NameError:
    pass



# Log settings
log = logging.getLogger("client")
log.setLevel(logging.DEBUG)
# Creates the console handler
handler = logging.StreamHandler()
log.addHandler(handler)


class Client(object):
    """A client for the Facebook Chat (Messenger).

    See http://github.com/carpedm20/fbchat for complete
    documentation for the API.
    """

    def __init__(self, email, password, debug=False, info_log=False, user_agent=None, max_retries=5,
                 session_cookies=None, logging_level=logging.INFO, set_default_events=True):
        """A client for the Facebook Chat (Messenger).

        :param email: Facebook `email` or `id` or `phone number`
        :param password: Facebook account password
        :param debug: Configures the logger to `debug` logging_level (deprecated)
        :param info_log: Configures the logger to `info` logging_level (deprecated)
        :param user_agent: Custom user agent to use when sending requests. If `None`, user agent will be chosen from a premade list (see utils.py)
        :param max_retries: Maximum number of times to retry login
        :param session_cookies: Cookie dict from a previous session (Will default to login if these are invalid)
        :param logging_level: Configures the logger to logging_level
        :param set_default_events: Specifies whether the default logging.info events should be initialized
        """

        self.sticky, self.pool = (None, None)
        self._session = requests.session()
        self.req_counter = 1
        self.seq = "0"
        self.payloadDefault = {}
        self.client = 'mercury'
        self.listening = False
        self.default_thread_id = None
        self.default_thread_type = None
        self.threads = []
        self.set_default_events = set_default_events

        self._setupEventHooks()
        self._setupOldEventHooks()

        if not user_agent:
            user_agent = choice(USER_AGENTS)

        self._header = {
            'Content-Type' : 'application/x-www-form-urlencoded',
            'Referer' : ReqUrl.BASE,
            'Origin' : ReqUrl.BASE,
            'User-Agent' : user_agent,
            'Connection' : 'keep-alive',
        }

        # Configure the logger differently based on the 'debug' and 'info_log' parameters
        if debug:
            deprecation('Client(debug)', deprecated_in='0.10.2', removed_in='0.15.0', details='Use Client(logging_level) instead')
            logging_level = logging.DEBUG
        elif info_log:
            deprecation('Client(info_log)', deprecated_in='0.10.2', removed_in='0.15.0', details='Use Client(logging_level) instead')
            logging_level = logging.INFO

        handler.setLevel(logging_level)

        # If session cookies aren't set, not properly loaded or gives us an invalid session, then do the login
        if not session_cookies or not self.setSession(session_cookies) or not self.isLoggedIn():
            self.login(email, password, max_retries)

    def _setEventHook(self, event_name, *functions):
        if not hasattr(type(self), event_name):
            if self.set_default_events:
                eventhook = EventHook(*functions)
            else:
                eventhook = EventHook()
            setattr(self, event_name, eventhook)

    def _setupEventHooks(self):
        self._setEventHook('onLoggingIn', lambda email: log.info("Logging in {}...".format(email)))

        self._setEventHook('onLoggedIn', lambda email: log.info("Login of {} successful.".format(email)))

        self._setEventHook('onListening', lambda: log.info("Listening..."))

        self._setEventHook('onListenError', lambda exception: raise_exception(exception))


        self._setEventHook('onMessage', lambda mid, author_id, message, thread_id, thread_type, ts, metadata, msg:\
            log.info("Message from {} in {} ({}): {}".format(author_id, thread_id, thread_type.name, message)))

        self._setEventHook('onColorChange', lambda mid, author_id, new_color, thread_id, thread_type, ts, metadata, msg:\
            log.info("Color change from {} in {} ({}): {}".format(author_id, thread_id, thread_type.name, new_color)))

        self._setEventHook('onEmojiChange', lambda mid, author_id, new_emoji, thread_id, thread_type, ts, metadata, msg:\
            log.info("Emoji change from {} in {} ({}): {}".format(author_id, thread_id, thread_type.name, new_emoji)))

        self._setEventHook('onTitleChange', lambda mid, author_id, new_title, thread_id, thread_type, ts, metadata, msg:\
            log.info("Title change from {} in {} ({}): {}".format(author_id, thread_id, thread_type.name, new_title)))

        self._setEventHook('onNicknameChange', lambda mid, author_id, new_title, changed_for, thread_id, thread_type, ts, metadata, msg:\
            log.info("Nickname change from {} in {} ({}) for {}: {}".format(author_id, thread_id, thread_type.name, changed_for, new_title)))


        self._setEventHook('onMessageSeen', lambda seen_by, thread_id, thread_type, seen_ts, delivered_ts, metadata, msg:\
            log.info("Messages seen by {} in {} ({}) at {}s".format(seen_by, thread_id, thread_type.name, seen_ts/1000)))

        self._setEventHook('onMessageDelivered', lambda msg_ids, delivered_for, thread_id, thread_type, ts, metadata, msg:\
            log.info("Messages {} delivered to {} in {} ({}) at {}s".format(msg_ids, delivered_for, thread_id, thread_type.name, ts/1000)))

        self._setEventHook('onMarkedSeen', lambda threads, seen_ts, delivered_ts, metadata, msg:\
            log.info("Marked messages as seen in threads {} at {}s".format([(x[0], x[1].name) for x in threads], seen_ts/1000)))


        self._setEventHook('onPeopleAdded', lambda added_ids, author_id, thread_id, msg:\
            log.info("{} added: {}".format(author_id, ', '.join(added_ids))))

        self._setEventHook('onPersonRemoved', lambda removed_id, author_id, thread_id, msg:\
            log.info("{} removed: {}".format(author_id, removed_id)))

        self._setEventHook('onFriendRequest', lambda from_id, msg: log.info("Friend request from {}".format(from_id)))

        self._setEventHook('onInbox', lambda unseen, unread, recent_unread, msg: log.info('Inbox event: {}, {}, {}'.format(unseen, unread, recent_unread)))


        self._setEventHook('onUnknownMesssageType', lambda msg: log.debug('Unknown message received: {}'.format(msg)))

        self._setEventHook('onMessageError', lambda exception, msg: log.exception('Exception in parsing of {}'.format(msg)))

    def _checkOldEventHook(self, old_event, new_event, deprecated_in='0.10.3', removed_in='0.15.0'):
        if hasattr(type(self), old_event):
            deprecation('Client.{}'.format(old_event), deprecated_in=deprecated_in, removed_in=removed_in, details='Use new event system instead (specifically Client.{})'.format(new_event))
            if not hasattr(type(self), new_event):
                return True
        return False

    def _setupOldEventHooks(self):
        if self._checkOldEventHook('on_message', 'onMessage', deprecated_in='0.7.0', removed_in='0.12.0'):
            self.onMessage += lambda mid, author_id, message, thread_id, thread_type, ts, metadata, msg:\
                self.on_message(mid, author_id, None, message, metadata)

        if self._checkOldEventHook('on_message_new', 'onMessage'):
            self.onMessage += lambda mid, author_id, message, thread_id, thread_type, ts, metadata, msg:\
                self.on_message_new(mid, author_id, message, metadata, thread_id, True if thread_type is ThreadType.USER else False)

        if self._checkOldEventHook('on_friend_request', 'onFriendRequest'):
            self.onFriendRequest += lambda from_id, msg: self.on_friend_request(from_id)

        if self._checkOldEventHook('on_typing', 'onTyping'):
            self.onTyping += lambda author_id, typing_status, msg: self.on_typing(author_id)

        if self._checkOldEventHook('on_read', 'onSeen'):
            self.onSeen += lambda seen_by, thread_id, timestamp, msg: self.on_read(seen_by, thread_id, timestamp)

        if self._checkOldEventHook('on_people_added', 'onPeopleAdded'):
            self.onPeopleAdded += lambda added_ids, author_id, thread_id, msg: self.on_people_added(added_ids, author_id, thread_id)

        if self._checkOldEventHook('on_person_removed', 'onPersonRemoved'):
            self.onPersonRemoved += lambda removed_id, author_id, thread_id, msg: self.on_person_removed(removed_id, author_id, thread_id)

        if self._checkOldEventHook('on_inbox', 'onInbox'):
            self.onInbox += lambda unseen, unread, recent_unread, msg: self.on_inbox(None, unseen, unread, None, recent_unread, None)

        if self._checkOldEventHook('on_qprimer', ''):
            pass

        if self._checkOldEventHook('on_message_error', 'onMessageError'):
            self.onMessageError += lambda exception, msg: self.on_message_error(exception, msg)

        if self._checkOldEventHook('on_unknown_type', 'onUnknownMesssageType'):
            self.onUnknownMesssageType += lambda msg: self.on_unknown_type(msg)

    @deprecated(deprecated_in='0.6.0', removed_in='0.11.0', details='Use log.<level> instead')
    def _console(self, msg):
        """Assumes an INFO level and log it.

        This method shouldn't be used anymore.
        Use the log itself:
        >>> import logging
        >>> from fbchat.client import log
        >>> log.setLevel(logging.DEBUG)

        You can do the same thing by adding the 'debug' argument:
        >>> from fbchat import Client
        >>> client = Client("...", "...", debug=True)
        """
        log.debug(msg)

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

    def _postFile(self, url, files=None, query=None, timeout=30):
        payload=self._generatePayload(query)
        # Removes 'Content-Type' from the header
        headers = dict((i, self._header[i]) for i in self._header if i != 'Content-Type')
        return self._session.post(url, headers=headers, data=payload, timeout=timeout, files=files)

    def _postLogin(self):
        self.payloadDefault = {}
        self.client_id = hex(int(random()*2147483648))[2:]
        self.start_time = now()
        self.uid = str(self._session.cookies['c_user'])
        self.user_channel = "p_" + self.uid
        self.ttstamp = ''

        r = self._get(ReqUrl.BASE)
        soup = bs(r.text, "lxml")
        log.debug(r.text)
        log.debug(r.url)
        self.fb_dtsg = soup.find("input", {'name':'fb_dtsg'})['value']
        self.fb_h = soup.find("input", {'name':'h'})['value']
        for i in self.fb_dtsg:
            self.ttstamp += str(ord(i))
        self.ttstamp += '2'
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

        soup = bs(self._get(ReqUrl.MOBILE).text, "lxml")
        data = dict((elem['name'], elem['value']) for elem in soup.findAll("input") if elem.has_attr('value') and elem.has_attr('name'))
        data['email'] = self.email
        data['pass'] = self.password
        data['login'] = 'Log In'

        r = self._cleanPost(ReqUrl.LOGIN, data)

        # Usually, 'Checkpoint' will refer to 2FA
        if 'checkpoint' in r.url and 'Enter Security Code to Continue' in r.text:
            r = self._2FA(r)

        # Sometimes Facebook tries to show the user a "Save Device" dialog
        if 'save-device' in r.url:
            r = self._cleanGet(ReqUrl.SAVE_DEVICE)

        if 'home' in r.url:
            self._postLogin()
            return True, r.url
        else:
            return False, r.url

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

        r = self._cleanPost(ReqUrl.CHECKPOINT, data)

        if 'home' in r.url:
            return r

        del(data['approvals_code'])
        del(data['submit[Submit Code]'])
        del(data['codes_submitted'])

        data['name_action_selected'] = 'save_device'
        data['submit[Continue]'] = 'Continue'
        log.info('Saving browser.')  # At this stage, we have dtsg, nh, name_action_selected, submit[Continue]
        r = self._cleanPost(ReqUrl.CHECKPOINT, data)

        if 'home' in r.url:
            return r

        del(data['name_action_selected'])
        log.info('Starting Facebook checkup flow.')  # At this stage, we have dtsg, nh, submit[Continue]
        r = self._cleanPost(ReqUrl.CHECKPOINT, data)

        if 'home' in r.url:
            return r

        del(data['submit[Continue]'])
        data['submit[This was me]'] = 'This Was Me'
        log.info('Verifying login attempt.')  # At this stage, we have dtsg, nh, submit[This was me]
        r = self._cleanPost(ReqUrl.CHECKPOINT, data)

        if 'home' in r.url:
            return r

        del(data['submit[This was me]'])
        data['submit[Continue]'] = 'Continue'
        data['name_action_selected'] = 'save_device'
        log.info('Saving device again.')  # At this stage, we have dtsg, nh, submit[Continue], name_action_selected
        r = self._cleanPost(ReqUrl.CHECKPOINT, data)
        return r

    def isLoggedIn(self):
        # Send a request to the login url, to see if we're directed to the home page.
        r = self._cleanGet(ReqUrl.LOGIN)
        return 'home' in r.url

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
        self._postLogin()
        return True

    def login(self, email, password, max_retries=5):
        self.onLoggingIn(email=email)
        
        if not (email and password):
            raise Exception("Email and password not set.")

        self.email = email
        self.password = password

        for i in range(1, max_retries+1):
            login_successful, login_url = self._login()
            if not login_successful:
                log.warning("Attempt #{} failed{}".format(i,{True:', retrying'}.get(i < max_retries, '')))
                time.sleep(1)
                continue
            else:
                self.onLoggedIn(email=email)
                break
        else:
            raise Exception("Login failed. Check email/password. (Failed on url: {})".format(login_url))

    def logout(self, timeout=30):
        data = {
            'ref': "mb",
            'h': self.fb_h
        }

        payload=self._generatePayload(data)
        r = self._session.get(ReqUrl.LOGOUT, headers=self._header, params=payload, timeout=timeout)
        # reset value
        self.payloadDefault={}
        self._session = requests.session()
        self.req_counter = 1
        self.seq = "0"
        return r

    @deprecated(deprecated_in='0.10.2', removed_in='0.15.0', details='Use setDefaultThread instead')
    def setDefaultRecipient(self, recipient_id, is_user=True):
        self.setDefaultThread(str(recipient_id), thread_type=isUserToThreadType(is_user))

    def setDefaultThread(self, thread_id, thread_type):
        # type: (str, ThreadType) -> None
        """Sets default thread to send messages and images to.

        :param thread_id: user/group ID to default to
        :param thread_type: type of thread_id
        """
        self.default_thread_id = thread_id
        self.default_thread_type = thread_type

    def resetDefaultThread(self):
        # type: () -> None
        """Resets default thread."""
        self.default_thread_id = None
        self.default_thread_type = None

    def _getThread(self, given_thread_id, given_thread_type):
        # type: (str, ThreadType) -> (str, ThreadType)
        """
        Checks if thread ID is given, checks if default is set and returns correct values
        
        :raises ValueError: if thread ID is not given and there is no default
        :return: tuple of thread ID and thread type
        """
        if given_thread_id is None:
            if self.default_thread_id is not None:
                return self.default_thread_id, self.default_thread_type
            else:
                raise ValueError('Thread ID is not set.')
        else:
            return given_thread_id, given_thread_type

    def getAllUsers(self):
        """ Gets all users from chat with info included """

        data = {
            'viewer': self.uid,
        }
        r = self._post(ReqUrl.ALL_USERS, query=data)
        if not r.ok or len(r.text) == 0:
            return None
        j = get_json(r)
        if not j['payload']:
            return None
        payload = j['payload']
        users = []

        for k in payload.keys():
            try:
                user = User.adaptFromChat(payload[k])
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

        r = self._get(ReqUrl.SEARCH, payload)
        self.j = j = get_json(r)

        users = []
        for entry in j['payload']['entries']:
            if entry['type'] == 'user':
                users.append(User(entry))
        return users # have bug TypeError: __repr__ returned non-string (type bytes)

    """
    SEND METHODS
    """

    def _getSendData(self, thread_id=None, thread_type=ThreadType.USER):
        """Returns the data needed to send a request to `SendURL`"""
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
            'offline_threading_id': messageAndOTID,
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

        return data

    def _checkRequest(self, r):
        if not r.ok:
            log.warning('Error when sending request: Got {} response'.format(r.status_code))
            return None

        j = get_json(r)
        if 'error' in j:
            # 'errorDescription' is in the users own language!
            log.warning('Error #{} when sending request: {}'.format(j['error'], j['errorDescription']))
            return None
        
        return j

    def _doSendRequest(self, data):
        """Sends the data to `SendURL`, and returns the message id"""
        r = self._post(ReqUrl.SEND, data)

        j = self._checkRequest(r)
        
        if j is None:
            return None

        try:
            message_ids = [action['message_id'] for action in j['payload']['actions'] if 'message_id' in action]
            if len(message_ids) != 1:
                log.warning("Got multiple message ids' back: {}".format(message_ids))
            message_id = message_ids[0]
        except (KeyError, IndexError) as e:
            log.warning('Error when sending message: No message ids could be found')
            return None

        log.info('Message sent.')
        log.debug('Sending {}'.format(r))
        log.debug('With data {}'.format(data))
        log.debug('Recieved message id {}'.format(message_id))
        return message_id

    @deprecated(deprecated_in='0.10.2', removed_in='0.15.0', details='Use specific functions (eg. sendMessage()) instead')
    def send(self, recipient_id=None, message=None, is_user=True, like=None, image_id=None, add_user_ids=None):
        if add_user_ids:
            return self.addUsersToChat(user_ids=add_user_ids, thread_id=recipient_id)
        elif image_id:
            return self.sendImage(image_id=image_id, message=message, thread_id=recipient_id, thread_type=isUserToThreadType(is_user))
        elif like:
            if not like in LIKES:
                like = 'l' # Backwards compatability
            return self.sendEmoji(emoji=None, size=LIKES[like], thread_id=recipient_id, thread_type=isUserToThreadType(is_user))
        else:
            return self.sendMessage(message, thread_id=recipient_id, thread_type=isUserToThreadType(is_user))

    def sendMessage(self, message, thread_id=None, thread_type=ThreadType.USER):
        # type: (str, str, ThreadType) -> list
        """
        Sends a message to given (or default, if not) thread with an additional image.
        
        :param message: message to send
        :param thread_id: user/group chat ID
        :param thread_type: specify whether thread_id is user or group chat
        :return: the message id of the message
        """
        thread_id, thread_type = self._getThread(thread_id, thread_type)
        data = self._getSendData(thread_id, thread_type)

        data['action_type'] = 'ma-type:user-generated-message'
        data['body'] = message or ''
        data['has_attachment'] = False
        data['specific_to_list[0]'] = 'fbid:' + thread_id
        data['specific_to_list[1]'] = 'fbid:' + self.uid

        return self._doSendRequest(data)

    def sendEmoji(self, emoji=None, size=EmojiSize.SMALL, thread_id=None, thread_type=ThreadType.USER):
        # type: (str, EmojiSize, str, ThreadType) -> list
        """
        Sends an emoji. If emoji and size are not specified a small like is sent.
        
        :param emoji: the chosen emoji to send. If not specified, default thread emoji is sent
        :param size: size of emoji to send
        :param thread_id: user/group chat ID
        :param thread_type: specify whether thread_id is user or group chat
        :return: the message id of the emoji
        """
        thread_id, thread_type = self._getThread(thread_id, thread_type)
        data = self._getSendData(thread_id, thread_type)
        data['action_type'] = 'ma-type:user-generated-message'
        data['has_attachment'] = False
        data['specific_to_list[0]'] = 'fbid:' + thread_id
        data['specific_to_list[1]'] = 'fbid:' + self.uid

        if emoji:
            data['body'] = emoji
            data['tags[0]'] = 'hot_emoji_size:' + size.name.lower()
        else:
            data["sticker_id"] = size.value

        return self._doSendRequest(data)

    def sendImage(self, image_id, message=None, thread_id=None, thread_type=ThreadType.USER):
        """Sends an already uploaded image with the id image_id to the thread"""
        thread_id, thread_type = self._getThread(thread_id, thread_type)
        data = self._getSendData(thread_id, thread_type)

        data['action_type'] = 'ma-type:user-generated-message'
        data['body'] = message or ''
        data['has_attachment'] = True
        data['specific_to_list[0]'] = 'fbid:' + str(thread_id)
        data['specific_to_list[1]'] = 'fbid:' + str(self.uid)

        data['image_ids[0]'] = image_id

        return self._doSendRequest(data)

    def sendRemoteImage(self, image_url, message=None, thread_id=None, thread_type=ThreadType.USER,
                        recipient_id=None, is_user=None, image=None):
        # type: (str, str, str, ThreadType) -> list
        """
        Sends an image from given URL to given (or default, if not) thread.        
        
        :param image_url: URL of an image to upload and send
        :param message: additional message
        :param thread_id: user/group chat ID
        :param thread_type: specify whether thread_id is user or group chat 
        :return: the message id of the message
        """
        if recipient_id is not None:
            deprecation('sendRemoteImage(recipient_id)', deprecated_in='0.10.2', removed_in='0.15.0', details='Use sendRemoteImage(thread_id) instead')
            thread_id = recipient_id
        if is_user is not None:
            deprecation('sendRemoteImage(is_user)', deprecated_in='0.10.2', removed_in='0.15.0', details='Use sendRemoteImage(thread_type) instead')
            thread_type = isUserToThreadType(is_user)
        if image is not None:
            deprecation('sendRemoteImage(image)', deprecated_in='0.10.2', removed_in='0.15.0', details='Use sendRemoteImage(image_url) instead')
            image_url = image

        thread_id, thread_type = self._getThread(thread_id, thread_type)
        mimetype = guess_type(image_url)[0]
        remote_image = requests.get(image_url).content
        image_id = self._uploadImage(image_url, remote_image, mimetype)
        return self.sendImage(image_id=image_id, message=message, thread_id=thread_id, thread_type=thread_type)

    def sendLocalImage(self, image_path, message=None, thread_id=None, thread_type=ThreadType.USER,
                       recipient_id=None, is_user=None, image=None):
        # type: (str, str, str, ThreadType) -> list
        """
        Sends an image from given URL to given (or default, if not) thread.
        
        :param image_path: path of an image to upload and send
        :param message: additional message
        :param thread_id: user/group chat ID
        :param thread_type: specify whether thread_id is user or group chat
        :return: the message id of the message
        """
        if recipient_id is not None:
            deprecation('sendLocalImage(recipient_id)', deprecated_in='0.10.2', removed_in='0.15.0', details='Use sendLocalImage(thread_id) instead')
            thread_id = recipient_id
        if is_user is not None:
            deprecation('sendLocalImage(is_user)', deprecated_in='0.10.2', removed_in='0.15.0', details='Use sendLocalImage(thread_type) instead')
            thread_type = isUserToThreadType(is_user)
        if image is not None:
            deprecation('sendLocalImage(image)', deprecated_in='0.10.2', removed_in='0.15.0', details='Use sendLocalImage(image_path) instead')
            image_path = image

        thread_id, thread_type = self._getThread(thread_id, thread_type)
        mimetype = guess_type(image_path)[0]
        image_id = self._uploadImage(image_path, open(image_path, 'rb'), mimetype)
        return self.sendImage(image_id=image_id, message=message, thread_id=thread_id, thread_type=thread_type)

    def addUsersToGroup(self, user_ids, thread_id=None):
        # type: (list, str) -> list
        """
        Adds users to the given (or default, if not) group.
        
        :param user_ids: list of user ids to add
        :param thread_id: group chat ID
        :return: the message id of the "message"
        """
        thread_id, thread_type = self._getThread(thread_id, None)
        data = self._getSendData(thread_id, ThreadType.GROUP)

        data['action_type'] = 'ma-type:log-message'
        data['log_message_type'] = 'log:subscribe'

        for i, user_id in enumerate(user_ids):
            data['log_message_data[added_participants][' + str(i) + ']'] = "fbid:" + str(user_id)

        return self._doSendRequest(data)

    def removeUserFromGroup(self, user_id, thread_id=None):
        # type: (str, str) -> bool
        """
        Adds users to the given (or default, if not) group.
        
        :param user_id: user ID to remove
        :param thread_id: group chat ID
        :return: whether the action was successful
        """

        thread_id, thread_type = self._getThread(thread_id, None)

        data = {
            "uid": user_id,
            "tid": thread_id
        }
        
        j = self._checkRequest(self._post(ReqUrl.REMOVE_USER, data))

        return False if j is None else True

    @deprecated(deprecated_in='0.10.2', removed_in='0.15.0', details='Use removeUserFromGroup() instead')
    def add_users_to_chat(self, threadID, userID):
        if not isinstance(userID, list):
            userID = [userID]
        return self.addUsersToGroup(userID, thread_id=threadID)

    @deprecated(deprecated_in='0.10.2', removed_in='0.15.0', details='Use removeUserFromGroup() instead')
    def remove_user_from_chat(self, threadID, userID):
        return self.removeUserFromGroup(userID, thread_id=threadID)

    @deprecated(deprecated_in='0.10.2', removed_in='0.15.0', details='Use changeGroupTitle() instead')
    def changeThreadTitle(self, threadID, newTitle):
        return self.changeGroupTitle(newTitle, thread_id=threadID)

    def changeGroupTitle(self, title, thread_id=None):
        """
        Change title of a group conversation.
        
        :param title: new group chat title
        :param thread_id: group chat ID
        :return: the message id of the "message"
        """
        thread_id, thread_type = self._getThread(thread_id, None)
        data = self._getSendData(thread_id, ThreadType.GROUP)

        data['action_type'] = 'ma-type:log-message'
        data['log_message_data[name]'] = title
        data['log_message_type'] = 'log:thread-name'

        return self._doSendRequest(data)

    def changeThreadColor(self, new_color, thread_id=None):
        # type: (ThreadColor, str, ThreadType) -> bool
        """
        Changes thread color to specified color. For more info about color names - see wiki.
        
        :param new_color: new color name
        :param thread_id: user/group chat ID
        :return: whether the action was successful
        """
        thread_id, thread_type = self._getThread(thread_id, None)

        data = {
            "color_choice": new_color.value,
            "thread_or_other_fbid": thread_id
        }

        j = self._checkRequest(self._post(ReqUrl.THREAD_COLOR, data))

        return False if j is None else True

    def reactToMessage(self, message_id, reaction):
        # type: (str, MessageReaction) -> bool
        """
        Reacts to a message.

        :param message_id: message ID to react to
        :param reaction: reaction emoji to send
        :return: whether the action was successful
        """
        full_data = {
            "doc_id": 1491398900900362,
            "dpr": 1,
            "variables": {
                "data": {
                    "action": "ADD_REACTION",
                    "client_mutation_id": "1",
                    "actor_id": self.uid,
                    "message_id": str(message_id),
                    "reaction": reaction.value
                }
            }
        }
        try:
            url_part = urllib.parse.urlencode(full_data)
        except AttributeError:
            # This is a very hacky solution, please suggest a better one ;)
            url_part = urllib.urlencode(full_data)\
                .replace('u%27', '%27')\
                .replace('%5CU{}'.format(MessageReactionFix[reaction.value][0]), MessageReactionFix[reaction.value][1])
        
        j = self._checkRequest(self._post('{}/?{}'.format(ReqUrl.MESSAGE_REACTION, url_part)))

        return False if j is None else True

    def setTypingStatus(self, status, thread_id=None, thread_type=None):
        # type: (TypingStatus, str, ThreadType) -> bool
        """
        Sets users typing status.
        
        :param status: specify whether the status is typing or not (TypingStatus)
        :param thread_id: user/group chat ID
        :param thread_type: specify whether thread_id is user or group chat
        :return: True if status changed
        """
        thread_id, thread_type = self._getThread(thread_id, None)

        data = {
            "typ": status.value,
            "thread": thread_id,
            "to": thread_id if thread_type == ThreadType.USER else "",
            "source": "mercury-chat"
        }

        j = self._checkRequest(self._post(ReqUrl.TYPING, data))

        return False if j is None else True

    """
    END SEND METHODS    
    """

    def _uploadImage(self, image_path, data, mimetype):
        """Upload an image and get the image_id for sending in a message

        :param image: a tuple of (file name, data, mime type) to upload to facebook
        """

        r = self._postFile(ReqUrl.UPLOAD, {
            'file': (
                image_path,
                data,
                mimetype
            )
        })
        j = get_json(r)
        # Return the image_id
        return j['payload']['metadata'][0]['image_id']

    def getThreadInfo(self, last_n=20, thread_id=None, thread_type=ThreadType.USER):
        # type: (int, str, ThreadType) -> list
        """Get the info of one Thread

        :param last_n: number of retrieved messages from start (default 20)
        :param thread_id: user/group chat ID
        :param thread_type: specify whether thread_id is user or group chat 
        :return: a list of messages
        """

        thread_id, thread_type = self._getThread(thread_id, thread_type)

        assert last_n > 0, 'length must be positive integer, got %d' % last_n

        if thread_type == ThreadType.USER:
            key = 'user_ids'
        elif thread_type == ThreadType.GROUP:
            key = 'thread_fbids'

        data = {'messages[{}][{}][offset]'.format(key, thread_id): 0,
                'messages[{}][{}][limit]'.format(key, thread_id): last_n - 1,
                'messages[{}][{}][timestamp]'.format(key, thread_id): now()}

        r = self._post(ReqUrl.MESSAGES, query=data)
        if not r.ok or len(r.text) == 0:
            return []

        j = get_json(r)
        if not j['payload']:
            return []

        messages = []
        for message in j['payload'].get('actions'):
            messages.append(Message(**message))
        return list(reversed(messages))


    def getThreadList(self, start, length=20):
        # type: (int, int) -> list
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

        r = self._post(ReqUrl.THREADS, data)
        if not r.ok or len(r.text) == 0:
            return []

        j = get_json(r)

        # Get names for people
        participants = {}
        try:
            for participant in j['payload']['participants']:
                participants[participant["fbid"]] = participant["name"]
        except Exception:
            log.exception('Exception while getting names for people in getThreadList. {}'.format(j))

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

        r = self._post(ReqUrl.THREAD_SYNC, form)
        if not r.ok or len(r.text) == 0:
            return None

        j = get_json(r)
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

        r = self._post(ReqUrl.DELIVERED, data)
        return r.ok

    def markAsRead(self, userID):
        data = {
            "watermarkTimestamp": now(),
            "shouldSendReadReceipt": True,
            "ids[%s]" % userID: True
        }

        r = self._post(ReqUrl.READ_STATUS, data)
        return r.ok

    def markAsSeen(self):
        r = self._post(ReqUrl.MARK_SEEN, {"seen_timestamp": 0})
        return r.ok

    @deprecated(deprecated_in='0.10.2', removed_in='0.15.0', details='Use friendConnect() instead')
    def friend_connect(self, friend_id):
        return self.friendConnect(friend_id)

    def friendConnect(self, friend_id):
        # type: (str) -> bool
        data = {
            "to_friend": friend_id,
            "action": "confirm"
        }

        r = self._post(ReqUrl.CONNECT, data)
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
        r = self._get(ReqUrl.PING, data)
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

        r = self._get(ReqUrl.STICKY, data)
        j = get_json(r)

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

        r = self._get(ReqUrl.STICKY, data)
        j = get_json(r)

        self.seq = j.get('seq', '0')
        return j

    def _parseMessage(self, content):
        """Get message and author name from content. May contain multiple messages in the content."""

        if 'ms' not in content: return

        log.debug("Received {}".format(content["ms"]))
        for m in content["ms"]:
            mtype = m.get("type")
            try:
                # Things that directly change chat
                if mtype == "delta":

                    def getThreadIdAndThreadType(msg_metadata):
                        """Returns a tuple consisting of thread id and thread type"""
                        id_thread = None
                        type_thread = None
                        if 'threadFbId' in msg_metadata['threadKey']:
                            id_thread = str(msg_metadata['threadKey']['threadFbId'])
                            type_thread = ThreadType.GROUP
                        elif 'otherUserFbId' in msg_metadata['threadKey']:
                            id_thread = str(msg_metadata['threadKey']['otherUserFbId'])
                            type_thread = ThreadType.USER
                        return id_thread, type_thread

                    delta = m["delta"]
                    delta_type = delta.get("type")
                    metadata = delta.get("messageMetadata")

                    if metadata is not None:
                        mid = metadata["messageId"]
                        author_id = str(metadata['actorFbId'])
                        ts = int(metadata.get("timestamp"))

                    # Added participants
                    if 'addedParticipants' in delta:
                        added_ids = [str(x['userFbId']) for x in delta['addedParticipants']]
                        thread_id = str(metadata['threadKey']['threadFbId'])
                        self.onPeopleAdded(mid=mid, added_ids=added_ids, author_id=author_id, thread_id=thread_id,
                                           ts=ts, msg=m)
                        continue

                    # Left/removed participants
                    elif 'leftParticipantFbId' in delta:
                        removed_id = str(delta['leftParticipantFbId'])
                        thread_id = str(metadata['threadKey']['threadFbId'])
                        self.onPersonRemoved(mid=mid, removed_id=removed_id, author_id=author_id, thread_id=thread_id,
                                             ts=ts, msg=m)
                        continue

                    # Color change
                    elif delta_type == "change_thread_theme":
                        new_color = delta["untypedData"]["theme_color"]
                        thread_id, thread_type = getThreadIdAndThreadType(metadata)
                        self.onColorChange(mid=mid, author_id=author_id, new_color=new_color, thread_id=thread_id,
                                           thread_type=thread_type, ts=ts, metadata=metadata, msg=m)
                        continue

                    # Emoji change
                    elif delta_type == "change_thread_icon":
                        new_emoji = delta["untypedData"]["thread_icon"]
                        thread_id, thread_type = getThreadIdAndThreadType(metadata)
                        self.onEmojiChange(mid=mid, author_id=author_id, new_emoji=new_emoji, thread_id=thread_id,
                                           thread_type=thread_type, ts=ts, metadata=metadata, msg=m)
                        continue

                    # Thread title change
                    elif delta.get("class") == "ThreadName":
                        new_title = delta["name"]
                        thread_id, thread_type = getThreadIdAndThreadType(metadata)
                        self.onTitleChange(mid=mid, author_id=author_id, new_title=new_title, thread_id=thread_id,
                                           thread_type=thread_type, ts=ts, metadata=metadata, msg=m)
                        continue

                    # Nickname change
                    elif delta_type == "change_thread_nickname":
                        changed_for = str(delta["untypedData"]["participant_id"])
                        new_title = delta["untypedData"]["nickname"]
                        thread_id, thread_type = getThreadIdAndThreadType(metadata)
                        self.onNicknameChange(mid=mid, author_id=author_id, changed_for=changed_for,
                                              new_title=new_title,
                                              thread_id=thread_id, thread_type=thread_type, ts=ts, metadata=metadata)
                        continue

                    # Message delivered
                    elif delta.get("class") == "DeliveryReceipt":
                        message_ids = delta["messageIds"]
                        delivered_for = str(delta.get("actorFbId") or delta["threadKey"]["otherUserFbId"])
                        ts = int(delta["deliveredWatermarkTimestampMs"])
                        thread_id, thread_type = getThreadIdAndThreadType(delta)
                        self.onMessageDelivered(msg_ids=message_ids, delivered_for=delivered_for,
                                                thread_id=thread_id, thread_type=thread_type, ts=ts, metadata=metadata, msg=m)
                        continue

                    # Message seen
                    elif delta.get("class") == "ReadReceipt":
                        seen_by = str(delta.get("actorFbId") or delta["threadKey"]["otherUserFbId"])
                        seen_ts = int(delta["actionTimestampMs"])
                        delivered_ts = int(delta["watermarkTimestampMs"])
                        thread_id, thread_type = getThreadIdAndThreadType(delta)
                        self.onMessageSeen(seen_by=seen_by, thread_id=thread_id, thread_type=thread_type,
                                           seen_ts=seen_ts, delivered_ts=delivered_ts, metadata=metadata, msg=m)
                        continue

                    # Messages marked as seen
                    elif delta.get("class") == "MarkRead":
                        seen_ts = int(delta.get("actionTimestampMs") or delta.get("actionTimestamp"))
                        delivered_ts = int(delta.get("watermarkTimestampMs") or delta.get("watermarkTimestamp"))

                        threads = []
                        if "folders" not in delta:
                            threads = [getThreadIdAndThreadType({"threadKey": thr}) for thr in delta.get("threadKeys")]

                        # thread_id, thread_type = getThreadIdAndThreadType(delta)
                        self.onMarkedSeen(threads=threads, seen_ts=seen_ts, delivered_ts=delivered_ts, metadata=delta, msg=m)
                        continue

                    # New message
                    elif delta.get("class") == "NewMessage":
                        message = delta.get('body', '')
                        thread_id, thread_type = getThreadIdAndThreadType(metadata)
                        self.onMessage(mid=mid, author_id=author_id, message=message,
                                       thread_id=thread_id, thread_type=thread_type, ts=ts, metadata=m, msg=m)
                        continue

                # Inbox
                if mtype == "inbox":
                    self.onInbox(unseen=m["unseen"], unread=m["unread"], recent_unread=m["recent_unread"], msg=m)

                # Typing
                # elif mtype == "typ":
                #     author_id = str(m.get("from"))
                #     typing_status = TypingStatus(m.get("st"))
                #     self.onTyping(author_id=author_id, typing_status=typing_status)

                # Delivered

                # Seen
                # elif mtype == "m_read_receipt":
                #
                #     self.onSeen(m.get('realtime_viewer_fbid'), m.get('reader'), m.get('time'))

                # elif mtype in ['jewel_requests_add']:
                #         from_id = m['from']
                #         self.on_friend_request(from_id)

                # Happens on every login
                elif mtype == "qprimer":
                    pass

                # Is sent before any other message
                elif mtype == "deltaflow":
                    pass

                # Unknown message type
                else:
                    self.onUnknownMesssageType(msg=m)

            except Exception as e:
                self.onMessageError(exception=e, msg=m)


    @deprecated(deprecated_in='0.10.2', removed_in='0.15.0', details='Use startListening() instead')
    def start_listening(self):
        return self.startListening()

    def startListening(self):
        """Start listening from an external event loop."""
        self.listening = True
        self.sticky, self.pool = self._getSticky()


    @deprecated(deprecated_in='0.10.2', removed_in='0.15.0', details='Use doOneListen() instead')
    def do_one_listen(self, markAlive=True):
        return self.doOneListen(markAlive)

    def doOneListen(self, markAlive=True):
        # type: (bool) -> None
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
        except Exception as e:
            self.onListenError(e)


    @deprecated(deprecated_in='0.10.2', removed_in='0.15.0', details='Use stopListening() instead')
    def stop_listening(self):
        return self.stopListening()

    def stopListening(self):
        """Cleans up the variables from start_listening."""
        self.listening = False
        self.sticky, self.pool = (None, None)


    def listen(self, markAlive=True):
        self.startListening()
        self.onListening()

        while self.listening:
            self.doOneListen(markAlive)

        self.stopListening()


    def getUserInfo(self, *user_ids):
        """Get user info from id. Unordered.

        :param user_ids: one or more user id(s) to query
        """

        def fbidStrip(_fbid):
            # Stripping of `fbid:` from author_id
            if type(_fbid) == int:
                return _fbid

            if type(_fbid) in [str, bytes] and 'fbid:' in _fbid:
                return int(_fbid[5:])

        user_ids = [fbidStrip(uid) for uid in user_ids]


        data = {"ids[{}]".format(i):uid for i,uid in enumerate(user_ids)}
        r = self._post(ReqUrl.USER_INFO, data)
        info = get_json(r)
        full_data= [details for profile,details in info['payload']['profiles'].items()]
        if len(full_data)==1:
            full_data=full_data[0]
        return full_data

