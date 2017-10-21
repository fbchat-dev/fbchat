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

test_sticker_id = '767334476626295'

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
        for thread in threads:
            client.setDefaultThread(thread_id=thread['id'], thread_type=thread['type'])
            self.assertTrue(client.send(Message(text='test_default_recipient★')))

        # resetDefaultThread
        client.resetDefaultThread()
        with self.assertRaises(ValueError):
            client.send(Message(text='should_not_send'))

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

    def test_send(self):
        for thread in threads:
            client.setDefaultThread(thread_id=thread['id'], thread_type=thread['type'])

            self.assertIsNotNone(client.send(Message(emoji_size=EmojiSize.SMALL)))
            self.assertIsNotNone(client.send(Message(emoji_size=EmojiSize.MEDIUM)))
            self.assertIsNotNone(client.send(Message(text='😆', emoji_size=EmojiSize.LARGE)))

            self.assertIsNotNone(client.send(Message(text='test_send★')))
            with self.assertRaises(FBchatFacebookError):
                self.assertIsNotNone(client.send(Message(text='test_send_should_fail★'), thread_id=thread['id'], thread_type=(ThreadType.GROUP if thread['type'] == ThreadType.USER else ThreadType.USER)))

            self.assertIsNotNone(client.send(Message(text='Hi there @user', mentions=[Mention(user_id, offset=9, length=5)])))
            self.assertIsNotNone(client.send(Message(text='Hi there @group', mentions=[Mention(group_id, offset=9, length=6)])))

            self.assertIsNotNone(client.send(Message(sticker=Sticker(test_sticker_id))))

    def test_sendImages(self):
        image_url = 'https://cdn4.iconfinder.com/data/icons/ionicons/512/icon-image-128.png'
        image_local_url = path.join(path.dirname(__file__), 'tests/image.png')
        for thread in threads:
            client.setDefaultThread(thread_id=thread['id'], thread_type=thread['type'])
            mentions = [Mention(thread['id'], offset=26, length=4)]
            self.assertTrue(client.sendRemoteImage(image_url, Message(text='test_send_image_remote_to_@you★', mentions=mentions)))
            self.assertTrue(client.sendLocalImage(image_local_url, Message(text='test_send_image_local_to__@you★', mentions=mentions)))

    def test_fetchThreadList(self):
        client.fetchThreadList(offset=0, limit=20)

    def test_fetchThreadMessages(self):
        for thread in threads:
            client.setDefaultThread(thread_id=thread['id'], thread_type=thread['type'])
            client.send(Message(text='test_getThreadInfo★'))

            messages = client.fetchThreadMessages(limit=1)
            self.assertEqual(messages[0].author, client.uid)
            self.assertEqual(messages[0].text, 'test_getThreadInfo★')

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
        for thread in threads:
            client.changeThreadTitle('test_changeThreadTitle★', thread_id=thread['id'], thread_type=thread['type'])

    def test_changeNickname(self):
        for thread in threads:
            client.setDefaultThread(thread_id=thread['id'], thread_type=thread['type'])
            client.changeNickname('test_changeNicknameSelf★', client.uid)
            client.changeNickname('test_changeNicknameOther★', user_id)

    def test_changeThreadEmoji(self):
        for thread in threads:
            client.changeThreadEmoji('😀', thread_id=thread['id'])
            client.changeThreadEmoji('😀', thread_id=thread['id'])

    def test_changeThreadColor(self):
        for thread in threads:
            client.setDefaultThread(thread_id=thread['id'], thread_type=thread['type'])
            client.changeThreadColor(ThreadColor.BRILLIANT_ROSE)
            client.changeThreadColor(ThreadColor.MESSENGER_BLUE)

    def test_reactToMessage(self):
        for thread in threads:
            mid = client.send(Message(text='test_reactToMessage★'), thread_id=thread['id'], thread_type=thread['type'])
            client.reactToMessage(mid, MessageReaction.LOVE)

    def test_setTypingStatus(self):
        for thread in threads:
            client.setDefaultThread(thread_id=thread['id'], thread_type=thread['type'])
            client.setTypingStatus(TypingStatus.TYPING)
            client.setTypingStatus(TypingStatus.STOPPED)


def start_test(param_client, param_group_id, param_user_id, param_threads, tests=[]):
    global client
    global group_id
    global user_id
    global threads

    client = param_client
    group_id = param_group_id
    user_id = param_user_id
    threads = param_threads

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
            j = json.load(f)
        email = j['email']
        password = j['password']
        user_id = j['user_thread_id']
        group_id = j['group_thread_id']
        session = j.get('session')
    except (IOError, IndexError) as e:
        email = input('Email: ')
        password = getpass()
        group_id = input('Please enter a group thread id (To test group functionality): ')
        user_id = input('Please enter a user thread id (To test kicking/adding functionality): ')
    threads = [
        {
            'id': user_id,
            'type': ThreadType.USER
        },
        {
            'id': group_id,
            'type': ThreadType.GROUP
        }
    ]

    print('Logging in...')
    client = CustomClient(email, password, logging_level=logging_level, session_cookies=session)

    # Warning! Taking user input directly like this could be dangerous! Use only for testing purposes!
    start_test(client, group_id, user_id, threads, argv[1:])

    with open(path.join(path.dirname(__file__), 'tests/my_data.json'), 'w') as f:
        session = None
        try:
            session = client.getSession()
        except Exception:
            print('Unable to fetch client session!')
        json.dump({
            'email': email,
            'password': password,
            'user_thread_id': user_id,
            'group_thread_id': group_id,
            'session': session
        }, f)
