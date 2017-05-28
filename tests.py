#!/usr/bin/env python
# -*- coding: UTF-8 -*-

from __future__ import unicode_literals
import json
import logging
import unittest
from getpass import getpass
from sys import argv
from os import path, chdir
from glob import glob
from fbchat import Client
from fbchat.models import *
import py_compile

logging_level = logging.ERROR

"""

Testing script for `fbchat`.
Full documentation on https://fbchat.readthedocs.io/

"""

class CustomClient(Client):
    def __init__(self, *args, **kwargs):
        self.got_qprimer = False
        super(type(self), self).__init__(*args, **kwargs)

    def onQprimer(self, made, msg):
        self.got_qprimer = True

class TestFbchat(unittest.TestCase):
    def test_examples(self):
        # Checks for syntax errors in the examples
        chdir('examples')
        for f in glob('*.txt'):
            print(f)
            with self.assertRaises(py_compile.PyCompileError):
                py_compile.compile(f)

        chdir('..')

    def test_loginFunctions(self):
        self.assertTrue(client.isLoggedIn())

        client.logout()

        self.assertFalse(client.isLoggedIn())

        with self.assertRaises(Exception):
            client.login('<email>', '<password>', max_retries=1)

        client.login(email, password)

        self.assertTrue(client.isLoggedIn())

    def test_sessions(self):
        global client
        session_cookies = client.getSession()
        client = CustomClient(email, password, session_cookies=session_cookies, logging_level=logging_level)

        self.assertTrue(client.isLoggedIn())

    def test_defaultThread(self):
        # setDefaultThread
        client.setDefaultThread(group_uid, ThreadType.GROUP)
        self.assertTrue(client.sendMessage('test_default_recipient★'))

        client.setDefaultThread(user_uid, ThreadType.USER)
        self.assertTrue(client.sendMessage('test_default_recipient★'))

        # resetDefaultThread
        client.resetDefaultThread()
        with self.assertRaises(ValueError):
            client.sendMessage('should_not_send')

    def test_getAllUsers(self):
        users = client.getAllUsers()
        self.assertGreater(len(users), 0)

    def test_getUsers(self):
        users = client.getUsers('Mark Zuckerberg')
        self.assertGreater(len(users), 0)

        u = users[0]

        # Test if values are set correctly
        self.assertIsInstance(u.uid, int)
        self.assertEqual(u.type, 'user')
        self.assertEqual(u.photo[:4], 'http')
        self.assertEqual(u.url[:4], 'http')
        self.assertEqual(u.name, 'Mark Zuckerberg')
        self.assertGreater(u.score, 0)

    def test_sendEmoji(self):
        self.assertTrue(client.sendEmoji(size=EmojiSize.SMALL, thread_id=user_uid, thread_type=ThreadType.USER))
        self.assertTrue(client.sendEmoji(size=EmojiSize.MEDIUM, thread_id=user_uid, thread_type=ThreadType.USER))
        self.assertTrue(client.sendEmoji('😆', EmojiSize.LARGE, user_uid, ThreadType.USER))

        self.assertTrue(client.sendEmoji(size=EmojiSize.SMALL, thread_id=group_uid, thread_type=ThreadType.GROUP))
        self.assertTrue(client.sendEmoji(size=EmojiSize.MEDIUM, thread_id=group_uid, thread_type=ThreadType.GROUP))
        self.assertTrue(client.sendEmoji('😆', EmojiSize.LARGE, group_uid, ThreadType.GROUP))

    def test_sendMessage(self):
        self.assertIsNotNone(client.sendMessage('test_send_user★', user_uid, ThreadType.USER))
        self.assertIsNotNone(client.sendMessage('test_send_group★', group_uid, ThreadType.GROUP))
        self.assertIsNone(client.sendMessage('test_send_user_should_fail★', user_uid, ThreadType.GROUP))
        self.assertIsNone(client.sendMessage('test_send_group_should_fail★', group_uid, ThreadType.USER))

    def test_sendImages(self):
        image_url = 'https://cdn4.iconfinder.com/data/icons/ionicons/512/icon-image-128.png'
        image_local_url = path.join(path.dirname(__file__), 'tests/image.png')
        self.assertTrue(client.sendRemoteImage(image_url, 'test_send_user_images_remote★', user_uid, ThreadType.USER))
        self.assertTrue(client.sendRemoteImage(image_url, 'test_send_group_images_remote★', group_uid, ThreadType.GROUP))
        self.assertTrue(client.sendLocalImage(image_local_url, 'test_send_group_images_local★', user_uid, ThreadType.USER))
        self.assertTrue(client.sendLocalImage(image_local_url, 'test_send_group_images_local★', group_uid, ThreadType.GROUP))

    def test_getThreadInfo(self):
        client.sendMessage('test_user_getThreadInfo★', user_uid, ThreadType.USER)

        info = client.getThreadInfo(20, user_uid, ThreadType.USER)
        self.assertEqual(info[0].author, 'fbid:' + client.uid)
        self.assertEqual(info[0].body, 'test_user_getThreadInfo★')

        client.sendMessage('test_group_getThreadInfo★', group_uid, ThreadType.GROUP)

        info = client.getThreadInfo(20, group_uid, ThreadType.GROUP)
        self.assertEqual(info[0].author, 'fbid:' + client.uid)
        self.assertEqual(info[0].body, 'test_group_getThreadInfo★')

    def test_listen(self):
        client.startListening()
        client.doOneListen()
        client.stopListening()

        self.assertTrue(client.got_qprimer)

    def test_getUserInfo(self):
        info = client.getUserInfo(4)
        self.assertEqual(info['name'], 'Mark Zuckerberg')

    def test_removeAddFromGroup(self):
        self.assertTrue(client.removeUserFromGroup(user_uid, thread_id=group_uid))
        self.assertTrue(client.addUsersToGroup(user_uid, thread_id=group_uid))

    def test_changeThreadTitle(self):
        self.assertTrue(client.changeThreadTitle('test_changeThreadTitle★', thread_id=group_uid, thread_type=ThreadType.GROUP))
        self.assertTrue(client.changeThreadTitle('test_changeThreadTitle★', thread_id=user_uid, thread_type=ThreadType.USER))

    def test_changeNickname(self):
        self.assertTrue(client.changeNickname('test_changeNicknameSelf★', client.uid, thread_id=user_uid, thread_type=ThreadType.USER))
        self.assertTrue(client.changeNickname('test_changeNicknameOther★', user_uid, thread_id=user_uid, thread_type=ThreadType.USER))
        self.assertTrue(client.changeNickname('test_changeNicknameSelf★', client.uid, thread_id=group_uid, thread_type=ThreadType.GROUP))
        self.assertTrue(client.changeNickname('test_changeNicknameOther★', user_uid, thread_id=group_uid, thread_type=ThreadType.GROUP))

    def test_changeThreadEmoji(self):
        self.assertTrue(client.changeThreadEmoji('😀', group_uid))
        self.assertTrue(client.changeThreadEmoji('😀', user_uid))
        self.assertTrue(client.changeThreadEmoji('😆', group_uid))
        self.assertTrue(client.changeThreadEmoji('😆', user_uid))

    def test_changeThreadColor(self):
        self.assertTrue(client.changeThreadColor(ThreadColor.BRILLIANT_ROSE, group_uid))
        self.assertTrue(client.changeThreadColor(ThreadColor.MESSENGER_BLUE, group_uid))
        self.assertTrue(client.changeThreadColor(ThreadColor.BRILLIANT_ROSE, user_uid))
        self.assertTrue(client.changeThreadColor(ThreadColor.MESSENGER_BLUE, user_uid))

    def test_reactToMessage(self):
        mid = client.sendMessage('test_reactToMessage★', user_uid, ThreadType.USER)
        self.assertTrue(client.reactToMessage(mid, MessageReaction.LOVE))
        mid = client.sendMessage('test_reactToMessage★', group_uid, ThreadType.GROUP)
        self.assertTrue(client.reactToMessage(mid, MessageReaction.LOVE))

    def test_setTypingStatus(self):
        self.assertTrue(client.sendMessage('Hi', thread_id=user_uid, thread_type=ThreadType.USER))
        self.assertTrue(client.setTypingStatus(TypingStatus.TYPING, thread_id=user_uid, thread_type=ThreadType.USER))
        self.assertTrue(client.setTypingStatus(TypingStatus.STOPPED, thread_id=user_uid, thread_type=ThreadType.USER))
        self.assertTrue(client.setTypingStatus(TypingStatus.TYPING, thread_id=group_uid, thread_type=ThreadType.GROUP))
        self.assertTrue(client.setTypingStatus(TypingStatus.STOPPED, thread_id=group_uid, thread_type=ThreadType.GROUP))


