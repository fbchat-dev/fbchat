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

    def onQprimer(self, msg, **kwargs):
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
            client.login('<email>', '<password>', max_tries=1)

        client.login(email, password)

        self.assertTrue(client.isLoggedIn())

    def test_sessions(self):
        global client
        session_cookies = client.getSession()
        client = CustomClient(email, password, session_cookies=session_cookies, logging_level=logging_level)

        self.assertTrue(client.isLoggedIn())

    def test_defaultThread(self):
        # setDefaultThread
        client.setDefaultThread(group_id, ThreadType.GROUP)
        self.assertTrue(client.sendMessage('test_default_recipient★'))

        client.setDefaultThread(user_id, ThreadType.USER)
        self.assertTrue(client.sendMessage('test_default_recipient★'))

        # resetDefaultThread
        client.resetDefaultThread()
        with self.assertRaises(ValueError):
            client.sendMessage('should_not_send')

    def test_fetchAllUsers(self):
        users = client.fetchAllUsers()
        self.assertGreater(len(users), 0)

    def test_searchFor(self):
        users = client.searchForUsers('Mark Zuckerberg')
        self.assertGreater(len(users), 0)

        u = users[0]

        # Test if values are set correctly
        self.assertEqual(u.uid, '4')
        self.assertEqual(u.type, ThreadType.USER)
        self.assertEqual(u.photo[:4], 'http')
        self.assertEqual(u.url[:4], 'http')
        self.assertEqual(u.name, 'Mark Zuckerberg')

        group_name = client.changeThreadTitle('tést_searchFor', thread_id=group_id, thread_type=ThreadType.GROUP)
        groups = client.searchForGroups('té')
        self.assertGreater(len(groups), 0)

    def test_sendEmoji(self):
        self.assertIsNotNone(client.sendEmoji(size=EmojiSize.SMALL, thread_id=user_id, thread_type=ThreadType.USER))
        self.assertIsNotNone(client.sendEmoji(size=EmojiSize.MEDIUM, thread_id=user_id, thread_type=ThreadType.USER))
        self.assertIsNotNone(client.sendEmoji('😆', EmojiSize.LARGE, user_id, ThreadType.USER))

        self.assertIsNotNone(client.sendEmoji(size=EmojiSize.SMALL, thread_id=group_id, thread_type=ThreadType.GROUP))
        self.assertIsNotNone(client.sendEmoji(size=EmojiSize.MEDIUM, thread_id=group_id, thread_type=ThreadType.GROUP))
        self.assertIsNotNone(client.sendEmoji('😆', EmojiSize.LARGE, group_id, ThreadType.GROUP))

    def test_sendMessage(self):
        self.assertIsNotNone(client.sendMessage('test_send_user★', user_id, ThreadType.USER))
        self.assertIsNotNone(client.sendMessage('test_send_group★', group_id, ThreadType.GROUP))
        with self.assertRaises(Exception):
            client.sendMessage('test_send_user_should_fail★', user_id, ThreadType.GROUP)
        with self.assertRaises(Exception):
            client.sendMessage('test_send_group_should_fail★', group_id, ThreadType.USER)

    def test_sendImages(self):
        image_url = 'https://cdn4.iconfinder.com/data/icons/ionicons/512/icon-image-128.png'
        image_local_url = path.join(path.dirname(__file__), 'tests/image.png')
        self.assertTrue(client.sendRemoteImage(image_url, 'test_send_user_images_remote★', user_id, ThreadType.USER))
        self.assertTrue(client.sendRemoteImage(image_url, 'test_send_group_images_remote★', group_id, ThreadType.GROUP))
        self.assertTrue(client.sendLocalImage(image_local_url, 'test_send_group_images_local★', user_id, ThreadType.USER))
        self.assertTrue(client.sendLocalImage(image_local_url, 'test_send_group_images_local★', group_id, ThreadType.GROUP))

    def test_fetchThreadList(self):
        client.fetchThreadList(offset=0, limit=20)

    def test_fetchThreadMessages(self):
        client.sendMessage('test_user_getThreadInfo★', thread_id=user_id, thread_type=ThreadType.USER)

        messages = client.fetchThreadMessages(thread_id=user_id, limit=1)
        self.assertEqual(messages[0].author, client.uid)
        self.assertEqual(messages[0].text, 'test_user_getThreadInfo★')

        client.sendMessage('test_group_getThreadInfo★', thread_id=group_id, thread_type=ThreadType.GROUP)

        messages = client.fetchThreadMessages(thread_id=group_id, limit=1)
        self.assertEqual(messages[0].author, client.uid)
        self.assertEqual(messages[0].text, 'test_group_getThreadInfo★')

    def test_listen(self):
        client.startListening()
        client.doOneListen()
        client.stopListening()

        self.assertTrue(client.got_qprimer)

    def test_fetchInfo(self):
        info = client.fetchUserInfo('4')['4']
        self.assertEqual(info.name, 'Mark Zuckerberg')

        info = client.fetchGroupInfo(group_id)[group_id]
        self.assertEqual(info.type, ThreadType.GROUP)

    def test_removeAddFromGroup(self):
        client.removeUserFromGroup(user_id, thread_id=group_id)
        client.addUsersToGroup(user_id, thread_id=group_id)

    def test_changeThreadTitle(self):
        client.changeThreadTitle('test_changeThreadTitle★', thread_id=group_id, thread_type=ThreadType.GROUP)
        client.changeThreadTitle('test_changeThreadTitle★', thread_id=user_id, thread_type=ThreadType.USER)

    def test_changeNickname(self):
        client.changeNickname('test_changeNicknameSelf★', client.uid, thread_id=user_id, thread_type=ThreadType.USER)
        client.changeNickname('test_changeNicknameOther★', user_id, thread_id=user_id, thread_type=ThreadType.USER)
        client.changeNickname('test_changeNicknameSelf★', client.uid, thread_id=group_id, thread_type=ThreadType.GROUP)
        client.changeNickname('test_changeNicknameOther★', user_id, thread_id=group_id, thread_type=ThreadType.GROUP)

    def test_changeThreadEmoji(self):
        client.changeThreadEmoji('😀', group_id)
        client.changeThreadEmoji('😀', user_id)
        client.changeThreadEmoji('😆', group_id)
        client.changeThreadEmoji('😆', user_id)

    def test_changeThreadColor(self):
        client.changeThreadColor(ThreadColor.BRILLIANT_ROSE, group_id)
        client.changeThreadColor(ThreadColor.MESSENGER_BLUE, group_id)
        client.changeThreadColor(ThreadColor.BRILLIANT_ROSE, user_id)
        client.changeThreadColor(ThreadColor.MESSENGER_BLUE, user_id)

    def test_reactToMessage(self):
        mid = client.sendMessage('test_reactToMessage★', user_id, ThreadType.USER)
        client.reactToMessage(mid, MessageReaction.LOVE)
        mid = client.sendMessage('test_reactToMessage★', group_id, ThreadType.GROUP)
        client.reactToMessage(mid, MessageReaction.LOVE)

    def test_setTypingStatus(self):
        client.setTypingStatus(TypingStatus.TYPING, thread_id=user_id, thread_type=ThreadType.USER)
        client.setTypingStatus(TypingStatus.STOPPED, thread_id=user_id, thread_type=ThreadType.USER)
        client.setTypingStatus(TypingStatus.TYPING, thread_id=group_id, thread_type=ThreadType.GROUP)
        client.setTypingStatus(TypingStatus.STOPPED, thread_id=group_id, thread_type=ThreadType.GROUP)


def start_test(param_client, param_group_id, param_user_id, tests=[]):
    global client
    global group_id
    global user_id

    client = param_client
    group_id = param_group_id
    user_id = param_user_id

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
        user_id = json['user_thread_id']
        group_id = json['group_thread_id']
    except (IOError, IndexError) as e:
        email = input('Email: ')
        password = getpass()
        group_id = input('Please enter a group thread id (To test group functionality): ')
        user_id = input('Please enter a user thread id (To test kicking/adding functionality): ')

    print('Logging in...')
    client = CustomClient(email, password, logging_level=logging_level)

    # Warning! Taking user input directly like this could be dangerous! Use only for testing purposes!
    start_test(client, group_id, user_id, argv[1:])
