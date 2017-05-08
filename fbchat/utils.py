import re
import json
from time import time
from random import random
USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.90 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_3) AppleWebKit/601.1.10 (KHTML, like Gecko) Version/8.0.5 Safari/601.1.10",
    "Mozilla/5.0 (Windows NT 6.3; WOW64; ; NCT50_AAP285C84A1328) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.90 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/22.0.1207.1 Safari/537.1",
    "Mozilla/5.0 (X11; CrOS i686 2268.111.0) AppleWebKit/536.11 (KHTML, like Gecko) Chrome/20.0.1132.57 Safari/536.11",
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.6 (KHTML, like Gecko) Chrome/20.0.1092.0 Safari/536.6"
]
GENDERS = {
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
}

def now():
    return int(time()*1000)

def strip_to_json(text):
    return text[text.index('{'):]

def get_json(text):
    return json.loads(strip_to_json(text))

def digit_to_char(digit):
    if digit < 10:
        return str(digit)
    return chr(ord('a') + digit - 10)

def str_base(number,base):
    if number < 0:
        return '-' + str_base(-number, base)
    (d, m) = divmod(number, base)
    if d > 0:
        return str_base(d, base) + digit_to_char(m)
    return digit_to_char(m)

def generateMessageID(client_id=None):
    k = now()
    l = int(random() * 4294967295)
    return ("<%s:%s-%s@mail.projektitan.com>" % (k, l, client_id));

def getSignatureID():
    return hex(int(random() * 2147483648))

def generateOfflineThreadingID() :
    ret = now()
    value = int(random() * 4294967295);
    string = ("0000000000000000000000" + bin(value))[-22:]
    msgs = bin(ret) + string
    return str(int(msgs,2))

