# -*- coding: UTF-8 -*-

from __future__ import unicode_literals
import re
import json
from time import time
from random import random
import warnings
import logging
from .models import *

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

#: Default list of user agents
USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.90 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_3) AppleWebKit/601.1.10 (KHTML, like Gecko) Version/8.0.5 Safari/601.1.10",
    "Mozilla/5.0 (Windows NT 6.3; WOW64; ; NCT50_AAP285C84A1328) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.90 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/22.0.1207.1 Safari/537.1",
    "Mozilla/5.0 (X11; CrOS i686 2268.111.0) AppleWebKit/536.11 (KHTML, like Gecko) Chrome/20.0.1132.57 Safari/536.11",
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.6 (KHTML, like Gecko) Chrome/20.0.1092.0 Safari/536.6"
]

LIKES = {
    'large': EmojiSize.LARGE,
    'medium': EmojiSize.MEDIUM,
    'small': EmojiSize.SMALL,
    'l': EmojiSize.LARGE,
    'm': EmojiSize.MEDIUM,
    's': EmojiSize.SMALL
}

MessageReactionFix = {
    '😍': ('0001f60d', '%F0%9F%98%8D'),
    '😆': ('0001f606', '%F0%9F%98%86'),
    '😮': ('0001f62e', '%F0%9F%98%AE'),
    '😢': ('0001f622', '%F0%9F%98%A2'),
    '😠': ('0001f620', '%F0%9F%98%A0'),
    '👍': ('0001f44d', '%F0%9F%91%8D'),
    '👎': ('0001f44e', '%F0%9F%91%8E')
}


GENDERS = {
    # For standard requests
    0: 'unknown',
    1: 'female_singular',
    2: 'male_singular',
    3: 'female_singular_guess',
    4: 'male_singular_guess',
    5: 'mixed',
    6: 'neuter_singular',
    7: 'unknown_singular',
    8: 'female_plural',
    9: 'male_plural',
    10: 'neuter_plural',
    11: 'unknown_plural',

    # For graphql requests
    'UNKNOWN': 'unknown',
    'FEMALE': 'female_singular',
    'MALE': 'male_singular',
    #'': 'female_singular_guess',
    #'': 'male_singular_guess',
    #'': 'mixed',
    'NEUTER': 'neuter_singular',
    #'': 'unknown_singular',
    #'': 'female_plural',
    #'': 'male_plural',
    #'': 'neuter_plural',
    #'': 'unknown_plural',
}

class ReqUrl(object):
    """A class containing all urls used by `fbchat`"""
    SEARCH = "https://www.facebook.com/ajax/typeahead/search.php"
    LOGIN = "https://m.facebook.com/login.php?login_attempt=1"
    SEND = "https://www.facebook.com/messaging/send/"
    THREAD_SYNC = "https://www.facebook.com/ajax/mercury/thread_sync.php"
    THREADS = "https://www.facebook.com/ajax/mercury/threadlist_info.php"
    MESSAGES = "https://www.facebook.com/ajax/mercury/thread_info.php"
    READ_STATUS = "https://www.facebook.com/ajax/mercury/change_read_status.php"
    DELIVERED = "https://www.facebook.com/ajax/mercury/delivery_receipts.php"
    MARK_SEEN = "https://www.facebook.com/ajax/mercury/mark_seen.php"
    BASE = "https://www.facebook.com"
    MOBILE = "https://m.facebook.com/"
    STICKY = "https://0-edge-chat.facebook.com/pull"
    PING = "https://0-edge-chat.facebook.com/active_ping"
    UPLOAD = "https://upload.facebook.com/ajax/mercury/upload.php"
    INFO = "https://www.facebook.com/chat/user_info/"
    CONNECT = "https://www.facebook.com/ajax/add_friend/action.php?dpr=1"
    REMOVE_USER = "https://www.facebook.com/chat/remove_participants/"
    LOGOUT = "https://www.facebook.com/logout.php"
    ALL_USERS = "https://www.facebook.com/chat/user_info_all"
    SAVE_DEVICE = "https://m.facebook.com/login/save-device/cancel/"
    CHECKPOINT = "https://m.facebook.com/login/checkpoint/"
    THREAD_COLOR = "https://www.facebook.com/messaging/save_thread_color/?source=thread_settings&dpr=1"
    THREAD_NICKNAME = "https://www.facebook.com/messaging/save_thread_nickname/?source=thread_settings&dpr=1"
    THREAD_EMOJI = "https://www.facebook.com/messaging/save_thread_emoji/?source=thread_settings&dpr=1"
    MESSAGE_REACTION = "https://www.facebook.com/webgraphql/mutation"
    TYPING = "https://www.facebook.com/ajax/messaging/typ.php"
    GRAPHQL = "https://www.facebook.com/api/graphqlbatch/"
    ATTACHMENT_PHOTO = "https://www.facebook.com/mercury/attachments/photo/"
    EVENT_REMINDER = "https://www.facebook.com/ajax/eventreminder/create"

    pull_channel = 0

    def change_pull_channel(self, channel=None):
        if channel is None:
            self.pull_channel = (self.pull_channel + 1) % 5 # Pull channel will be 0-4
        else:
            self.pull_channel = channel
        self.STICKY = "https://{}-edge-chat.facebook.com/pull".format(self.pull_channel)
        self.PING = "https://{}-edge-chat.facebook.com/active_ping".format(self.pull_channel)


