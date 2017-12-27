#!/usr/bin/env python
# -*- coding: UTF-8 -*-

from __future__ import unicode_literals
import json
import logging
import unittest
from os import environ
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
    @classmethod
    def setUpClass(self):
        self.email = environ['FBCHAT_EMAIL']
        self.password = environ['FBCHAT_PASSWORD']
        self.client = CustomClient(self.email, self.password, logging_level=logging_level)
        self.user_id = '100023782141139'
        self.group_id = '1463789480385605'
        self.threads = [
            {
                'id': self.user_id,
                'type': ThreadType.USER
            },
            {
                'id': self.group_id,
                'type': ThreadType.GROUP
            }
        ]

    @classmethod
    def tearDownClass(self):
        pass

    def test_examples(self):
        # Checks for syntax errors in the examples
        chdir('examples')
        for f in glob('*.txt'):
            print(f)
            with self.assertRaises(py_compile.PyCompileError):
                py_compile.compile(f)

        chdir('..')

    def test_loginFunctions(self):
        self.assertTrue(self.client.isLoggedIn())

        self.client.logout()

        self.assertFalse(self.client.isLoggedIn())

        with self.assertRaises(Exception):
            self.client.login('<email>', '<password>', max_tries=1)

        self.client.login(self.email, self.password)

        self.assertTrue(self.client.isLoggedIn())

    def test_sessions(self):
        session_cookies = self.client.getSession()
        self.client = CustomClient(self.email, self.password, session_cookies=session_cookies, logging_level=logging_level)

        self.assertTrue(self.client.isLoggedIn())

    def test_defaultThread(self):
        # setDefaultThread
        for thread in self.threads:
            self.client.setDefaultThread(thread_id=thread['id'], thread_type=thread['type'])
            self.assertTrue(self.client.send(Message(text='test_default_recipient★')))

        # resetDefaultThread
        self.client.resetDefaultThread()
        with self.assertRaises(ValueError):
            self.client.send(Message(text='should_not_send'))

    def test_fetchAllUsers(self):
        users = self.client.fetchAllUsers()
        self.assertGreater(len(users), 0)

    ''' Disabled atm. Will be fixed later
    def test_searchFor(self):
        users = self.client.searchForUsers('Mark Zuckerberg')
        self.assertGreater(len(users), 0)

        u = users[0]

        # Test if values are set correctly
        self.assertEqual(u.uid, '4')
        self.assertEqual(u.type, ThreadType.USER)
        self.assertEqual(u.photo[:4], 'http')
        self.assertEqual(u.url[:4], 'http')
        self.assertEqual(u.name, 'Mark Zuckerberg')

        group_name = self.client.changeThreadTitle('tést_searchFor', thread_id=self.group_id, thread_type=ThreadType.GROUP)
        groups = self.client.searchForGroups('té')
        self.assertGreater(len(groups), 0)
    '''

    def test_send(self):
        for thread in self.threads:
            self.client.setDefaultThread(thread_id=thread['id'], thread_type=thread['type'])

            self.assertIsNotNone(self.client.send(Message(emoji_size=EmojiSize.SMALL)))
            self.assertIsNotNone(self.client.send(Message(emoji_size=EmojiSize.MEDIUM)))
            self.assertIsNotNone(self.client.send(Message(text='😆', emoji_size=EmojiSize.LARGE)))

            self.assertIsNotNone(self.client.send(Message(text='test_send★')))
            with self.assertRaises(FBchatFacebookError):
                self.assertIsNotNone(self.client.send(Message(text='test_send_should_fail★'), thread_id=thread['id'], thread_type=(ThreadType.GROUP if thread['type'] == ThreadType.USER else ThreadType.USER)))

            self.assertIsNotNone(self.client.send(Message(text='Hi there @user', mentions=[Mention(self.user_id, offset=9, length=5)])))
            self.assertIsNotNone(self.client.send(Message(text='Hi there @group', mentions=[Mention(self.group_id, offset=9, length=6)])))

            self.assertIsNotNone(self.client.send(Message(sticker=Sticker(test_sticker_id))))

    def test_sendImages(self):
        image_url = 'https://cdn4.iconfinder.com/data/icons/ionicons/512/icon-image-128.png'
        image_local_url = path.join(path.dirname(__file__), 'tests/image.png')
        for thread in self.threads:
            self.client.setDefaultThread(thread_id=thread['id'], thread_type=thread['type'])
            mentions = [Mention(thread['id'], offset=26, length=4)]
            self.assertTrue(self.client.sendRemoteImage(image_url, Message(text='test_send_image_remote_to_@you★', mentions=mentions)))
            self.assertTrue(self.client.sendLocalImage(image_local_url, Message(text='test_send_image_local_to__@you★', mentions=mentions)))

    def test_fetchThreadList(self):
        self.client.fetchThreadList(offset=0, limit=20)

    def test_fetchThreadMessages(self):
        for thread in self.threads:
            self.client.setDefaultThread(thread_id=thread['id'], thread_type=thread['type'])
            self.client.send(Message(text='test_getThreadInfo★'))

            messages = self.client.fetchThreadMessages(limit=1)
            self.assertEqual(messages[0].author, self.client.uid)
            self.assertEqual(messages[0].text, 'test_getThreadInfo★')

    def test_listen(self):
        self.client.startListening()
        self.client.doOneListen()
        self.client.stopListening()

        self.assertTrue(self.client.got_qprimer)

    def test_fetchInfo(self):
        info = self.client.fetchUserInfo('4')['4']
        self.assertEqual(info.name, 'Mark Zuckerberg')

        info = self.client.fetchGroupInfo(self.group_id)[self.group_id]
        self.assertEqual(info.type, ThreadType.GROUP)

    def test_removeAddFromGroup(self):
        self.client.removeUserFromGroup(self.user_id, thread_id=self.group_id)
        self.client.addUsersToGroup(self.user_id, thread_id=self.group_id)

    def test_changeThreadTitle(self):
        for thread in self.threads:
            self.client.changeThreadTitle('test_changeThreadTitle★', thread_id=thread['id'], thread_type=thread['type'])

    def test_changeNickname(self):
        for thread in self.threads:
            self.client.setDefaultThread(thread_id=thread['id'], thread_type=thread['type'])
            self.client.changeNickname('test_changeNicknameSelf★', self.client.uid)
            self.client.changeNickname('test_changeNicknameOther★', self.user_id)

    def test_changeThreadEmoji(self):
        for thread in self.threads:
            self.client.changeThreadEmoji('😀', thread_id=thread['id'])
            self.client.changeThreadEmoji('😀', thread_id=thread['id'])

    def test_changeThreadColor(self):
        for thread in self.threads:
            self.client.setDefaultThread(thread_id=thread['id'], thread_type=thread['type'])
            self.client.changeThreadColor(ThreadColor.BRILLIANT_ROSE)
            self.client.changeThreadColor(ThreadColor.MESSENGER_BLUE)

    def test_reactToMessage(self):
        for thread in self.threads:
            mid = self.client.send(Message(text='test_reactToMessage★'), thread_id=thread['id'], thread_type=thread['type'])
            self.client.reactToMessage(mid, MessageReaction.LOVE)

    def test_setTypingStatus(self):
        for thread in self.threads:
            self.client.setDefaultThread(thread_id=thread['id'], thread_type=thread['type'])
            self.client.setTypingStatus(TypingStatus.TYPING)
            self.client.setTypingStatus(TypingStatus.STOPPED)


'''
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
        self.user_id = j['user_thread_id']
        self.group_id = j['group_thread_id']
        session = j.get('session')
    except (IOError, IndexError) as e:
        email = input('Email: ')
        password = getpass()
        self.group_id = input('Please enter a group thread id (To test group functionality): ')
        self.user_id = input('Please enter a user thread id (To test kicking/adding functionality): ')

    print('Logging in...')
    self.client = CustomClient(email, password, logging_level=logging_level, session_cookies=session)

    # Warning! Taking user input directly like this could be dangerous! Use only for testing purposes!
    start_test(self.client, self.group_id, self.user_id, self.threads, argv[1:])

    with open(path.join(path.dirname(__file__), 'tests/my_data.json'), 'w') as f:
        session = None
        try:
            session = self.client.getSession()
        except Exception:
            print('Unable to fetch self.client session!')
        json.dump({
            'email': email,
            'password': password,
            'user_thread_id': self.user_id,
            'group_thread_id': self.group_id,
            'session': session
        }, f)
'''
