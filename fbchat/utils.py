# -*- coding: UTF-8 -*-

from __future__ import unicode_literals
import re
import json
from time import time
from random import random
from contextlib import contextmanager
from mimetypes import guess_type
from os.path import basename
import warnings
import logging
import requests
from .models import *

try:
    from urllib.parse import urlencode
    basestring = (str, bytes)
except ImportError:
    from urllib import urlencode
    basestring = basestring

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
    UNREAD_THREADS = "https://www.facebook.com/ajax/mercury/unread_threads.php"
    UNSEEN_THREADS = "https://www.facebook.com/mercury/unseen_thread_ids/"
    THREADS = "https://www.facebook.com/ajax/mercury/threadlist_info.php"
    MOVE_THREAD = "https://www.facebook.com/ajax/mercury/move_thread.php"
    ARCHIVED_STATUS = "https://www.facebook.com/ajax/mercury/change_archived_status.php?dpr=1"
    PINNED_STATUS = "https://www.facebook.com/ajax/mercury/change_pinned_status.php?dpr=1"
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
    THREAD_IMAGE = "https://www.facebook.com/messaging/set_thread_image/?dpr=1"
    THREAD_NAME = "https://www.facebook.com/messaging/set_thread_name/?dpr=1"
    MESSAGE_REACTION = "https://www.facebook.com/webgraphql/mutation"
    TYPING = "https://www.facebook.com/ajax/messaging/typ.php"
    GRAPHQL = "https://www.facebook.com/api/graphqlbatch/"
    ATTACHMENT_PHOTO = "https://www.facebook.com/mercury/attachments/photo/"
    PLAN_CREATE = "https://www.facebook.com/ajax/eventreminder/create"
    PLAN_INFO = "https://www.facebook.com/ajax/eventreminder"
    PLAN_CHANGE = "https://www.facebook.com/ajax/eventreminder/submit"
    PLAN_PARTICIPATION = "https://www.facebook.com/ajax/eventreminder/rsvp"
    MODERN_SETTINGS_MENU = "https://www.facebook.com/bluebar/modern_settings_menu/"
    REMOVE_FRIEND = "https://m.facebook.com/a/removefriend.php"
    BLOCK_USER = "https://www.facebook.com/messaging/block_messages/?dpr=1"
    UNBLOCK_USER = "https://www.facebook.com/messaging/unblock_messages/?dpr=1"
    SAVE_ADMINS = "https://www.facebook.com/messaging/save_admins/?dpr=1"
    APPROVAL_MODE = "https://www.facebook.com/messaging/set_approval_mode/?dpr=1"
    CREATE_GROUP = "https://m.facebook.com/messages/send/?icm=1"
    DELETE_THREAD = "https://www.facebook.com/ajax/mercury/delete_thread.php?dpr=1"
    DELETE_MESSAGES = "https://www.facebook.com/ajax/mercury/delete_messages.php?dpr=1"
    MUTE_THREAD = "https://www.facebook.com/ajax/mercury/change_mute_thread.php?dpr=1"
    MUTE_REACTIONS = "https://www.facebook.com/ajax/mercury/change_reactions_mute_thread/?dpr=1"
    MUTE_MENTIONS = "https://www.facebook.com/ajax/mercury/change_mentions_mute_thread/?dpr=1"
    CREATE_POLL = "https://www.facebook.com/messaging/group_polling/create_poll/?dpr=1"
    UPDATE_VOTE = "https://www.facebook.com/messaging/group_polling/update_vote/?dpr=1"
    GET_POLL_OPTIONS = "https://www.facebook.com/ajax/mercury/get_poll_options"
    SEARCH_MESSAGES = "https://www.facebook.com/ajax/mercury/search_snippets.php?dpr=1"
    MARK_SPAM = "https://www.facebook.com/ajax/mercury/mark_spam.php?dpr=1"

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
        raise FBchatException('No JSON object found: {!r}'.format(text))

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
            raise FBchatFacebookError('Error while parsing JSON: {!r}'.format(content))
        check_json(j)
        log.debug(j)
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

def require_list(list_):
    if isinstance(list_, list):
        return set(list_)
    else:
        return set([list_])

def mimetype_to_key(mimetype):
    if not mimetype:
        return "file_id"
    if mimetype == "image/gif":
        return "gif_id"
    x = mimetype.split("/")
    if x[0] in ["video", "image", "audio"]:
        return "%s_id" % x[0]
    return "file_id"


def get_files_from_urls(file_urls):
    files = []
    for file_url in file_urls:
        r = requests.get(file_url)
        # We could possibly use r.headers.get('Content-Disposition'), see
        # https://stackoverflow.com/a/37060758
        files.append((
            basename(file_url),
            r.content,
            r.headers.get('Content-Type') or guess_type(file_url)[0],
        ))
    return files


@contextmanager
def get_files_from_paths(filenames):
    files = []
    for filename in filenames:
        files.append((
            basename(filename),
            open(filename, 'rb'),
            guess_type(filename)[0],
        ))
    yield files
    for fn, fp, ft in files:
        fp.close()
