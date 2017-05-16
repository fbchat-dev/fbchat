#!/usr/bin/env python

import time
import json
import logging
import fbchat
from fbchat.models import *
import getpass
import unittest
import sys
from os import path

#Setup logging
logging.basicConfig(level=logging.INFO)

"""

Tests for fbchat
~~~~~~~~~~~~~~~~

To use these tests copy test_data.json to my_test_data.json or type this information manually in the terminal prompts.

- email: Your (or a test user's) email / phone number
- password: Your (or a test user's) password
- group_thread_id: A test group that will be used to test group functionality
- user_thread_id: A person that will be used to test kick/add functionality (This user should be in the group)

Please remember to test both python v. 2.7 and python v. 3.6!

If you've made any changes to the 2FA functionality, test it with a 2FA enabled account
If you only want to execute specific tests, pass the function names in the commandline

"""

class TestFbchat(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        time.sleep(3)

    def test_loginFunctions(self):
        self.assertTrue(client.isLoggedIn())

        client.logout()

        self.assertFalse(client.isLoggedIn())

        with self.assertRaises(Exception):
            client.login("not@email.com", "not_password", max_retries=1)

        client.login(email, password)

        self.assertTrue(client.isLoggedIn())

    def test_sessions(self):
        global client
        session_cookies = client.getSession()
        client = fbchat.Client(email, password, session_cookies=session_cookies)

        self.assertTrue(client.isLoggedIn())

    def test_setDefaultThreadId(self):
        client.setDefaultThread(client.uid, ThreadType.USER)
        self.assertTrue(client.sendMessage("test_default_recipient"))

    def test_resetDefaultThreadId(self):
        client.resetDefaultThread()
        self.assertRaises(ValueError, client.sendMessage("should_not_send"))

    def test_getAllUsers(self):
        users = client.getAllUsers()
        self.assertGreater(len(users), 0)

    def test_getUsers(self):
        users = client.getUsers("Mark Zuckerberg")
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
        self.assertTrue(client.sendEmoji("😆", EmojiSize.LARGE, user_uid, ThreadType.USER))

        self.assertTrue(client.sendEmoji(size=EmojiSize.SMALL, thread_id=group_uid, thread_type=ThreadType.GROUP))
        self.assertTrue(client.sendEmoji(size=EmojiSize.MEDIUM, thread_id=group_uid, thread_type=ThreadType.GROUP))
        self.assertTrue(client.sendEmoji("😆", EmojiSize.LARGE, group_uid, ThreadType.GROUP))

    def test_sendMessage(self):
        self.assertTrue(client.sendMessage('test_send_user', user_uid, ThreadType.USER))
        self.assertTrue(client.sendMessage('test_send_group', group_uid, ThreadType.GROUP))

    def test_sendImages(self):
        image_url = 'https://cdn4.iconfinder.com/data/icons/ionicons/512/icon-image-128.png'
        image_local_url = path.join(path.dirname(__file__), 'test_image.png')
        self.assertTrue(client.sendRemoteImage(image_url, 'test_send_user_images_remote', user_uid, ThreadType.USER))
        self.assertTrue(client.sendRemoteImage(image_url, 'test_send_group_images_remote', group_uid, ThreadType.GROUP))
        # Idk why but doesnt work, payload is null
        self.assertTrue(client.sendLocalImage(image_local_url, 'test_send_group_images_local', user_uid, ThreadType.USER))
        self.assertTrue(client.sendLocalImage(image_local_url, 'test_send_group_images_local', group_uid, ThreadType.GROUP))

    def test_getThreadInfo(self):
        client.sendMessage('test_user_getThreadInfo', user_uid, ThreadType.USER)
        time.sleep(3)
        info = client.getThreadInfo(20, user_uid, ThreadType.USER)
        self.assertEqual(info[0].author, 'fbid:' + client.uid)
        self.assertEqual(info[0].body, 'test_user_getThreadInfo')

        client.sendMessage('test_group_getThreadInfo', group_uid, ThreadType.GROUP)
        time.sleep(3)
        info = client.getThreadInfo(20, group_uid, ThreadType.GROUP)
        self.assertEquals(info[0].author, 'fbid:' + client.uid)
        self.assertEquals(info[0].body, 'test_group_getThreadInfo')

    def test_markAs(self):
        # To be implemented (requires some form of manual watching)
        pass

    def test_listen(self):
        client.doOneListen()

    def test_getUserInfo(self):
        info = client.getUserInfo(4)
        self.assertEquals(info['name'], 'Mark Zuckerberg')

    def test_removeAddFromChat(self):
        self.assertTrue(client.removeUserFromChat(user_uid, group_uid))
        self.assertTrue(client.addUsersToChat([user_uid], group_uid))

    def test_changeThreadTitle(self):
        self.assertTrue(client.changeThreadTitle('test_changeThreadTitle', group_uid))

    def test_changeThreadColor(self):
        self.assertTrue(client.changeThreadColor(ChatColor.BRILLIANT_ROSE, group_uid))
        client.sendMessage(ChatColor.BRILLIANT_ROSE.name, group_uid, ThreadType.GROUP)

        time.sleep(1)

        self.assertTrue(client.changeThreadColor(ChatColor.MESSENGER_BLUE, group_uid))
        client.sendMessage(ChatColor.MESSENGER_BLUE.name, group_uid, ThreadType.GROUP)

        time.sleep(2)

        self.assertTrue(client.changeThreadColor(ChatColor.BRILLIANT_ROSE, user_uid))
        client.sendMessage(ChatColor.BRILLIANT_ROSE.name, user_uid, ThreadType.USER)

        time.sleep(1)

        self.assertTrue(client.changeThreadColor(ChatColor.MESSENGER_BLUE, user_uid))
        client.sendMessage(ChatColor.MESSENGER_BLUE.name, user_uid, ThreadType.USER)


def start_test(param_client, param_group_uid, param_user_uid, tests=[]):
    global client
    global group_uid
    global user_uid

    client = param_client
    group_uid = param_group_uid
    user_uid = param_user_uid

    if len(tests) == 0:
        suite = unittest.TestLoader().loadTestsFromTestCase(TestFbchat)
    else:
        suite = unittest.TestSuite(map(TestFbchat, tests))
    print('Starting test(s)')
    unittest.TextTestRunner(verbosity=2).run(suite)


client = None

if __name__ == 'tests':
    # Python 3 does not use raw_input, whereas Python 2 does
    try:
        input = raw_input
    except Exception as e:
        pass

    try:
        with open(path.join(path.dirname(__file__), 'my_test_data.json'), 'r') as f:
            json = json.load(f)
        email = json['email']
        password = json['password']
        user_uid = json['user_thread_id']
        group_uid = json['group_thread_id']
    except (IOError, IndexError) as e:
        email = input('Email: ')
        password = getpass.getpass()
        group_uid = input('Please enter a group thread id (To test group functionality): ')
        user_uid = input('Please enter a user thread id (To test kicking/adding functionality): ')

    print('Logging in...')
    client = fbchat.Client(email, password)
    
    # Warning! Taking user input directly like this could be dangerous! Use only for testing purposes!
    start_test(client, group_uid, user_uid, sys.argv[1:])