def start_test(param_client, param_group_uid, param_user_uid, tests=[]):
    global client
    global group_uid
    global user_uid

    client = param_client
    group_uid = param_group_uid
    user_uid = param_user_uid

    tests = ['test_' + test if 'test_' != test[:5] else test for test in tests]

    if len(tests) == 0:
        suite = unittest.TestLoader().loadTestsFromTestCase(TestFbchat)
    else:
        suite = unittest.TestSuite(map(TestFbchat, tests))
    print('Starting test(s)')
    unittest.TextTestRunner(verbosity=2).run(suite)


client = None

if __name__ == '__main__':
    # Python 3 does not use raw_input, whereas Python 2 does
    try:
        input = raw_input
    except Exception as e:
        pass

    try:
        with open(path.join(path.dirname(__file__), 'tests/my_data.json'), 'r') as f:
            json = json.load(f)
        email = json['email']
        password = json['password']
        user_uid = json['user_thread_id']
        group_uid = json['group_thread_id']
    except (IOError, IndexError) as e:
        email = input('Email: ')
        password = getpass()
        group_uid = input('Please enter a group thread id (To test group functionality): ')
        user_uid = input('Please enter a user thread id (To test kicking/adding functionality): ')

    print('Logging in...')
    client = CustomClient(email, password, logging_level=logging_level)

    # Warning! Taking user input directly like this could be dangerous! Use only for testing purposes!
    start_test(client, group_uid, user_uid, argv[1:])
