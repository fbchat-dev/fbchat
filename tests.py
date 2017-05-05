#!/usr/bin/env python

import logging
import fbchat
import getpass
import unittest
import sys
from os import path

# Disable logging
logging.basicConfig(level=100)
fbchat.log.setLevel(100)

"""

Tests for fbchat
~~~~~~~~~~~~~~~~

To use these tests, put:
- email
- password
- a group_uid
- a user_uid (the user will be kicked from the group and then added again)
(seperated these by a newline) in a file called `tests.data`, or type them manually in the terminal prompts

Please remember to test both python v. 2.7 and python v. 3.6!

If you've made any changes to the 2FA functionality, test it with a 2FA enabled account
If you only want to execute specific tests, pass the function names in the commandline

"""

class TestFbchat(unittest.TestCase):
    def test_login_functions(self):
        self.assertTrue(client.is_logged_in())
        
        client.logout()
        
        self.assertFalse(client.is_logged_in())
        
        with self.assertRaises(Exception):
            client.login("not@email.com", "not_password", max_retries=1)
        
        client.login(email, password)
        
        self.assertTrue(client.is_logged_in())

    def test_sessions(self):
        global client
        session_cookies = client.getSession()
        client = fbchat.Client(email, password, session_cookies=session_cookies)
        
        self.assertTrue(client.is_logged_in())

    def test_setDefaultRecipient(self):
        client.setDefaultRecipient(client.uid, is_user=True)
        self.assertTrue(client.send(message="test_default_recipient"))

    def test_getAllUsers(self):
        users = client.getAllUsers()
        self.assertGreater(len(users), 0)

    def test_getUsers(self):
        users = client.getUsers("Mark Zuckerberg")
        self.assertGreater(len(users), 0)
        
        u = users[0]
        
        # Test if values are set correctly
        self.assertIsInstance(u.uid, int)
        self.assertEquals(u.type, 'user')
        self.assertEquals(u.photo[:4], 'http')
        self.assertEquals(u.url[:4], 'http')
        self.assertEquals(u.name, 'Mark Zuckerberg')
        self.assertGreater(u.score, 0)
    
    def test_send_likes(self):
        self.assertTrue(client.send(client.uid, like='s'))
        self.assertTrue(client.send(client.uid, like='m'))
        self.assertTrue(client.send(client.uid, like='l'))
        self.assertTrue(client.send(group_uid, like='s', is_user=False))
        self.assertTrue(client.send(group_uid, like='m', is_user=False))
        self.assertTrue(client.send(group_uid, like='l', is_user=False))
    
    def test_send(self):
        self.assertTrue(client.send(client.uid, message='test_send_user'))
        self.assertTrue(client.send(group_uid, message='test_send_group', is_user=False))
    
    def test_send_images(self):
        image_url = 'https://cdn4.iconfinder.com/data/icons/ionicons/512/icon-image-128.png'
        image_local_url = path.join(path.dirname(__file__), 'test_image.png')
        self.assertTrue(client.sendRemoteImage(client.uid, message='test_send_user_images_remote', image=image_url))
        self.assertTrue(client.sendLocalImage(client.uid, message='test_send_user_images_local', image=image_local_url))
        self.assertTrue(client.sendRemoteImage(group_uid, message='test_send_group_images_remote', is_user=False, image=image_url))
        self.assertTrue(client.sendLocalImage(group_uid, message='test_send_group_images_local', is_user=False, image=image_local_url))
    
    def test_getThreadInfo(self):
        info = client.getThreadInfo(client.uid, last_n=1)
        self.assertEquals(info[0].author, 'fbid:' + str(client.uid))
        client.send(group_uid, message='test_getThreadInfo', is_user=False)
        info = client.getThreadInfo(group_uid, last_n=1, is_user=False)
        self.assertEquals(info[0].author, 'fbid:' + str(client.uid))
        self.assertEquals(info[0].body, 'test_getThreadInfo')

    def test_markAs(self):
        # To be implemented (requires some form of manual watching)
        pass

    def test_listen(self):
        client.do_one_listen()

    def test_getUserInfo(self):
        info = client.getUserInfo(4)
        self.assertEquals(info['name'], 'Mark Zuckerberg')
    
    def test_remove_add_from_chat(self):
        self.assertTrue(client.remove_user_from_chat(group_uid, user_uid))
        self.assertTrue(client.add_users_to_chat(group_uid, user_uid))
    
    def test_changeThreadTitle(self):
        self.assertTrue(client.changeThreadTitle(group_uid, 'test_changeThreadTitle'))


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
    print ('Starting test(s)')
    unittest.TextTestRunner(verbosity=2).run(suite)



if __name__ == '__main__':
    # Python 3 does not use raw_input, whereas Python 2 does
    try:
        input = raw_input
    except Exception as e:
        pass

    try:
        with open(path.join(path.dirname(__file__), 'tests.data'), 'r') as f:
            content = f.readlines()
        content = [x.strip() for x in content if len(x.strip()) != 0]
        email = content[0]
        password = content[1]
        group_uid = content[2]
        user_uid = content[3]
    except (IOError, IndexError) as e:
        email = input('Email: ')
        password = getpass.getpass()
        group_uid = input('Please enter a group uid (To test group functionality): ')
        user_uid = input('Please enter a user uid (To test kicking/adding functionality): ')

    print ('Logging in')
    client = fbchat.Client(email, password)
    
    # Warning! Taking user input directly like this could be dangerous! Use only for testing purposes!
    start_test(client, group_uid, user_uid, sys.argv[1:])

