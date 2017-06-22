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

TYPES = {
    'Page': ThreadType.PAGE,
    'User': ThreadType.USER,
    'Group': ThreadType.GROUP
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
    #'': 'unknown',
    'FEMALE': 'female_singular',
    'MALE': 'male_singular',
    #'': 'female_singular_guess',
    #'': 'male_singular_guess',
    #'': 'mixed',
    #'': 'neuter_singular',
    #'': 'unknown_singular',
    #'': 'female_plural',
    #'': 'male_plural',
    #'': 'neuter_plural',
    #'': 'unknown_plural',
    None: None
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


facebookEncoding = 'UTF-8'

def now():
    return int(time()*1000)

def strip_to_json(text):
    try:
        return text[text.index('{'):]
    except ValueError as e:
        return None

def get_decoded(r):
    if not isinstance(r._content, str):
        return r._content.decode(facebookEncoding)
    else:
        return r._content

def get_json(r):
    return json.loads(strip_to_json(get_decoded(r)))

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
    if 'error' in j and j['error'] is not None:
        if 'errorDescription' in j:
            # 'errorDescription' is in the users own language!
            raise Exception('Error #{} when sending request: {}'.format(j['error'], j['errorDescription']))
        elif 'debug_info' in j['error']:
            raise Exception('Error #{} when sending request: {}'.format(j['error']['code'], repr(j['error']['debug_info'])))
        else:
            raise Exception('Error {} when sending request'.format(j['error']))

def checkRequest(r, do_json_check=True):
    if not r.ok:
        raise Exception('Error when sending request: Got {} response'.format(r.status_code))

    content = get_decoded(r)

    if content is None or len(content) == 0:
        raise Exception('Error when sending request: Got empty response')

    if do_json_check:
        try:
            j = json.loads(strip_to_json(content))
        except Exception as e:
            raise Exception('Error while parsing JSON: {}'.format(repr(content)))
        check_json(j)
        return j
    else:
        return content