facebookEncoding = 'UTF-8'

def now():
    return int(time()*1000)

def strip_to_json(text):
    try:
        return text[text.index('{'):]
    except ValueError:
        raise FBchatException('No JSON object found: {}, {}'.format(repr(text), text.index('{')))

def get_decoded_r(r):
    return get_decoded(r._content)

def get_decoded(content):
    return content.decode(facebookEncoding)

def parse_json(content):
    return json.loads(content)

def get_json(r):
    return json.loads(strip_to_json(get_decoded_r(r)))

def digitToChar(digit):
    if digit < 10:
        return str(digit)
    return chr(ord('a') + digit - 10)

def str_base(number, base):
    if number < 0:
        return '-' + str_base(-number, base)
    (d, m) = divmod(number, base)
    if d > 0:
        return str_base(d, base) + digitToChar(m)
    return digitToChar(m)

def generateMessageID(client_id=None):
    k = now()
    l = int(random() * 4294967295)
    return "<{}:{}-{}@mail.projektitan.com>".format(k, l, client_id)

def getSignatureID():
    return hex(int(random() * 2147483648))

def generateOfflineThreadingID():
    ret = now()
    value = int(random() * 4294967295)
    string = ("0000000000000000000000" + format(value, 'b'))[-22:]
    msgs = format(ret, 'b') + string
    return str(int(msgs, 2))

def check_json(j):
    if j.get('error') is None:
        return
    if 'errorDescription' in j:
        # 'errorDescription' is in the users own language!
        raise FBchatFacebookError('Error #{} when sending request: {}'.format(j['error'], j['errorDescription']), fb_error_code=j['error'], fb_error_message=j['errorDescription'])
    elif 'debug_info' in j['error'] and 'code' in j['error']:
        raise FBchatFacebookError('Error #{} when sending request: {}'.format(j['error']['code'], repr(j['error']['debug_info'])), fb_error_code=j['error']['code'], fb_error_message=j['error']['debug_info'])
    else:
        raise FBchatFacebookError('Error {} when sending request'.format(j['error']), fb_error_code=j['error'])

def check_request(r, as_json=True):
    if not r.ok:
        raise FBchatFacebookError('Error when sending request: Got {} response'.format(r.status_code), request_status_code=r.status_code)

    content = get_decoded_r(r)

    if content is None or len(content) == 0:
        raise FBchatFacebookError('Error when sending request: Got empty response')

    if as_json:
        content = strip_to_json(content)
        try:
            j = json.loads(content)
        except ValueError:
            raise FBchatFacebookError('Error while parsing JSON: {}'.format(repr(content)))
        check_json(j)
        return j
    else:
        return content

def get_jsmods_require(j, index):
    if j.get('jsmods') and j['jsmods'].get('require'):
        try:
            return j['jsmods']['require'][0][index][0]
        except (KeyError, IndexError) as e:
            log.warning('Error when getting jsmods_require: {}. Facebook might have changed protocol'.format(j))
    return None

def get_emojisize_from_tags(tags):
    if tags is None:
        return None
    tmp = [tag for tag in tags if tag.startswith('hot_emoji_size:')]
    if len(tmp) > 0:
        try:
            return LIKES[tmp[0].split(':')[1]]
        except (KeyError, IndexError):
            log.exception('Could not determine emoji size from {} - {}'.format(tags, tmp))
    return None
