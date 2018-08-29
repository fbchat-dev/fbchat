# -*- coding: UTF-8 -*-

from __future__ import unicode_literals
import requests
import urllib
from uuid import uuid1
from random import choice
from bs4 import BeautifulSoup as bs
from mimetypes import guess_type
from collections import OrderedDict
from .utils import *
from .models import *
from .graphql import *
import time
import json
try:
    from urllib.parse import urlparse, parse_qs
except ImportError:
    from urlparse import urlparse, parse_qs


class Client(object):
    """A client for the Facebook Chat (Messenger).

    See https://fbchat.readthedocs.io for complete documentation of the API.
    """

    ssl_verify = True
    """Verify ssl certificate, set to False to allow debugging with a proxy"""
    listening = False
    """Whether the client is listening. Used when creating an external event loop to determine when to stop listening"""
    uid = None
    """
    The ID of the client.
    Can be used as `thread_id`. See :ref:`intro_threads` for more info.

    Note: Modifying this results in undefined behaviour
    """

    def __init__(self, email, password, user_agent=None, max_tries=5, session_cookies=None, logging_level=logging.INFO):
        """Initializes and logs in the client

        :param email: Facebook `email`, `id` or `phone number`
        :param password: Facebook account password
        :param user_agent: Custom user agent to use when sending requests. If `None`, user agent will be chosen from a premade list (see :any:`utils.USER_AGENTS`)
        :param max_tries: Maximum number of times to try logging in
        :param session_cookies: Cookies from a previous session (Will default to login if these are invalid)
        :param logging_level: Configures the `logging level <https://docs.python.org/3/library/logging.html#logging-levels>`_. Defaults to `INFO`
        :type max_tries: int
        :type session_cookies: dict
        :type logging_level: int
        :raises: FBchatException on failed login
        """

        self.sticky, self.pool = (None, None)
        self._session = requests.session()
        self.req_counter = 1
        self.seq = "0"
        # See `createPoll` for the reason for using `OrderedDict` here
        self.payloadDefault = OrderedDict()
        self.client = 'mercury'
        self.default_thread_id = None
        self.default_thread_type = None
        self.req_url = ReqUrl()

        if not user_agent:
            user_agent = choice(USER_AGENTS)

        self._header = {
            'Content-Type' : 'application/x-www-form-urlencoded',
            'Referer' : self.req_url.BASE,
            'Origin' : self.req_url.BASE,
            'User-Agent' : user_agent,
            'Connection' : 'keep-alive',
        }

        handler.setLevel(logging_level)

        # If session cookies aren't set, not properly loaded or gives us an invalid session, then do the login
        if not session_cookies or not self.setSession(session_cookies) or not self.isLoggedIn():
            self.login(email, password, max_tries)
        else:
            self.email = email
            self.password = password

    """
    INTERNAL REQUEST METHODS
    """

    def _generatePayload(self, query):
        """Adds the following defaults to the payload:
          __rev, __user, __a, ttstamp, fb_dtsg, __req
        """
        payload = self.payloadDefault.copy()
        if query:
            payload.update(query)
        payload['__req'] = str_base(self.req_counter, 36)
        payload['seq'] = self.seq
        self.req_counter += 1
        return payload

    def _fix_fb_errors(self, error_code):
        """
        This fixes "Please try closing and re-opening your browser window" errors (1357004)
        This error usually happens after 1-2 days of inactivity
        It may be a bad idea to do this in an exception handler, if you have a better method, please suggest it!
        """
        if error_code == '1357004':
            log.warning('Got error #1357004. Doing a _postLogin, and resending request')
            self._postLogin()
            return True
        return False

    def _get(self, url, query=None, timeout=30, fix_request=False, as_json=False, error_retries=3):
        payload = self._generatePayload(query)
        r = self._session.get(url, headers=self._header, params=payload, timeout=timeout, verify=self.ssl_verify)
        if not fix_request:
            return r
        try:
            return check_request(r, as_json=as_json)
        except FBchatFacebookError as e:
            if error_retries > 0 and self._fix_fb_errors(e.fb_error_code):
                return self._get(url, query=query, timeout=timeout, fix_request=fix_request, as_json=as_json, error_retries=error_retries-1)
            raise e

    def _post(self, url, query=None, timeout=30, fix_request=False, as_json=False, error_retries=3):
        payload = self._generatePayload(query)
        r = self._session.post(url, headers=self._header, data=payload, timeout=timeout, verify=self.ssl_verify)
        if not fix_request:
            return r
        try:
            return check_request(r, as_json=as_json)
        except FBchatFacebookError as e:
            if error_retries > 0 and self._fix_fb_errors(e.fb_error_code):
                return self._post(url, query=query, timeout=timeout, fix_request=fix_request, as_json=as_json, error_retries=error_retries-1)
            raise e

    def _graphql(self, payload, error_retries=3):
        content = self._post(self.req_url.GRAPHQL, payload, fix_request=True, as_json=False)
        try:
            return graphql_response_to_json(content)
        except FBchatFacebookError as e:
            if error_retries > 0 and self._fix_fb_errors(e.fb_error_code):
                return self._graphql(payload, error_retries=error_retries-1)
            raise e

    def _cleanGet(self, url, query=None, timeout=30, allow_redirects=True):
        return self._session.get(url, headers=self._header, params=query, timeout=timeout, verify=self.ssl_verify,
                                 allow_redirects=allow_redirects)

    def _cleanPost(self, url, query=None, timeout=30):
        self.req_counter += 1
        return self._session.post(url, headers=self._header, data=query, timeout=timeout, verify=self.ssl_verify)

    def _postFile(self, url, files=None, query=None, timeout=30, fix_request=False, as_json=False, error_retries=3):
        payload=self._generatePayload(query)
        # Removes 'Content-Type' from the header
        headers = dict((i, self._header[i]) for i in self._header if i != 'Content-Type')
        r = self._session.post(url, headers=headers, data=payload, timeout=timeout, files=files, verify=self.ssl_verify)
        if not fix_request:
            return r
        try:
            return check_request(r, as_json=as_json)
        except FBchatFacebookError as e:
            if error_retries > 0 and self._fix_fb_errors(e.fb_error_code):
                return self._postFile(url, files=files, query=query, timeout=timeout, fix_request=fix_request, as_json=as_json, error_retries=error_retries-1)
            raise e

    def graphql_requests(self, *queries):
        """
        .. todo::
            Documenting this

        :raises: FBchatException if request failed
        """

        return tuple(self._graphql({
            'method': 'GET',
            'response_format': 'json',
            'queries': graphql_queries_to_json(*queries)
        }))

    def graphql_request(self, query):
        """
        Shorthand for `graphql_requests(query)[0]`

        :raises: FBchatException if request failed
        """
        return self.graphql_requests(query)[0]

    """
    END INTERNAL REQUEST METHODS
    """

    """
    LOGIN METHODS
    """

    def _resetValues(self):
        self.payloadDefault = OrderedDict()
        self._session = requests.session()
        self.req_counter = 1
        self.seq = "0"
        self.uid = None

    def _postLogin(self):
        self.payloadDefault = OrderedDict()
        self.client_id = hex(int(random()*2147483648))[2:]
        self.start_time = now()
        self.uid = self._session.cookies.get_dict().get('c_user')
        if self.uid is None:
            raise FBchatException('Could not find c_user cookie')
        self.uid = str(self.uid)
        self.user_channel = "p_" + self.uid
        self.ttstamp = ''

        r = self._get(self.req_url.BASE)
        soup = bs(r.text, "html.parser")

        fb_dtsg_element = soup.find("input", {'name': 'fb_dtsg'})
        if fb_dtsg_element:
            self.fb_dtsg = fb_dtsg_element['value']
        else:
            self.fb_dtsg = re.search(r'name="fb_dtsg" value="(.*?)"', r.text).group(1)


        fb_h_element = soup.find("input", {'name':'h'})
        if fb_h_element:
            self.fb_h = fb_h_element['value']

        for i in self.fb_dtsg:
            self.ttstamp += str(ord(i))
        self.ttstamp += '2'
        # Set default payload
        self.payloadDefault['__rev'] = int(r.text.split('"client_revision":',1)[1].split(",",1)[0])
        self.payloadDefault['__user'] = self.uid
        self.payloadDefault['__a'] = '1'
        self.payloadDefault['ttstamp'] = self.ttstamp
        self.payloadDefault['fb_dtsg'] = self.fb_dtsg

        self.form = {
            'channel' : self.user_channel,
            'partition' : '-2',
            'clientid' : self.client_id,
            'viewer_uid' : self.uid,
            'uid' : self.uid,
            'state' : 'active',
            'format' : 'json',
            'idle' : 0,
            'cap' : '8'
        }

        self.prev = now()
        self.tmp_prev = now()
        self.last_sync = now()

    def _login(self):
        if not (self.email and self.password):
            raise FBchatUserError("Email and password not found.")

        soup = bs(self._get(self.req_url.MOBILE).text, "html.parser")
        data = dict((elem['name'], elem['value']) for elem in soup.findAll("input") if elem.has_attr('value') and elem.has_attr('name'))
        data['email'] = self.email
        data['pass'] = self.password
        data['login'] = 'Log In'

        r = self._cleanPost(self.req_url.LOGIN, data)

        # Usually, 'Checkpoint' will refer to 2FA
        if ('checkpoint' in r.url
            and ('id="approvals_code"' in r.text.lower())):
            r = self._2FA(r)

        # Sometimes Facebook tries to show the user a "Save Device" dialog
        if 'save-device' in r.url:
            r = self._cleanGet(self.req_url.SAVE_DEVICE)

        if 'home' in r.url:
            self._postLogin()
            return True, r.url
        else:
            return False, r.url

    def _2FA(self, r):
        soup = bs(r.text, "html.parser")
        data = dict()

        s = self.on2FACode()

        data['approvals_code'] = s
        data['fb_dtsg'] = soup.find("input", {'name':'fb_dtsg'})['value']
        data['nh'] = soup.find("input", {'name':'nh'})['value']
        data['submit[Submit Code]'] = 'Submit Code'
        data['codes_submitted'] = 0
        log.info('Submitting 2FA code.')

        r = self._cleanPost(self.req_url.CHECKPOINT, data)

        if 'home' in r.url:
            return r

        del(data['approvals_code'])
        del(data['submit[Submit Code]'])
        del(data['codes_submitted'])

        data['name_action_selected'] = 'save_device'
        data['submit[Continue]'] = 'Continue'
        log.info('Saving browser.')  # At this stage, we have dtsg, nh, name_action_selected, submit[Continue]
        r = self._cleanPost(self.req_url.CHECKPOINT, data)

        if 'home' in r.url:
            return r

        del(data['name_action_selected'])
        log.info('Starting Facebook checkup flow.')  # At this stage, we have dtsg, nh, submit[Continue]
        r = self._cleanPost(self.req_url.CHECKPOINT, data)

        if 'home' in r.url:
            return r

        del(data['submit[Continue]'])
        data['submit[This was me]'] = 'This Was Me'
        log.info('Verifying login attempt.')  # At this stage, we have dtsg, nh, submit[This was me]
        r = self._cleanPost(self.req_url.CHECKPOINT, data)

        if 'home' in r.url:
            return r

        del(data['submit[This was me]'])
        data['submit[Continue]'] = 'Continue'
        data['name_action_selected'] = 'save_device'
        log.info('Saving device again.')  # At this stage, we have dtsg, nh, submit[Continue], name_action_selected
        r = self._cleanPost(self.req_url.CHECKPOINT, data)
        return r

    def isLoggedIn(self):
        """
        Sends a request to Facebook to check the login status

        :return: True if the client is still logged in
        :rtype: bool
        """
        # Send a request to the login url, to see if we're directed to the home page
        r = self._cleanGet(self.req_url.LOGIN, allow_redirects=False)
        return 'Location' in r.headers and 'home' in r.headers['Location']

    def getSession(self):
        """Retrieves session cookies

        :return: A dictionay containing session cookies
        :rtype: dict
        """
        return self._session.cookies.get_dict()

    def setSession(self, session_cookies):
        """Loads session cookies

        :param session_cookies: A dictionay containing session cookies
        :type session_cookies: dict
        :return: False if `session_cookies` does not contain proper cookies
        :rtype: bool
        """

        # Quick check to see if session_cookies is formatted properly
        if not session_cookies or 'c_user' not in session_cookies:
            return False

        try:
            # Load cookies into current session
            self._session.cookies = requests.cookies.merge_cookies(self._session.cookies, session_cookies)
            self._postLogin()
        except Exception as e:
            log.exception('Failed loading session')
            self._resetValues()
            return False
        return True

    def login(self, email, password, max_tries=5):
        """
        Uses `email` and `password` to login the user (If the user is already logged in, this will do a re-login)

        :param email: Facebook `email` or `id` or `phone number`
        :param password: Facebook account password
        :param max_tries: Maximum number of times to try logging in
        :type max_tries: int
        :raises: FBchatException on failed login
        """
        self.onLoggingIn(email=email)

        if max_tries < 1:
            raise FBchatUserError('Cannot login: max_tries should be at least one')

        if not (email and password):
            raise FBchatUserError('Email and password not set')

        self.email = email
        self.password = password

        for i in range(1, max_tries+1):
            login_successful, login_url = self._login()
            if not login_successful:
                log.warning('Attempt #{} failed{}'.format(i, {True:', retrying'}.get(i < max_tries, '')))
                time.sleep(1)
                continue
            else:
                self.onLoggedIn(email=email)
                break
        else:
            raise FBchatUserError('Login failed. Check email/password. (Failed on url: {})'.format(login_url))

    def logout(self):
        """
        Safely logs out the client

        :param timeout: See `requests timeout <http://docs.python-requests.org/en/master/user/advanced/#timeouts>`_
        :return: True if the action was successful
        :rtype: bool
        """

        if not hasattr(self, 'fb_h'):
            h_r = self._post(self.req_url.MODERN_SETTINGS_MENU, {'pmid': '4'})
            self.fb_h = re.search(r'name=\\"h\\" value=\\"(.*?)\\"', h_r.text).group(1)

        data = {
            'ref': "mb",
            'h': self.fb_h
        }

        r = self._get(self.req_url.LOGOUT, data)

        self._resetValues()

        return r.ok

    """
    END LOGIN METHODS
    """

    """
    DEFAULT THREAD METHODS
    """

    def _getThread(self, given_thread_id=None, given_thread_type=None):
        """
        Checks if thread ID is given, checks if default is set and returns correct values

        :raises ValueError: If thread ID is not given and there is no default
        :return: Thread ID and thread type
        :rtype: tuple
        """
        if given_thread_id is None:
            if self.default_thread_id is not None:
                return self.default_thread_id, self.default_thread_type
            else:
                raise ValueError('Thread ID is not set')
        else:
            return given_thread_id, given_thread_type

    def setDefaultThread(self, thread_id, thread_type):
        """Sets default thread to send messages to

        :param thread_id: User/Group ID to default to. See :ref:`intro_threads`
        :param thread_type: See :ref:`intro_threads`
        :type thread_type: models.ThreadType
        """
        self.default_thread_id = thread_id
        self.default_thread_type = thread_type

    def resetDefaultThread(self):
        """Resets default thread"""
        self.setDefaultThread(None, None)

    """
    END DEFAULT THREAD METHODS
    """

    """
    FETCH METHODS
    """

    def _forcedFetch(self, thread_id, mid):
        j = self.graphql_request(GraphQL(doc_id='1768656253222505', params={
            'thread_and_message_id': {
                'thread_id': thread_id,
                'message_id': mid
            }
        }))
        return j

    def fetchAllUsers(self):
        """
        Gets all users the client is currently chatting with

        :return: :class:`models.User` objects
        :rtype: list
        :raises: FBchatException if request failed
        """

        data = {
            'viewer': self.uid,
        }
        j = self._post(self.req_url.ALL_USERS, query=data, fix_request=True, as_json=True)
        if j.get('payload') is None:
            raise FBchatException('Missing payload while fetching users: {}'.format(j))

        users = []

        for key in j['payload']:
            k = j['payload'][key]
            if k['type'] in ['user', 'friend']:
                if k['id'] in ['0', 0]:
                    # Skip invalid users
                    pass
                users.append(User(k['id'], first_name=k.get('firstName'), url=k.get('uri'), photo=k.get('thumbSrc'), name=k.get('name'), is_friend=k.get('is_friend'), gender=GENDERS.get(k.get('gender'))))

        return users

    def searchForUsers(self, name, limit=1):
        """
        Find and get user by his/her name

        :param name: Name of the user
        :param limit: The max. amount of users to fetch
        :return: :class:`models.User` objects, ordered by relevance
        :rtype: list
        :raises: FBchatException if request failed
        """

        j = self.graphql_request(GraphQL(query=GraphQL.SEARCH_USER, params={'search': name, 'limit': limit}))

        return [graphql_to_user(node) for node in j[name]['users']['nodes']]

    def searchForPages(self, name, limit=1):
        """
        Find and get page by its name

        :param name: Name of the page
        :return: :class:`models.Page` objects, ordered by relevance
        :rtype: list
        :raises: FBchatException if request failed
        """

        j = self.graphql_request(GraphQL(query=GraphQL.SEARCH_PAGE, params={'search': name, 'limit': limit}))

        return [graphql_to_page(node) for node in j[name]['pages']['nodes']]

    # TODO intergrate Rooms
    def searchForGroups(self, name, limit=1):
        """
        Find and get group thread by its name

        :param name: Name of the group thread
        :param limit: The max. amount of groups to fetch
        :return: :class:`models.Group` objects, ordered by relevance
        :rtype: list
        :raises: FBchatException if request failed
        """

        j = self.graphql_request(GraphQL(query=GraphQL.SEARCH_GROUP, params={'search': name, 'limit': limit}))

        return [graphql_to_group(node) for node in j['viewer']['groups']['nodes']]

    def searchForThreads(self, name, limit=1):
        """
        Find and get a thread by its name

        :param name: Name of the thread
        :param limit: The max. amount of groups to fetch
        :return: :class:`models.User`, :class:`models.Group` and :class:`models.Page` objects, ordered by relevance
        :rtype: list
        :raises: FBchatException if request failed
        """

        j = self.graphql_request(GraphQL(query=GraphQL.SEARCH_THREAD, params={'search': name, 'limit': limit}))

        rtn = []
        for node in j[name]['threads']['nodes']:
            if node['__typename'] == 'User':
                rtn.append(graphql_to_user(node))
            elif node['__typename'] == 'MessageThread':
                # MessageThread => Group thread
                rtn.append(graphql_to_group(node))
            elif node['__typename'] == 'Page':
                rtn.append(graphql_to_page(node))
            elif node['__typename'] == 'Group':
                # We don't handle Facebook "Groups"
                pass
            # TODO Add Rooms
            else:
                log.warning('Unknown __typename: {} in {}'.format(repr(node['__typename']), node))

        return rtn

    def searchForMessageIDs(self, query, offset=0, limit=5, thread_id=None):
        """
        Find and get message IDs by query

        :param query: Text to search for
        :param offset: Number of messages to skip
        :param limit: Max. number of messages to retrieve
        :param thread_id: User/Group ID to search in. See :ref:`intro_threads`
        :type offset: int
        :type limit: int
        :return: Found Message IDs
        :rtype: generator
        :raises: FBchatException if request failed
        """
        thread_id, thread_type = self._getThread(thread_id, None)

        data = {
            "query": query,
            "snippetOffset": offset,
            "snippetLimit": limit,
            "identifier": "thread_fbid",
            "thread_fbid": thread_id,
        }
        j = self._post(self.req_url.SEARCH_MESSAGES, data, fix_request=True, as_json=True)

        result = j["payload"]["search_snippets"][query]
        snippets = result[thread_id]["snippets"] if result.get(thread_id) else []
        for snippet in snippets:
            yield snippet["message_id"]

    def searchForMessages(self, query, offset=0, limit=5, thread_id=None):
        """
        Find and get :class:`models.Message` objects by query

        .. warning::
            This method sends request for every found message ID.

        :param query: Text to search for
        :param offset: Number of messages to skip
        :param limit: Max. number of messages to retrieve
        :param thread_id: User/Group ID to search in. See :ref:`intro_threads`
        :type offset: int
        :type limit: int
        :return: Found :class:`models.Message` objects
        :rtype: generator
        :raises: FBchatException if request failed
        """
        message_ids = self.searchForMessageIDs(query, offset=offset, limit=limit, thread_id=thread_id)
        for mid in message_ids:
            yield self.fetchMessageInfo(mid, thread_id)

    def search(self, query, fetch_messages=False, thread_limit=5, message_limit=5):
        """
        Searches for messages in all threads

        :param query: Text to search for
        :param fetch_messages: Whether to fetch :class:`models.Message` objects or IDs only
        :param thread_limit: Max. number of threads to retrieve
        :param message_limit: Max. number of messages to retrieve
        :type thread_limit: int
        :type message_limit: int
        :return: Dictionary with thread IDs as keys and generators to get messages as values
        :rtype: generator
        :raises: FBchatException if request failed
        """
        data = {
            "query": query,
            "snippetLimit": thread_limit
        }
        j = self._post(self.req_url.SEARCH_MESSAGES, data, fix_request=True, as_json=True)

        result = j["payload"]["search_snippets"][query]

        if fetch_messages:
            return {thread_id: self.searchForMessages(query, limit=message_limit, thread_id=thread_id) for thread_id in result}
        else:
            return {thread_id: self.searchForMessageIDs(query, limit=message_limit, thread_id=thread_id) for thread_id in result}

    def _fetchInfo(self, *ids):
        data = {
            "ids[{}]".format(i): _id for i, _id in enumerate(ids)
        }
        j = self._post(self.req_url.INFO, data, fix_request=True, as_json=True)

        if j.get('payload') is None or j['payload'].get('profiles') is None:
            raise FBchatException('No users/pages returned: {}'.format(j))

        entries = {}
        for _id in j['payload']['profiles']:
            k = j['payload']['profiles'][_id]
            if k['type'] in ['user', 'friend']:
                entries[_id] = {
                    'id': _id,
                    'type': ThreadType.USER,
                    'url': k.get('uri'),
                    'first_name': k.get('firstName'),
                    'is_viewer_friend': k.get('is_friend'),
                    'gender': k.get('gender'),
                    'profile_picture': {'uri': k.get('thumbSrc')},
                    'name': k.get('name')
                }
            elif k['type'] == 'page':
                entries[_id] = {
                    'id': _id,
                    'type': ThreadType.PAGE,
                    'url': k.get('uri'),
                    'profile_picture': {'uri': k.get('thumbSrc')},
                    'name': k.get('name')
                }
            else:
                raise FBchatException('{} had an unknown thread type: {}'.format(_id, k))

        log.debug(entries)
        return entries

    def fetchUserInfo(self, *user_ids):
        """
        Get users' info from IDs, unordered

        .. warning::
            Sends two requests, to fetch all available info!

        :param user_ids: One or more user ID(s) to query
        :return: :class:`models.User` objects, labeled by their ID
        :rtype: dict
        :raises: FBchatException if request failed
        """

        threads = self.fetchThreadInfo(*user_ids)
        users = {}
        for k in threads:
            if threads[k].type == ThreadType.USER:
                users[k] = threads[k]
            else:
                raise FBchatUserError('Thread {} was not a user'.format(threads[k]))

        return users

    def fetchPageInfo(self, *page_ids):
        """
        Get pages' info from IDs, unordered

        .. warning::
            Sends two requests, to fetch all available info!

        :param page_ids: One or more page ID(s) to query
        :return: :class:`models.Page` objects, labeled by their ID
        :rtype: dict
        :raises: FBchatException if request failed
        """

        threads = self.fetchThreadInfo(*page_ids)
        pages = {}
        for k in threads:
            if threads[k].type == ThreadType.PAGE:
                pages[k] = threads[k]
            else:
                raise FBchatUserError('Thread {} was not a page'.format(threads[k]))

        return pages

    def fetchGroupInfo(self, *group_ids):
        """
        Get groups' info from IDs, unordered

        :param group_ids: One or more group ID(s) to query
        :return: :class:`models.Group` objects, labeled by their ID
        :rtype: dict
        :raises: FBchatException if request failed
        """

        threads = self.fetchThreadInfo(*group_ids)
        groups = {}
        for k in threads:
            if threads[k].type == ThreadType.GROUP:
                groups[k] = threads[k]
            else:
                raise FBchatUserError('Thread {} was not a group'.format(threads[k]))

        return groups

    def fetchThreadInfo(self, *thread_ids):
        """
        Get threads' info from IDs, unordered

        .. warning::
            Sends two requests if users or pages are present, to fetch all available info!

        :param thread_ids: One or more thread ID(s) to query
        :return: :class:`models.Thread` objects, labeled by their ID
        :rtype: dict
        :raises: FBchatException if request failed
        """

        queries = []
        for thread_id in thread_ids:
            queries.append(GraphQL(doc_id='2147762685294928', params={
                'id': thread_id,
                'message_limit': 0,
                'load_messages': False,
                'load_read_receipts': False,
                'before': None
            }))

        j = self.graphql_requests(*queries)

        for i, entry in enumerate(j):
            if entry.get('message_thread') is None:
                # If you don't have an existing thread with this person, attempt to retrieve user data anyways
                j[i]['message_thread'] = {
                    'thread_key': {
                        'other_user_id': thread_ids[i]
                    },
                    'thread_type': 'ONE_TO_ONE'
                }

        pages_and_user_ids = [k['message_thread']['thread_key']['other_user_id'] for k in j if k['message_thread'].get('thread_type') == 'ONE_TO_ONE']
        pages_and_users = {}
        if len(pages_and_user_ids) != 0:
            pages_and_users = self._fetchInfo(*pages_and_user_ids)

        rtn = {}
        for i, entry in enumerate(j):
            entry = entry['message_thread']
            if entry.get('thread_type') == 'GROUP':
                _id = entry['thread_key']['thread_fbid']
                rtn[_id] = graphql_to_group(entry)
            elif entry.get('thread_type') == 'ROOM':
                _id = entry['thread_key']['thread_fbid']
                rtn[_id] = graphql_to_room(entry)
            elif entry.get('thread_type') == 'ONE_TO_ONE':
                _id = entry['thread_key']['other_user_id']
                if pages_and_users.get(_id) is None:
                    raise FBchatException('Could not fetch thread {}'.format(_id))
                entry.update(pages_and_users[_id])
                if entry['type'] == ThreadType.USER:
                    rtn[_id] = graphql_to_user(entry)
                else:
                    rtn[_id] = graphql_to_page(entry)
            else:
                raise FBchatException('{} had an unknown thread type: {}'.format(thread_ids[i], entry))

        return rtn

    def fetchThreadMessages(self, thread_id=None, limit=20, before=None):
        """
        Get the last messages in a thread

        :param thread_id: User/Group ID to get messages from. See :ref:`intro_threads`
        :param limit: Max. number of messages to retrieve
        :param before: A timestamp, indicating from which point to retrieve messages
        :type limit: int
        :type before: int
        :return: :class:`models.Message` objects
        :rtype: list
        :raises: FBchatException if request failed
        """

        thread_id, thread_type = self._getThread(thread_id, None)

        j = self.graphql_request(GraphQL(doc_id='1386147188135407', params={
            'id': thread_id,
            'message_limit': limit,
            'load_messages': True,
            'load_read_receipts': False,
            'before': before
        }))

        if j.get('message_thread') is None:
            raise FBchatException('Could not fetch thread {}: {}'.format(thread_id, j))

        return list(reversed([graphql_to_message(message) for message in j['message_thread']['messages']['nodes']]))

    def fetchThreadList(self, offset=None, limit=20, thread_location=ThreadLocation.INBOX, before=None):
        """Get thread list of your facebook account

        :param offset: Deprecated. Do not use!
        :param limit: Max. number of threads to retrieve. Capped at 20
        :param thread_location: models.ThreadLocation: INBOX, PENDING, ARCHIVED or OTHER
        :param before: A timestamp (in milliseconds), indicating from which point to retrieve threads
        :type limit: int
        :type before: int
        :return: :class:`models.Thread` objects
        :rtype: list
        :raises: FBchatException if request failed
        """

        if offset is not None:
            log.warning('Using `offset` in `fetchThreadList` is no longer supported, since Facebook migrated to the use of GraphQL in this request. Use `before` instead')

        if limit > 20 or limit < 1:
            raise FBchatUserError('`limit` should be between 1 and 20')

        if thread_location in ThreadLocation:
            loc_str = thread_location.value
        else:
            raise FBchatUserError('"thread_location" must be a value of ThreadLocation')

        j = self.graphql_request(GraphQL(doc_id='1349387578499440', params={
            'limit': limit,
            'tags': [loc_str],
            'before': before,
            'includeDeliveryReceipts': True,
            'includeSeqID': False
        }))

        return [graphql_to_thread(node) for node in j['viewer']['message_threads']['nodes']]

    def fetchUnread(self):
        """
        Get the unread thread list

        :return: List of unread thread ids
        :rtype: list
        :raises: FBchatException if request failed
        """
        form = {
            'folders[0]': 'inbox',
            'client': 'mercury',
            'last_action_timestamp': now() - 60*1000
            # 'last_action_timestamp': 0
        }

        j = self._post(self.req_url.UNREAD_THREADS, form, fix_request=True, as_json=True)

        return j['payload']['unread_thread_fbids'][0]['other_user_fbids']

    def fetchUnseen(self):
        """
        Get the unseen (new) thread list

        :return: List of unseen thread ids
        :rtype: list
        :raises: FBchatException if request failed
        """
        j = self._post(self.req_url.UNSEEN_THREADS, None, fix_request=True, as_json=True)

        return j['payload']['unseen_thread_fbids'][0]['other_user_fbids']

    def fetchImageUrl(self, image_id):
        """Fetches the url to the original image from an image attachment ID

        :param image_id: The image you want to fethc
        :type image_id: str
        :return: An url where you can download the original image
        :rtype: str
        :raises: FBChatException if request failed
        """
        image_id = str(image_id)
        j = check_request(self._get(ReqUrl.ATTACHMENT_PHOTO, query={'photo_id': str(image_id)}))

        url = get_jsmods_require(j, 3)
        if url is None:
            raise FBChatException('Could not fetch image url from: {}'.format(j))
        return url

    def fetchMessageInfo(self, mid, thread_id=None):
        """
        Fetches :class:`models.Message` object from the message id

        :param mid: Message ID to fetch from
        :param thread_id: User/Group ID to get message info from. See :ref:`intro_threads`
        :return: :class:`models.Message` object
        :rtype: models.Message
        :raises: FBChatException if request failed
        """
        thread_id, thread_type = self._getThread(thread_id, None)
        message_info = self._forcedFetch(thread_id, mid).get("message")
        message = graphql_to_message(message_info)
        return message

    def fetchPollOptions(self, poll_id):
        """
        Fetches list of :class:`models.PollOption` objects from the poll id

        :param poll_id: Poll ID to fetch from
        :rtype: list
        :raises: FBChatException if request failed
        """
        data = {
            "question_id": poll_id
        }

        j = self._post(self.req_url.GET_POLL_OPTIONS, data, fix_request=True, as_json=True)

        return [graphql_to_poll_option(m) for m in j["payload"]]

    def fetchPlanInfo(self, plan_id):
        """
        Fetches a :class:`models.Plan` object from the plan id

        :param plan_id: Plan ID to fetch from
        :return: :class:`models.Plan` object
        :rtype: models.Plan
        :raises: FBChatException if request failed
        """
        data = {
            "event_reminder_id": plan_id
        }
        j = self._post(self.req_url.PLAN_INFO, data, fix_request=True, as_json=True)
        plan = graphql_to_plan(j["payload"])
        return plan

    """
    END FETCH METHODS
    """

    """
    SEND METHODS
    """

    def _oldMessage(self, message):
        return message if isinstance(message, Message) else Message(text=message)

    def _getSendData(self, message=None, thread_id=None, thread_type=ThreadType.USER):
        """Returns the data needed to send a request to `SendURL`"""
        messageAndOTID = generateOfflineThreadingID()
        timestamp = now()
        data = {
            'client': self.client,
            'author' : 'fbid:' + str(self.uid),
            'timestamp' : timestamp,
            'source' : 'source:chat:web',
            'offline_threading_id': messageAndOTID,
            'message_id' : messageAndOTID,
            'threading_id': generateMessageID(self.client_id),
            'ephemeral_ttl_mode:': '0'
        }

        # Set recipient
        if thread_type in [ThreadType.USER, ThreadType.PAGE]:
            data['other_user_fbid'] = thread_id
        elif thread_type == ThreadType.GROUP:
            data['thread_fbid'] = thread_id

        if message is None:
            message = Message()

        if message.text or message.sticker or message.emoji_size:
            data['action_type'] = 'ma-type:user-generated-message'

        if message.text:
            data['body'] = message.text

        for i, mention in enumerate(message.mentions):
            data['profile_xmd[{}][id]'.format(i)] = mention.thread_id
            data['profile_xmd[{}][offset]'.format(i)] = mention.offset
            data['profile_xmd[{}][length]'.format(i)] = mention.length
            data['profile_xmd[{}][type]'.format(i)] = 'p'

        if message.emoji_size:
            if message.text:
                data['tags[0]'] = 'hot_emoji_size:' + message.emoji_size.name.lower()
            else:
                data['sticker_id'] = message.emoji_size.value

        if message.sticker:
            data['sticker_id'] = message.sticker.uid

        return data

    def _doSendRequest(self, data, get_thread_id=False):
        """Sends the data to `SendURL`, and returns the message ID or None on failure"""
        j = self._post(self.req_url.SEND, data, fix_request=True, as_json=True)

        # update JS token if received in response
        fb_dtsg = get_jsmods_require(j, 2)
        if fb_dtsg is not None:
            self.payloadDefault['fb_dtsg'] = fb_dtsg

        try:
            message_ids = [(action['message_id'], action['thread_fbid']) for action in j['payload']['actions'] if 'message_id' in action]
            if len(message_ids) != 1:
                log.warning("Got multiple message ids' back: {}".format(message_ids))
            if get_thread_id:
                return message_ids[0]
            else:
                return message_ids[0][0]
        except (KeyError, IndexError, TypeError) as e:
            raise FBchatException('Error when sending message: No message IDs could be found: {}'.format(j))

    def send(self, message, thread_id=None, thread_type=ThreadType.USER):
        """
        Sends a message to a thread

        :param message: Message to send
        :param thread_id: User/Group ID to send to. See :ref:`intro_threads`
        :param thread_type: See :ref:`intro_threads`
        :type message: models.Message
        :type thread_type: models.ThreadType
        :return: :ref:`Message ID <intro_message_ids>` of the sent message
        :raises: FBchatException if request failed
        """
        thread_id, thread_type = self._getThread(thread_id, thread_type)
        data = self._getSendData(message=message, thread_id=thread_id, thread_type=thread_type)

        return self._doSendRequest(data)

    def sendMessage(self, message, thread_id=None, thread_type=ThreadType.USER):
        """
        Deprecated. Use :func:`fbchat.Client.send` instead
        """
        return self.send(Message(text=message), thread_id=thread_id, thread_type=thread_type)

    def sendEmoji(self, emoji=None, size=EmojiSize.SMALL, thread_id=None, thread_type=ThreadType.USER):
        """
        Deprecated. Use :func:`fbchat.Client.send` instead
        """
        return self.send(Message(text=emoji, emoji_size=size), thread_id=thread_id, thread_type=thread_type)

    def wave(self, wave_first=True, thread_id=None, thread_type=None):
        """
        Says hello with a wave to a thread!

        :param wave_first: Whether to wave first or wave back
        :param thread_id: User/Group ID to send to. See :ref:`intro_threads`
        :param thread_type: See :ref:`intro_threads`
        :type thread_type: models.ThreadType
        :return: :ref:`Message ID <intro_message_ids>` of the sent message
        :raises: FBchatException if request failed
        """
        thread_id, thread_type = self._getThread(thread_id, thread_type)
        data = self._getSendData(thread_id=thread_id, thread_type=thread_type)
        data['action_type'] = 'ma-type:user-generated-message'
        data['lightweight_action_attachment[lwa_state]'] = "INITIATED" if wave_first else "RECIPROCATED"
        data['lightweight_action_attachment[lwa_type]'] = "WAVE"
        if thread_type == ThreadType.USER:
            data['specific_to_list[0]'] = "fbid:{}".format(thread_id)
        return self._doSendRequest(data)

    def _upload(self, files):
        """
        Uploads files to Facebook

        `files` should be a list of files that requests can upload, see:
        http://docs.python-requests.org/en/master/api/#requests.request

        Returns a list of tuples with a file's ID and mimetype
        """
        file_dict = {'upload_{}'.format(i): f for i, f in enumerate(files)}
        j = self._postFile(self.req_url.UPLOAD, files=file_dict, fix_request=True, as_json=True)

        if len(j['payload']['metadata']) != len(files):
            raise FBchatException("Some files could not be uploaded: {}, {}".format(j, files))

        return [(data[mimetype_to_key(data['filetype'])], data['filetype']) for data in j['payload']['metadata']]

    def _sendFiles(self, files, message=None, thread_id=None, thread_type=ThreadType.USER):
        """
        Sends files from file IDs to a thread

        `files` should be a list of tuples, with a file's ID and mimetype
        """
        thread_id, thread_type = self._getThread(thread_id, thread_type)
        data = self._getSendData(message=self._oldMessage(message), thread_id=thread_id, thread_type=thread_type)

        data['action_type'] = 'ma-type:user-generated-message'
        data['has_attachment'] = True

        for i, (file_id, mimetype) in enumerate(files):
            data['{}s[{}]'.format(mimetype_to_key(mimetype), i)] = file_id

        return self._doSendRequest(data)

    def sendRemoteFiles(self, file_urls, message=None, thread_id=None, thread_type=ThreadType.USER):
        """
        Sends files from URLs to a thread

        :param file_urls: URLs of files to upload and send
        :param message: Additional message
        :param thread_id: User/Group ID to send to. See :ref:`intro_threads`
        :param thread_type: See :ref:`intro_threads`
        :type thread_type: models.ThreadType
        :return: :ref:`Message ID <intro_message_ids>` of the sent files
        :raises: FBchatException if request failed
        """
        file_urls = require_list(file_urls)
        files = self._upload(get_files_from_urls(file_urls))
        return self._sendFiles(files=files, message=message, thread_id=thread_id, thread_type=thread_type)

    def sendLocalFiles(self, file_paths, message=None, thread_id=None, thread_type=ThreadType.USER):
        """
        Sends local files to a thread

        :param file_path: Paths of files to upload and send
        :param message: Additional message
        :param thread_id: User/Group ID to send to. See :ref:`intro_threads`
        :param thread_type: See :ref:`intro_threads`
        :type thread_type: models.ThreadType
        :return: :ref:`Message ID <intro_message_ids>` of the sent files
        :raises: FBchatException if request failed
        """
        file_paths = require_list(file_paths)
        with get_files_from_paths(file_paths) as x:
            files = self._upload(x)
        return self._sendFiles(files=files, message=message, thread_id=thread_id, thread_type=thread_type)

    def sendImage(self, image_id, message=None, thread_id=None, thread_type=ThreadType.USER, is_gif=False):
        """
        Deprecated. Use :func:`fbchat.Client._sendFiles` instead
        """
        if is_gif:
            return self._sendFiles(files=[(image_id, "image/png")], message=message, thread_id=thread_id, thread_type=thread_type)
        else:
            return self._sendFiles(files=[(image_id, "image/gif")], message=message, thread_id=thread_id, thread_type=thread_type)

    def sendRemoteImage(self, image_url, message=None, thread_id=None, thread_type=ThreadType.USER):
        """
        Deprecated. Use :func:`fbchat.Client.sendRemoteFiles` instead
        """
        return self.sendRemoteFiles(file_urls=[image_url], message=message, thread_id=thread_id, thread_type=thread_type)

    def sendLocalImage(self, image_path, message=None, thread_id=None, thread_type=ThreadType.USER):
        """
        Deprecated. Use :func:`fbchat.Client.sendLocalFiles` instead
        """
        return self.sendLocalFiles(file_paths=[image_path], message=message, thread_id=thread_id, thread_type=thread_type)

    def createGroup(self, message, user_ids):
        """
        Creates a group with the given ids

        :param message: The initial message
        :param user_ids: A list of users to create the group with.
        :return: ID of the new group
        :raises: FBchatException if request failed
        """
        data = self._getSendData(message=self._oldMessage(message))

        if len(user_ids) < 2:
            raise FBchatUserError("Error when creating group: Not enough participants")

        for i, user_id in enumerate(user_ids + [self.uid]):
            data['specific_to_list[{}]'.format(i)] = 'fbid:{}'.format(user_id)

        message_id, thread_id = self._doSendRequest(data, get_thread_id=True)
        if not thread_id:
            raise FBchatException("Error when creating group: No thread_id could be found")
        return thread_id

    def addUsersToGroup(self, user_ids, thread_id=None):
        """
        Adds users to a group.

        :param user_ids: One or more user IDs to add
        :param thread_id: Group ID to add people to. See :ref:`intro_threads`
        :type user_ids: list
        :raises: FBchatException if request failed
        """
        thread_id, thread_type = self._getThread(thread_id, None)
        data = self._getSendData(thread_id=thread_id, thread_type=ThreadType.GROUP)

        data['action_type'] = 'ma-type:log-message'
        data['log_message_type'] = 'log:subscribe'

        user_ids = require_list(user_ids)

        for i, user_id in enumerate(user_ids):
            if user_id == self.uid:
                raise FBchatUserError('Error when adding users: Cannot add self to group thread')
            else:
                data['log_message_data[added_participants][' + str(i) + ']'] = "fbid:" + str(user_id)

        return self._doSendRequest(data)

    def removeUserFromGroup(self, user_id, thread_id=None):
        """
        Removes users from a group.

        :param user_id: User ID to remove
        :param thread_id: Group ID to remove people from. See :ref:`intro_threads`
        :raises: FBchatException if request failed
        """

        thread_id, thread_type = self._getThread(thread_id, None)

        data = {
            "uid": user_id,
            "tid": thread_id
        }

        j = self._post(self.req_url.REMOVE_USER, data, fix_request=True, as_json=True)

    def _adminStatus(self, admin_ids, admin, thread_id=None):
        thread_id, thread_type = self._getThread(thread_id, None)

        data = {
            "add": admin,
            "thread_fbid": thread_id
        }

        admin_ids = require_list(admin_ids)

        for i, admin_id in enumerate(admin_ids):
            data['admin_ids[' + str(i) + ']'] = str(admin_id)

        j = self._post(self.req_url.SAVE_ADMINS, data, fix_request=True, as_json=True)

    def addGroupAdmins(self, admin_ids, thread_id=None):
        """
        Sets specifed users as group admins.

        :param admin_ids: One or more user IDs to set admin
        :param thread_id: Group ID to remove people from. See :ref:`intro_threads`
        :raises: FBchatException if request failed
        """
        self._adminStatus(admin_ids, True, thread_id)

    def removeGroupAdmins(self, admin_ids, thread_id=None):
        """
        Removes admin status from specifed users.

        :param admin_ids: One or more user IDs to remove admin
        :param thread_id: Group ID to remove people from. See :ref:`intro_threads`
        :raises: FBchatException if request failed
        """
        self._adminStatus(admin_ids, False, thread_id)

    def changeGroupApprovalMode(self, require_admin_approval, thread_id=None):
        """
        Changes group's approval mode

        :param require_admin_approval: True or False
        :param thread_id: Group ID to remove people from. See :ref:`intro_threads`
        :raises: FBchatException if request failed
        """
        thread_id, thread_type = self._getThread(thread_id, None)

        data = {
            "set_mode": int(require_admin_approval),
            "thread_fbid": thread_id
        }

        j = self._post(self.req_url.APPROVAL_MODE, data, fix_request=True, as_json=True)

    def _usersApproval(self, user_ids, approve, thread_id=None):
        thread_id, thread_type = self._getThread(thread_id, None)

        user_ids = list(require_list(user_ids))

        j = self.graphql_request(GraphQL(doc_id='1574519202665847', params={
            'data': {
                'client_mutation_id': '0',
                'actor_id': self.uid,
                'thread_fbid': thread_id,
                'user_ids': user_ids,
                'response': 'ACCEPT' if approve else 'DENY',
                'surface': 'ADMIN_MODEL_APPROVAL_CENTER'
            }
        }))

    def acceptUsersToGroup(self, user_ids, thread_id=None):
        """
        Accepts users to the group from the group's approval

        :param user_ids: One or more user IDs to accept
        :param thread_id: Group ID to accept users to. See :ref:`intro_threads`
        :raises: FBchatException if request failed
        """
        self._usersApproval(user_ids, True, thread_id)

    def denyUsersFromGroup(self, user_ids, thread_id=None):
        """
        Denies users from the group's approval

        :param user_ids: One or more user IDs to deny
        :param thread_id: Group ID to deny users from. See :ref:`intro_threads`
        :raises: FBchatException if request failed
        """
        self._usersApproval(user_ids, False, thread_id)

    def _changeGroupImage(self, image_id, thread_id=None):
        """
        Changes a thread image from an image id

        :param image_id: ID of uploaded image
        :param thread_id: User/Group ID to change image. See :ref:`intro_threads`
        :raises: FBchatException if request failed
        """

        thread_id, thread_type = self._getThread(thread_id, None)

        data = {
            'thread_image_id': image_id,
            'thread_id': thread_id
        }

        j = self._post(self.req_url.THREAD_IMAGE, data, fix_request=True, as_json=True)
        return image_id

    def changeGroupImageRemote(self, image_url, thread_id=None):
        """
        Changes a thread image from a URL

        :param image_url: URL of an image to upload and change
        :param thread_id: User/Group ID to change image. See :ref:`intro_threads`
        :raises: FBchatException if request failed
        """

        (image_id, mimetype), = self._upload(get_files_from_urls([image_url]))
        return self._changeGroupImage(image_id, thread_id)

    def changeGroupImageLocal(self, image_path, thread_id=None):
        """
        Changes a thread image from a local path

        :param image_path: Path of an image to upload and change
        :param thread_id: User/Group ID to change image. See :ref:`intro_threads`
        :raises: FBchatException if request failed
        """

        with get_files_from_paths([image_path]) as files:
            (image_id, mimetype), = self._upload(files)

        return self._changeGroupImage(image_id, thread_id)

    def changeThreadTitle(self, title, thread_id=None, thread_type=ThreadType.USER):
        """
        Changes title of a thread.
        If this is executed on a user thread, this will change the nickname of that user, effectively changing the title

        :param title: New group thread title
        :param thread_id: Group ID to change title of. See :ref:`intro_threads`
        :param thread_type: See :ref:`intro_threads`
        :type thread_type: models.ThreadType
        :raises: FBchatException if request failed
        """

        thread_id, thread_type = self._getThread(thread_id, thread_type)

        if thread_type == ThreadType.USER:
            # The thread is a user, so we change the user's nickname
            return self.changeNickname(title, thread_id, thread_id=thread_id, thread_type=thread_type)

        data = {
            'thread_name': title,
            'thread_id': thread_id,
        }

        j = self._post(self.req_url.THREAD_NAME, data, fix_request=True, as_json=True)

    def changeNickname(self, nickname, user_id, thread_id=None, thread_type=ThreadType.USER):
        """
        Changes the nickname of a user in a thread

        :param nickname: New nickname
        :param user_id: User that will have their nickname changed
        :param thread_id: User/Group ID to change color of. See :ref:`intro_threads`
        :param thread_type: See :ref:`intro_threads`
        :type thread_type: models.ThreadType
        :raises: FBchatException if request failed
        """
        thread_id, thread_type = self._getThread(thread_id, thread_type)

        data = {
            'nickname': nickname,
            'participant_id': user_id,
            'thread_or_other_fbid': thread_id
        }

        j = self._post(self.req_url.THREAD_NICKNAME, data, fix_request=True, as_json=True)

    def changeThreadColor(self, color, thread_id=None):
        """
        Changes thread color

        :param color: New thread color
        :param thread_id: User/Group ID to change color of. See :ref:`intro_threads`
        :type color: models.ThreadColor
        :raises: FBchatException if request failed
        """
        thread_id, thread_type = self._getThread(thread_id, None)

        data = {
            'color_choice': color.value if color != ThreadColor.MESSENGER_BLUE else '',
            'thread_or_other_fbid': thread_id
        }

        j = self._post(self.req_url.THREAD_COLOR, data, fix_request=True, as_json=True)

    def changeThreadEmoji(self, emoji, thread_id=None):
        """
        Changes thread color

        Trivia: While changing the emoji, the Facebook web client actually sends multiple different requests, though only this one is required to make the change

        :param color: New thread emoji
        :param thread_id: User/Group ID to change emoji of. See :ref:`intro_threads`
        :raises: FBchatException if request failed
        """
        thread_id, thread_type = self._getThread(thread_id, None)

        data = {
            'emoji_choice': emoji,
            'thread_or_other_fbid': thread_id
        }

        j = self._post(self.req_url.THREAD_EMOJI, data, fix_request=True, as_json=True)

    def reactToMessage(self, message_id, reaction):
        """
        Reacts to a message

        :param message_id: :ref:`Message ID <intro_message_ids>` to react to
        :param reaction: Reaction emoji to use
        :type reaction: models.MessageReaction
        :raises: FBchatException if request failed
        """
        full_data = {
            "doc_id": 1491398900900362,
            "variables": json.dumps({
                "data": {
                    "action": "ADD_REACTION",
                    "client_mutation_id": "1",
                    "actor_id": self.uid,
                    "message_id": str(message_id),
                    "reaction": reaction.value
                }
            })
        }

        j = self._post(self.req_url.MESSAGE_REACTION, full_data, fix_request=True, as_json=True)

    def createPlan(self, plan, thread_id=None):
        """
        Sets a plan

        :param plan: Plan to set
        :param thread_id: User/Group ID to send plan to. See :ref:`intro_threads`
        :type plan: models.Plan
        :raises: FBchatException if request failed
        """
        thread_id, thread_type = self._getThread(thread_id, None)

        full_data = {
            "event_type": "EVENT",
            "event_time" : plan.time,
            "title" : plan.title,
            "thread_id" : thread_id,
            "location_id" : plan.location_id or '',
            "location_name" : plan.location or '',
            "acontext": {
                "action_history": [{
                    "surface": "messenger_chat_tab",
                    "mechanism": "messenger_composer"
                }]
            }
        }

        j = self._post(self.req_url.PLAN_CREATE, full_data, fix_request=True, as_json=True)

    def editPlan(self, plan, new_plan):
        """
        Edits a plan

        :param plan: Plan to edit
        :param new_plan: New plan
        :type plan: models.Plan
        :raises: FBchatException if request failed
        """
        full_data = {
            "event_reminder_id": plan.uid,
            "delete": "false",
            "date": new_plan.time,
            "location_name": new_plan.location or '',
            "location_id": new_plan.location_id or '',
            "title": new_plan.title,
            "acontext": {
                "action_history": [{
                    "surface": "messenger_chat_tab",
                    "mechanism": "reminder_banner"
                }]
            }
        }

        j = self._post(self.req_url.PLAN_CHANGE, full_data, fix_request=True, as_json=True)

    def deletePlan(self, plan):
        """
        Deletes a plan

        :param plan: Plan to delete
        :raises: FBchatException if request failed
        """
        full_data = {
            "event_reminder_id": plan.uid,
            "delete": "true",
            "acontext": {
                "action_history": [{
                    "surface": "messenger_chat_tab",
                    "mechanism": "reminder_banner"
                }]
            }
        }

        j = self._post(self.req_url.PLAN_CHANGE, full_data, fix_request=True, as_json=True)

    def changePlanParticipation(self, plan, take_part=True):
        """
        Changes participation in a plan

        :param plan: Plan to take part in or not
        :param take_part: Whether to take part in the plan
        :raises: FBchatException if request failed
        """
        full_data = {
            "event_reminder_id": plan.uid,
            "guest_state": "GOING" if take_part else "DECLINED",
            "acontext": {
                "action_history": [{
                    "surface": "messenger_chat_tab",
                    "mechanism": "reminder_banner"
                }]
            }
        }

        j = self._post(self.req_url.PLAN_PARTICIPATION, full_data, fix_request=True, as_json=True)

    def eventReminder(self, thread_id, time, title, location='', location_id=''):
        """
        Deprecated. Use :func:`fbchat.Client.createPlan` instead
        """
        self.createPlan(plan=Plan(time=time, title=title, location=location, location_id=location_id), thread_id=thread_id)

    def createPoll(self, poll, thread_id=None):
        """
        Creates poll in a group thread

        :param poll: Poll to create
        :param thread_id: User/Group ID to create poll in. See :ref:`intro_threads`
        :type poll: models.Poll
        :raises: FBchatException if request failed
        """
        thread_id, thread_type = self._getThread(thread_id, None)

        # We're using ordered dicts, because the Facebook endpoint that parses the POST
        # parameters is badly implemented, and deals with ordering the options wrongly.
        # This also means we had to change `client.payloadDefault` to an ordered dict,
        # since that's being copied in between this point and the `requests` call
        #
        # If you can find a way to fix this for the endpoint, or if you find another
        # endpoint, please do suggest it ;)
        data = OrderedDict([
            ("question_text", poll.title),
            ("target_id", thread_id),
        ])

        for i, option in enumerate(poll.options):
            data["option_text_array[{}]".format(i)] = option.text
            data["option_is_selected_array[{}]".format(i)] = str(int(option.vote))

        j = self._post(self.req_url.CREATE_POLL, data, fix_request=True, as_json=True)

    def updatePollVote(self, poll_id, option_ids=[], new_options=[]):
        """
        Updates a poll vote

        :param poll_id: ID of the poll to update vote
        :param option_ids: List of the option IDs to vote
        :param new_options: List of the new option names
        :param thread_id: User/Group ID to change status in. See :ref:`intro_threads`
        :param thread_type: See :ref:`intro_threads`
        :type thread_type: models.ThreadType
        :raises: FBchatException if request failed
        """
        data = {
            "question_id": poll_id
        }

        for i, option_id in enumerate(option_ids):
            data["selected_options[{}]".format(i)] = option_id

        for i, option_text in enumerate(new_options):
            data["new_options[{}]".format(i)] = option_text

        j = self._post(self.req_url.UPDATE_VOTE, data, fix_request=True, as_json=True)

    def setTypingStatus(self, status, thread_id=None, thread_type=None):
        """
        Sets users typing status in a thread

        :param status: Specify the typing status
        :param thread_id: User/Group ID to change status in. See :ref:`intro_threads`
        :param thread_type: See :ref:`intro_threads`
        :type status: models.TypingStatus
        :type thread_type: models.ThreadType
        :raises: FBchatException if request failed
        """
        thread_id, thread_type = self._getThread(thread_id, thread_type)

        data = {
            "typ": status.value,
            "thread": thread_id,
            "to": thread_id if thread_type == ThreadType.USER else "",
            "source": "mercury-chat"
        }

        j = self._post(self.req_url.TYPING, data, fix_request=True, as_json=True)

    """
    END SEND METHODS
    """

    def markAsDelivered(self, thread_id, message_id):
        """
        Mark a message as delivered

        :param thread_id: User/Group ID to which the message belongs. See :ref:`intro_threads`
        :param message_id: Message ID to set as delivered. See :ref:`intro_threads`
        :return: Whether the request was successful
        :raises: FBchatException if request failed
        """
        data = {
            "message_ids[0]": message_id,
            "thread_ids[%s][0]" % thread_id: message_id
        }

        r = self._post(self.req_url.DELIVERED, data)
        return r.ok

    def _readStatus(self, read, thread_ids):
        thread_ids = require_list(thread_ids)

        data = {
            "watermarkTimestamp": now(),
            "shouldSendReadReceipt": 'true',
        }

        for thread_id in thread_ids:
            data["ids[{}]".format(thread_id)] = read

        r = self._post(self.req_url.READ_STATUS, data)
        return r.ok

    def markAsRead(self, thread_ids=None):
        """
        Mark threads as read
        All messages inside the threads will be marked as read

        :param thread_ids: User/Group IDs to set as read. See :ref:`intro_threads`
        :return: Whether the request was successful
        :raises: FBchatException if request failed
        """
        self._readStatus(True, thread_ids)

    def markAsUnread(self, thread_ids=None):
        """
        Mark threads as unread
        All messages inside the threads will be marked as unread

        :param thread_ids: User/Group IDs to set as unread. See :ref:`intro_threads`
        :return: Whether the request was successful
        :raises: FBchatException if request failed
        """
        self._readStatus(False, thread_ids)

    def markAsSeen(self):
        """
        .. todo::
            Documenting this
        """
        r = self._post(self.req_url.MARK_SEEN, {"seen_timestamp": 0})
        return r.ok

    def friendConnect(self, friend_id):
        """
        .. todo::
            Documenting this
        """
        data = {
            "to_friend": friend_id,
            "action": "confirm"
        }

        r = self._post(self.req_url.CONNECT, data)
        return r.ok

    def removeFriend(self, friend_id=None):
        """
        Removes a specifed friend from your friend list

        :param friend_id: The ID of the friend that you want to remove
        :return: Returns error if the removing was unsuccessful, returns True when successful.
        """
        payload = {
            "friend_id": friend_id,
            "unref": "none",
            "confirm": "Confirm",
        }
        r = self._post(self.req_url.REMOVE_FRIEND, payload)
        query = parse_qs(urlparse(r.url).query)
        if "err" not in query:
            log.debug("Remove was successful!")
            return True
        else:
            log.warning("Error while removing friend")
            return False

    def blockUser(self, user_id):
        """
        Blocks messages from a specifed user

        :param user_id: The ID of the user that you want to block
        :return: Whether the request was successful
        :raises: FBchatException if request failed
        """
        data = {
            'fbid': user_id
        }
        r = self._post(self.req_url.BLOCK_USER, data)
        return r.ok

    def unblockUser(self, user_id):
        """
        Unblocks messages from a blocked user

        :param user_id: The ID of the user that you want to unblock
        :return: Whether the request was successful
        :raises: FBchatException if request failed
        """
        data = {
            'fbid': user_id
        }
        r = self._post(self.req_url.UNBLOCK_USER, data)
        return r.ok

    def moveThreads(self, location, thread_ids):
        """
        Moves threads to specifed location

        :param location: models.ThreadLocation: INBOX, PENDING, ARCHIVED or OTHER
        :param thread_ids: Thread IDs to move. See :ref:`intro_threads`
        :return: Whether the request was successful
        :raises: FBchatException if request failed
        """
        thread_ids = require_list(thread_ids)

        if location == ThreadLocation.PENDING:
            location = ThreadLocation.OTHER

        if location == ThreadLocation.ARCHIVED:
            data_archive = dict()
            data_unpin = dict()
            for thread_id in thread_ids:
                data_archive["ids[{}]".format(thread_id)] = 'true'
                data_unpin["ids[{}]".format(thread_id)] = 'false'
            r_archive = self._post(self.req_url.ARCHIVED_STATUS, data_archive)
            r_unpin = self._post(self.req_url.PINNED_STATUS, data_unpin)
            return r_archive.ok and r_unpin.ok
        else:
            data = dict()
            for i, thread_id in enumerate(thread_ids):
                data["{}[{}]".format(location.name.lower(), i)] = thread_id
            r = self._post(self.req_url.MOVE_THREAD, data)
            return r.ok

    def deleteThreads(self, thread_ids):
        """
        Deletes threads

        :param thread_ids: Thread IDs to delete. See :ref:`intro_threads`
        :return: Whether the request was successful
        :raises: FBchatException if request failed
        """
        thread_ids = require_list(thread_ids)

        data_unpin = dict()
        data_delete = dict()
        for i, thread_id in enumerate(thread_ids):
            data_unpin["ids[{}]".format(thread_id)] = "false"
            data_delete["ids[{}]".format(i)] = thread_id
        r_unpin = self._post(self.req_url.PINNED_STATUS, data_unpin)
        r_delete = self._post(self.req_url.DELETE_THREAD, data_delete)
        return r_unpin.ok and r_delete.ok

    def markAsSpam(self, thread_id=None):
        """
        Mark a thread as spam and delete it

        :param thread_id: User/Group ID to mark as spam. See :ref:`intro_threads`
        :return: Whether the request was successful
        :raises: FBchatException if request failed
        """
        thread_id, thread_type = self._getThread(thread_id, None)
        r = self._post(self.req_url.MARK_SPAM, {"id": thread_id})
        return r.ok

    def deleteMessages(self, message_ids):
        """
        Deletes specifed messages

        :param message_ids: Message IDs to delete
        :return: Whether the request was successful
        :raises: FBchatException if request failed
        """
        message_ids = require_list(message_ids)
        data = dict()
        for i, message_id in enumerate(message_ids):
            data["message_ids[{}]".format(i)] = message_id
        r = self._post(self.req_url.DELETE_MESSAGES, data)
        return r.ok

    def muteThread(self, mute_time=-1, thread_id=None):
        """
        Mutes thread

        :param mute_time: Mute time in seconds, leave blank to mute forever
        :param thread_id: User/Group ID to mute. See :ref:`intro_threads`
        """
        thread_id, thread_type = self._getThread(thread_id, None)
        data = {
            "mute_settings": str(mute_time),
            "thread_fbid": thread_id
        }
        r = self._post(self.req_url.MUTE_THREAD, data)
        r.raise_for_status()

    def unmuteThread(self, thread_id=None):
        """
        Unmutes thread

        :param thread_id: User/Group ID to unmute. See :ref:`intro_threads`
        """
        return self.muteThread(0, thread_id)

    def muteThreadReactions(self, mute=True, thread_id=None):
        """
        Mutes thread reactions

        :param mute: Boolean. True to mute, False to unmute
        :param thread_id: User/Group ID to mute. See :ref:`intro_threads`
        """
        thread_id, thread_type = self._getThread(thread_id, None)
        data = {
            "reactions_mute_mode": int(mute),
            "thread_fbid": thread_id
        }
        r = self._post(self.req_url.MUTE_REACTIONS, data)
        r.raise_for_status()

    def unmuteThreadReactions(self, thread_id=None):
        """
        Unmutes thread reactions

        :param thread_id: User/Group ID to unmute. See :ref:`intro_threads`
        """
        return self.muteThreadReactions(False, thread_id)

    def muteThreadMentions(self, mute=True, thread_id=None):
        """
        Mutes thread mentions

        :param mute: Boolean. True to mute, False to unmute
        :param thread_id: User/Group ID to mute. See :ref:`intro_threads`
        """
        thread_id, thread_type = self._getThread(thread_id, None)
        data = {
            "mentions_mute_mode": int(mute),
            "thread_fbid": thread_id
        }
        r = self._post(self.req_url.MUTE_MENTIONS, data)
        r.raise_for_status()

    def unmuteThreadMentions(self, thread_id=None):
        """
        Unmutes thread mentions

        :param thread_id: User/Group ID to unmute. See :ref:`intro_threads`
        """
        return self.muteThreadMentions(False, thread_id)

    """
    LISTEN METHODS
    """

    def _ping(self, sticky, pool):
        data = {
            'channel': self.user_channel,
            'clientid': self.client_id,
            'partition': -2,
            'cap': 0,
            'uid': self.uid,
            'sticky_token': sticky,
            'sticky_pool': pool,
            'viewer_uid': self.uid,
            'state': 'active'
        }
        self._get(self.req_url.PING, data, fix_request=True, as_json=False)

    def _fetchSticky(self):
        """Call pull api to get sticky and pool parameter, newer api needs these parameters to work"""

        data = {
            "msgs_recv": 0,
            "channel": self.user_channel,
            "clientid": self.client_id
        }

        j = self._get(self.req_url.STICKY, data, fix_request=True, as_json=True)

        if j.get('lb_info') is None:
            raise FBchatException('Missing lb_info: {}'.format(j))

        return j['lb_info']['sticky'], j['lb_info']['pool']

    def _pullMessage(self, sticky, pool):
        """Call pull api with seq value to get message data."""

        data = {
            "msgs_recv": 0,
            "sticky_token": sticky,
            "sticky_pool": pool,
            "clientid": self.client_id,
        }

        j = self._get(ReqUrl.STICKY, data, fix_request=True, as_json=True)

        self.seq = j.get('seq', '0')
        return j

    def _parseMessage(self, content):
        """Get message and author name from content. May contain multiple messages in the content."""

        if 'ms' not in content: return

        for m in content["ms"]:
            mtype = m.get("type")
            try:
                # Things that directly change chat
                if mtype == "delta":

                    def getThreadIdAndThreadType(msg_metadata):
                        """Returns a tuple consisting of thread ID and thread type"""
                        id_thread = None
                        type_thread = None
                        if 'threadFbId' in msg_metadata['threadKey']:
                            id_thread = str(msg_metadata['threadKey']['threadFbId'])
                            type_thread = ThreadType.GROUP
                        elif 'otherUserFbId' in msg_metadata['threadKey']:
                            id_thread = str(msg_metadata['threadKey']['otherUserFbId'])
                            type_thread = ThreadType.USER
                        return id_thread, type_thread

                    delta = m["delta"]
                    delta_type = delta.get("type")
                    metadata = delta.get("messageMetadata")

                    if metadata:
                        mid = metadata["messageId"]
                        author_id = str(metadata['actorFbId'])
                        ts = int(metadata.get("timestamp"))

                    # Added participants
                    if 'addedParticipants' in delta:
                        added_ids = [str(x['userFbId']) for x in delta['addedParticipants']]
                        thread_id = str(metadata['threadKey']['threadFbId'])
                        self.onPeopleAdded(mid=mid, added_ids=added_ids, author_id=author_id, thread_id=thread_id,
                                           ts=ts, msg=m)

                    # Left/removed participants
                    elif 'leftParticipantFbId' in delta:
                        removed_id = str(delta['leftParticipantFbId'])
                        thread_id = str(metadata['threadKey']['threadFbId'])
                        self.onPersonRemoved(mid=mid, removed_id=removed_id, author_id=author_id, thread_id=thread_id,
                                             ts=ts, msg=m)

                    # Color change
                    elif delta_type == "change_thread_theme":
                        new_color = graphql_color_to_enum(delta["untypedData"]["theme_color"])
                        thread_id, thread_type = getThreadIdAndThreadType(metadata)
                        self.onColorChange(mid=mid, author_id=author_id, new_color=new_color, thread_id=thread_id,
                                           thread_type=thread_type, ts=ts, metadata=metadata, msg=m)

                    # Emoji change
                    elif delta_type == "change_thread_icon":
                        new_emoji = delta["untypedData"]["thread_icon"]
                        thread_id, thread_type = getThreadIdAndThreadType(metadata)
                        self.onEmojiChange(mid=mid, author_id=author_id, new_emoji=new_emoji, thread_id=thread_id,
                                           thread_type=thread_type, ts=ts, metadata=metadata, msg=m)

                    # Thread title change
                    elif delta.get("class") == "ThreadName":
                        new_title = delta["name"]
                        thread_id, thread_type = getThreadIdAndThreadType(metadata)
                        self.onTitleChange(mid=mid, author_id=author_id, new_title=new_title, thread_id=thread_id,
                                           thread_type=thread_type, ts=ts, metadata=metadata, msg=m)

                    # Forced fetch
                    elif delta.get("class") == "ForcedFetch":
                        mid = delta.get("messageId")
                        if mid is None:
                            self.onUnknownMesssageType(msg=m)
                        else:
                            thread_id = str(delta['threadKey']['threadFbId'])
                            fetch_info = self._forcedFetch(thread_id, mid)
                            fetch_data = fetch_info["message"]
                            author_id = fetch_data["message_sender"]["id"]
                            ts = fetch_data["timestamp_precise"]
                            if fetch_data.get("__typename") == "ThreadImageMessage":
                                # Thread image change
                                image_metadata = fetch_data.get("image_with_metadata")
                                image_id = int(image_metadata["legacy_attachment_id"]) if image_metadata else None
                                self.onImageChange(mid=mid, author_id=author_id, new_image=image_id, thread_id=thread_id,
                                                   thread_type=ThreadType.GROUP, ts=ts)

                    # Nickname change
                    elif delta_type == "change_thread_nickname":
                        changed_for = str(delta["untypedData"]["participant_id"])
                        new_nickname = delta["untypedData"]["nickname"]
                        thread_id, thread_type = getThreadIdAndThreadType(metadata)
                        self.onNicknameChange(mid=mid, author_id=author_id, changed_for=changed_for,
                                              new_nickname=new_nickname,
                                              thread_id=thread_id, thread_type=thread_type, ts=ts, metadata=metadata, msg=m)

                    # Admin added or removed in a group thread
                    elif delta_type == "change_thread_admins":
                        thread_id, thread_type = getThreadIdAndThreadType(metadata)
                        target_id = delta["untypedData"]["TARGET_ID"]
                        admin_event = delta["untypedData"]["ADMIN_EVENT"]
                        if admin_event == "add_admin":
                            self.onAdminAdded(mid=mid, added_id=target_id, author_id=author_id, thread_id=thread_id,
                                               thread_type=thread_type, ts=ts, msg=m)
                        elif admin_event == "remove_admin":
                            self.onAdminRemoved(mid=mid, removed_id=target_id, author_id=author_id, thread_id=thread_id,
                                                 thread_type=thread_type, ts=ts, msg=m)

                    # Group approval mode change
                    elif delta_type == "change_thread_approval_mode":
                        thread_id, thread_type = getThreadIdAndThreadType(metadata)
                        approval_mode = bool(int(delta['untypedData']['APPROVAL_MODE']))
                        self.onApprovalModeChange(mid=mid, approval_mode=approval_mode, author_id=author_id,
                                                  thread_id=thread_id, thread_type=thread_type, ts=ts, msg=m)

                    # Message delivered
                    elif delta.get("class") == "DeliveryReceipt":
                        message_ids = delta["messageIds"]
                        delivered_for = str(delta.get("actorFbId") or delta["threadKey"]["otherUserFbId"])
                        ts = int(delta["deliveredWatermarkTimestampMs"])
                        thread_id, thread_type = getThreadIdAndThreadType(delta)
                        self.onMessageDelivered(msg_ids=message_ids, delivered_for=delivered_for,
                                                thread_id=thread_id, thread_type=thread_type, ts=ts,
                                                metadata=metadata, msg=m)

                    # Message seen
                    elif delta.get("class") == "ReadReceipt":
                        seen_by = str(delta.get("actorFbId") or delta["threadKey"]["otherUserFbId"])
                        seen_ts = int(delta["actionTimestampMs"])
                        delivered_ts = int(delta["watermarkTimestampMs"])
                        thread_id, thread_type = getThreadIdAndThreadType(delta)
                        self.onMessageSeen(seen_by=seen_by, thread_id=thread_id, thread_type=thread_type,
                                           seen_ts=seen_ts, ts=delivered_ts, metadata=metadata, msg=m)

                    # Messages marked as seen
                    elif delta.get("class") == "MarkRead":
                        seen_ts = int(delta.get("actionTimestampMs") or delta.get("actionTimestamp"))
                        delivered_ts = int(delta.get("watermarkTimestampMs") or delta.get("watermarkTimestamp"))

                        threads = []
                        if "folders" not in delta:
                            threads = [getThreadIdAndThreadType({"threadKey": thr}) for thr in delta.get("threadKeys")]

                        # thread_id, thread_type = getThreadIdAndThreadType(delta)
                        self.onMarkedSeen(threads=threads, seen_ts=seen_ts, ts=delivered_ts, metadata=delta, msg=m)

                    # Game played
                    elif delta_type == "instant_game_update":
                        game_id = delta["untypedData"]["game_id"]
                        game_name = delta["untypedData"]["game_name"]
                        score = delta["untypedData"].get("score")
                        if score is not None:
                            score = int(score)
                        leaderboard = delta["untypedData"].get("leaderboard")
                        if leaderboard is not None:
                            leaderboard = json.loads(leaderboard)["scores"]
                        thread_id, thread_type = getThreadIdAndThreadType(metadata)
                        self.onGamePlayed(mid=mid, author_id=author_id, game_id=game_id, game_name=game_name,
                                           score=score, leaderboard=leaderboard, thread_id=thread_id,
                                           thread_type=thread_type, ts=ts, metadata=metadata, msg=m)

                    # Group call started/ended
                    elif delta_type == "rtc_call_log":
                        thread_id, thread_type = getThreadIdAndThreadType(metadata)
                        call_status = delta["untypedData"]["event"]
                        call_duration = int(delta["untypedData"]["call_duration"])
                        is_video_call = bool(int(delta["untypedData"]["is_video_call"]))
                        if call_status == "call_started":
                            self.onCallStarted(mid=mid, caller_id=author_id, is_video_call=is_video_call,
                                                thread_id=thread_id, thread_type=thread_type, ts=ts, metadata=metadata, msg=m)
                        elif call_status == "call_ended":
                            self.onCallEnded(mid=mid, caller_id=author_id, is_video_call=is_video_call, call_duration=call_duration,
                                                thread_id=thread_id, thread_type=thread_type, ts=ts, metadata=metadata, msg=m)

                    # User joined to group call
                    elif delta_type == "participant_joined_group_call":
                        thread_id, thread_type = getThreadIdAndThreadType(metadata)
                        is_video_call = bool(int(delta["untypedData"]["group_call_type"]))
                        self.onUserJoinedCall(mid=mid, joined_id=author_id, is_video_call=is_video_call,
                                            thread_id=thread_id, thread_type=thread_type, ts=ts, metadata=metadata, msg=m)

                    # Group poll event
                    elif delta_type == "group_poll":
                        thread_id, thread_type = getThreadIdAndThreadType(metadata)
                        event_type = delta["untypedData"]["event_type"]
                        poll_json = json.loads(delta["untypedData"]["question_json"])
                        poll = graphql_to_poll(poll_json)
                        if event_type == "question_creation":
                            # User created group poll
                            self.onPollCreated(mid=mid, poll=poll, author_id=author_id, thread_id=thread_id, thread_type=thread_type,
                                               ts=ts, metadata=metadata, msg=m)
                        elif event_type == "update_vote":
                            # User voted on group poll
                            added_options = json.loads(delta["untypedData"]["added_option_ids"])
                            removed_options = json.loads(delta["untypedData"]["removed_option_ids"])
                            self.onPollVoted(mid=mid, poll=poll, added_options=added_options, removed_options=removed_options,
                                             author_id=author_id, thread_id=thread_id, thread_type=thread_type,
                                             ts=ts, metadata=metadata, msg=m)

                    # Plan created
                    elif delta_type == "lightweight_event_create":
                        thread_id, thread_type = getThreadIdAndThreadType(metadata)
                        plan = graphql_to_plan(delta["untypedData"])
                        self.onPlanCreated(mid=mid, plan=plan, author_id=author_id, thread_id=thread_id, thread_type=thread_type,
                                           ts=ts, metadata=metadata, msg=m)

                    # Plan ended
                    elif delta_type == "lightweight_event_notify":
                        thread_id, thread_type = getThreadIdAndThreadType(metadata)
                        plan = graphql_to_plan(delta["untypedData"])
                        self.onPlanEnded(mid=mid, plan=plan, thread_id=thread_id, thread_type=thread_type,
                                            ts=ts, metadata=metadata, msg=m)

                    # Plan edited
                    elif delta_type == "lightweight_event_update":
                        thread_id, thread_type = getThreadIdAndThreadType(metadata)
                        plan = graphql_to_plan(delta["untypedData"])
                        self.onPlanEdited(mid=mid, plan=plan, author_id=author_id, thread_id=thread_id,
                                          thread_type=thread_type, ts=ts, metadata=metadata, msg=m)

                    # Plan deleted
                    elif delta_type == "lightweight_event_delete":
                        thread_id, thread_type = getThreadIdAndThreadType(metadata)
                        plan = graphql_to_plan(delta["untypedData"])
                        self.onPlanDeleted(mid=mid, plan=plan, author_id=author_id, thread_id=thread_id,
                                           thread_type=thread_type, ts=ts, metadata=metadata, msg=m)

                     # Plan participation change
                    elif delta_type == "lightweight_event_rsvp":
                        thread_id, thread_type = getThreadIdAndThreadType(metadata)
                        plan = graphql_to_plan(delta["untypedData"])
                        take_part = delta["untypedData"]["guest_status"] == "GOING"
                        self.onPlanParticipation(mid=mid, plan=plan, take_part=take_part, author_id=author_id,
                                                 thread_id=thread_id, thread_type=thread_type, ts=ts, metadata=metadata, msg=m)

                    # New message
                    elif delta.get("class") == "NewMessage":
                        mentions = []
                        if delta.get('data') and delta['data'].get('prng'):
                            try:
                                mentions = [Mention(str(mention.get('i')), offset=mention.get('o'), length=mention.get('l')) for mention in parse_json(delta['data']['prng'])]
                            except Exception:
                                log.exception('An exception occured while reading attachments')

                        sticker = None
                        attachments = []
                        if delta.get('attachments'):
                            try:
                                for a in delta['attachments']:
                                    mercury = a['mercury']
                                    if mercury.get('blob_attachment'):
                                        image_metadata = a.get('imageMetadata', {})
                                        attach_type = mercury['blob_attachment']['__typename']
                                        attachment = graphql_to_attachment(mercury.get('blob_attachment', {}))

                                        if attach_type == ['MessageFile', 'MessageVideo', 'MessageAudio']:
                                            # TODO: Add more data here for audio files
                                            attachment.size = int(a['fileSize'])
                                        attachments.append(attachment)
                                    elif mercury.get('sticker_attachment'):
                                        sticker = graphql_to_sticker(a['mercury']['sticker_attachment'])
                                    elif mercury.get('extensible_attachment'):
                                        # TODO: Add more data here for shared stuff (URLs, events and so on)
                                        pass
                            except Exception:
                                log.exception('An exception occured while reading attachments: {}'.format(delta['attachments']))

                        if metadata and metadata.get('tags'):
                            emoji_size = get_emojisize_from_tags(metadata.get('tags'))

                        message = Message(
                            text=delta.get('body'),
                            mentions=mentions,
                            emoji_size=emoji_size,
                            sticker=sticker,
                            attachments=attachments
                        )
                        message.uid = mid
                        message.author = author_id
                        message.timestamp = ts
                        #message.reactions = {}
                        thread_id, thread_type = getThreadIdAndThreadType(metadata)
                        self.onMessage(mid=mid, author_id=author_id, message=delta.get('body', ''), message_object=message,
                                       thread_id=thread_id, thread_type=thread_type, ts=ts, metadata=metadata, msg=m)

                    # Unknown message type
                    else:
                        self.onUnknownMesssageType(msg=m)

                # Inbox
                elif mtype == "inbox":
                    self.onInbox(unseen=m["unseen"], unread=m["unread"], recent_unread=m["recent_unread"], msg=m)

                # Typing
                elif mtype == "typ" or mtype == "ttyp":
                    author_id = str(m.get("from"))
                    thread_id = m.get("thread_fbid")
                    if thread_id:
                        thread_type = ThreadType.GROUP
                        thread_id = str(thread_id)
                    else:
                        thread_type = ThreadType.USER
                        if author_id == self.uid:
                            thread_id = m.get("to")
                        else:
                            thread_id = author_id
                    typing_status = TypingStatus(m.get("st"))
                    self.onTyping(author_id=author_id, status=typing_status, thread_id=thread_id, thread_type=thread_type, msg=m)

                # Delivered

                # Seen
                # elif mtype == "m_read_receipt":
                #
                #     self.onSeen(m.get('realtime_viewer_fbid'), m.get('reader'), m.get('time'))

                elif mtype in ['jewel_requests_add']:
                    from_id = m['from']
                    self.onFriendRequest(from_id=from_id, msg=m)

                # Happens on every login
                elif mtype == "qprimer":
                    self.onQprimer(ts=m.get("made"), msg=m)

                # Is sent before any other message
                elif mtype == "deltaflow":
                    pass

                # Chat timestamp
                elif mtype == "chatproxy-presence":
                    buddylist = {}
                    for _id in m.get('buddyList', {}):
                        payload = m['buddyList'][_id]
                        buddylist[_id] = payload.get('lat')
                    self.onChatTimestamp(buddylist=buddylist, msg=m)

                # Unknown message type
                else:
                    self.onUnknownMesssageType(msg=m)

            except Exception as e:
                self.onMessageError(exception=e, msg=m)

    def startListening(self):
        """
        Start listening from an external event loop

        :raises: FBchatException if request failed
        """
        self.listening = True
        self.sticky, self.pool = self._fetchSticky()

    def doOneListen(self, markAlive=True):
        """
        Does one cycle of the listening loop.
        This method is useful if you want to control fbchat from an external event loop

        :param markAlive: Whether this should ping the Facebook server before running
        :type markAlive: bool
        :return: Whether the loop should keep running
        :rtype: bool
        """
        try:
            if markAlive:
                self._ping(self.sticky, self.pool)
            content = self._pullMessage(self.sticky, self.pool)
            if content:
                self._parseMessage(content)
        except KeyboardInterrupt:
            return False
        except requests.Timeout:
            pass
        except requests.ConnectionError:
            # If the client has lost their internet connection, keep trying every 30 seconds
            time.sleep(30)
        except FBchatFacebookError as e:
            # Fix 502 and 503 pull errors
            if e.request_status_code in [502, 503]:
                self.req_url.change_pull_channel()
                self.startListening()
            else:
                raise e
        except Exception as e:
            return self.onListenError(exception=e)

        return True

    def stopListening(self):
        """Cleans up the variables from startListening"""
        self.listening = False
        self.sticky, self.pool = (None, None)

    def listen(self, markAlive=True):
        """
        Initializes and runs the listening loop continually

        :param markAlive: Whether this should ping the Facebook server each time the loop runs
        :type markAlive: bool
        """
        self.startListening()
        self.onListening()

        while self.listening and self.doOneListen(markAlive):
            pass

        self.stopListening()

    """
    END LISTEN METHODS
    """

    """
    EVENTS
    """

    def onLoggingIn(self, email=None):
        """
        Called when the client is logging in

        :param email: The email of the client
        """
        log.info("Logging in {}...".format(email))

    def on2FACode(self):
        """Called when a 2FA code is needed to progress"""
        return input('Please enter your 2FA code --> ')

    def onLoggedIn(self, email=None):
        """
        Called when the client is successfully logged in

        :param email: The email of the client
        """
        log.info("Login of {} successful.".format(email))

    def onListening(self):
        """Called when the client is listening"""
        log.info("Listening...")

    def onListenError(self, exception=None):
        """
        Called when an error was encountered while listening

        :param exception: The exception that was encountered
        :return: Whether the loop should keep running
        """
        log.exception('Got exception while listening')
        return True


    def onMessage(self, mid=None, author_id=None, message=None, message_object=None, thread_id=None, thread_type=ThreadType.USER, ts=None, metadata=None, msg=None):
        """
        Called when the client is listening, and somebody sends a message

        :param mid: The message ID
        :param author_id: The ID of the author
        :param message: (deprecated. Use `message_object.text` instead)
        :param message_object: The message (As a `Message` object)
        :param thread_id: Thread ID that the message was sent to. See :ref:`intro_threads`
        :param thread_type: Type of thread that the message was sent to. See :ref:`intro_threads`
        :param ts: The timestamp of the message
        :param metadata: Extra metadata about the message
        :param msg: A full set of the data recieved
        :type message_object: models.Message
        :type thread_type: models.ThreadType
        """
        log.info("{} from {} in {}".format(message_object, thread_id, thread_type.name))

    def onColorChange(self, mid=None, author_id=None, new_color=None, thread_id=None, thread_type=ThreadType.USER, ts=None, metadata=None, msg=None):
        """
        Called when the client is listening, and somebody changes a thread's color

        :param mid: The action ID
        :param author_id: The ID of the person who changed the color
        :param new_color: The new color
        :param thread_id: Thread ID that the action was sent to. See :ref:`intro_threads`
        :param thread_type: Type of thread that the action was sent to. See :ref:`intro_threads`
        :param ts: A timestamp of the action
        :param metadata: Extra metadata about the action
        :param msg: A full set of the data recieved
        :type new_color: models.ThreadColor
        :type thread_type: models.ThreadType
        """
        log.info("Color change from {} in {} ({}): {}".format(author_id, thread_id, thread_type.name, new_color))

    def onEmojiChange(self, mid=None, author_id=None, new_emoji=None, thread_id=None, thread_type=ThreadType.USER, ts=None, metadata=None, msg=None):
        """
        Called when the client is listening, and somebody changes a thread's emoji

        :param mid: The action ID
        :param author_id: The ID of the person who changed the emoji
        :param new_emoji: The new emoji
        :param thread_id: Thread ID that the action was sent to. See :ref:`intro_threads`
        :param thread_type: Type of thread that the action was sent to. See :ref:`intro_threads`
        :param ts: A timestamp of the action
        :param metadata: Extra metadata about the action
        :param msg: A full set of the data recieved
        :type thread_type: models.ThreadType
        """
        log.info("Emoji change from {} in {} ({}): {}".format(author_id, thread_id, thread_type.name, new_emoji))

    def onTitleChange(self, mid=None, author_id=None, new_title=None, thread_id=None, thread_type=ThreadType.USER, ts=None, metadata=None, msg=None):
        """
        Called when the client is listening, and somebody changes the title of a thread

        :param mid: The action ID
        :param author_id: The ID of the person who changed the title
        :param new_title: The new title
        :param thread_id: Thread ID that the action was sent to. See :ref:`intro_threads`
        :param thread_type: Type of thread that the action was sent to. See :ref:`intro_threads`
        :param ts: A timestamp of the action
        :param metadata: Extra metadata about the action
        :param msg: A full set of the data recieved
        :type thread_type: models.ThreadType
        """
        log.info("Title change from {} in {} ({}): {}".format(author_id, thread_id, thread_type.name, new_title))


    def onImageChange(self, mid=None, author_id=None, new_image=None, thread_id=None, thread_type=ThreadType.GROUP, ts=None):
        """
        Called when the client is listening, and somebody changes the image of a thread

        :param mid: The action ID
        :param new_image: The ID of the new image
        :param author_id: The ID of the person who changed the image
        :param thread_id: Thread ID that the action was sent to. See :ref:`intro_threads`
        :param ts: A timestamp of the action
        """
        log.info("{} changed thread image in {}".format(author_id, thread_id))


    def onNicknameChange(self, mid=None, author_id=None, changed_for=None, new_nickname=None, thread_id=None, thread_type=ThreadType.USER, ts=None, metadata=None, msg=None):
        """
        Called when the client is listening, and somebody changes the nickname of a person

        :param mid: The action ID
        :param author_id: The ID of the person who changed the nickname
        :param changed_for: The ID of the person whom got their nickname changed
        :param new_nickname: The new nickname
        :param thread_id: Thread ID that the action was sent to. See :ref:`intro_threads`
        :param thread_type: Type of thread that the action was sent to. See :ref:`intro_threads`
        :param ts: A timestamp of the action
        :param metadata: Extra metadata about the action
        :param msg: A full set of the data recieved
        :type thread_type: models.ThreadType
        """
        log.info("Nickname change from {} in {} ({}) for {}: {}".format(author_id, thread_id, thread_type.name, changed_for, new_nickname))


    def onAdminAdded(self, mid=None, added_id=None, author_id=None, thread_id=None, thread_type=ThreadType.GROUP, ts=None, msg=None):
        """
        Called when the client is listening, and somebody adds an admin to a group thread

        :param mid: The action ID
        :param added_id: The ID of the admin who got added
        :param author_id: The ID of the person who added the admins
        :param thread_id: Thread ID that the action was sent to. See :ref:`intro_threads`
        :param ts: A timestamp of the action
        :param msg: A full set of the data recieved
        """
        log.info("{} added admin: {} in {}".format(author_id, added_id, thread_id))


    def onAdminRemoved(self, mid=None, removed_id=None, author_id=None, thread_id=None, thread_type=ThreadType.GROUP, ts=None, msg=None):
        """
        Called when the client is listening, and somebody removes an admin from a group thread

        :param mid: The action ID
        :param removed_id: The ID of the admin who got removed
        :param author_id: The ID of the person who removed the admins
        :param thread_id: Thread ID that the action was sent to. See :ref:`intro_threads`
        :param ts: A timestamp of the action
        :param msg: A full set of the data recieved
        """
        log.info("{} removed admin: {} in {}".format(author_id, removed_id, thread_id))


    def onApprovalModeChange(self, mid=None, approval_mode=None, author_id=None, thread_id=None, thread_type=ThreadType.GROUP, ts=None, msg=None):
        """
        Called when the client is listening, and somebody changes approval mode in a group thread

        :param mid: The action ID
        :param approval_mode: True if approval mode is activated
        :param author_id: The ID of the person who changed approval mode
        :param thread_id: Thread ID that the action was sent to. See :ref:`intro_threads`
        :param ts: A timestamp of the action
        :param msg: A full set of the data recieved
        """
        if approval_mode:
            log.info("{} activated approval mode in {}".format(author_id, thread_id))
        else:
            log.info("{} disabled approval mode in {}".format(author_id, thread_id))

    def onMessageSeen(self, seen_by=None, thread_id=None, thread_type=ThreadType.USER, seen_ts=None, ts=None, metadata=None, msg=None):
        """
        Called when the client is listening, and somebody marks a message as seen

        :param seen_by: The ID of the person who marked the message as seen
        :param thread_id: Thread ID that the action was sent to. See :ref:`intro_threads`
        :param thread_type: Type of thread that the action was sent to. See :ref:`intro_threads`
        :param seen_ts: A timestamp of when the person saw the message
        :param ts: A timestamp of the action
        :param metadata: Extra metadata about the action
        :param msg: A full set of the data recieved
        :type thread_type: models.ThreadType
        """
        log.info("Messages seen by {} in {} ({}) at {}s".format(seen_by, thread_id, thread_type.name, seen_ts/1000))

    def onMessageDelivered(self, msg_ids=None, delivered_for=None, thread_id=None, thread_type=ThreadType.USER, ts=None, metadata=None, msg=None):
        """
        Called when the client is listening, and somebody marks messages as delivered

        :param msg_ids: The messages that are marked as delivered
        :param delivered_for: The person that marked the messages as delivered
        :param thread_id: Thread ID that the action was sent to. See :ref:`intro_threads`
        :param thread_type: Type of thread that the action was sent to. See :ref:`intro_threads`
        :param ts: A timestamp of the action
        :param metadata: Extra metadata about the action
        :param msg: A full set of the data recieved
        :type thread_type: models.ThreadType
        """
        log.info("Messages {} delivered to {} in {} ({}) at {}s".format(msg_ids, delivered_for, thread_id, thread_type.name, ts/1000))

    def onMarkedSeen(self, threads=None, seen_ts=None, ts=None, metadata=None, msg=None):
        """
        Called when the client is listening, and the client has successfully marked threads as seen

        :param threads: The threads that were marked
        :param author_id: The ID of the person who changed the emoji
        :param seen_ts: A timestamp of when the threads were seen
        :param ts: A timestamp of the action
        :param metadata: Extra metadata about the action
        :param msg: A full set of the data recieved
        :type thread_type: models.ThreadType
        """
        log.info("Marked messages as seen in threads {} at {}s".format([(x[0], x[1].name) for x in threads], seen_ts/1000))


    def onPeopleAdded(self, mid=None, added_ids=None, author_id=None, thread_id=None, ts=None, msg=None):
        """
        Called when the client is listening, and somebody adds people to a group thread

        :param mid: The action ID
        :param added_ids: The IDs of the people who got added
        :param author_id: The ID of the person who added the people
        :param thread_id: Thread ID that the action was sent to. See :ref:`intro_threads`
        :param ts: A timestamp of the action
        :param msg: A full set of the data recieved
        """
        log.info("{} added: {} in {}".format(author_id, ', '.join(added_ids), thread_id))

    def onPersonRemoved(self, mid=None, removed_id=None, author_id=None, thread_id=None, ts=None, msg=None):
        """
        Called when the client is listening, and somebody removes a person from a group thread

        :param mid: The action ID
        :param removed_id: The ID of the person who got removed
        :param author_id: The ID of the person who removed the person
        :param thread_id: Thread ID that the action was sent to. See :ref:`intro_threads`
        :param ts: A timestamp of the action
        :param msg: A full set of the data recieved
        """
        log.info("{} removed: {} in {}".format(author_id, removed_id, thread_id))

    def onFriendRequest(self, from_id=None, msg=None):
        """
        Called when the client is listening, and somebody sends a friend request

        :param from_id: The ID of the person that sent the request
        :param msg: A full set of the data recieved
        """
        log.info("Friend request from {}".format(from_id))

    def onInbox(self, unseen=None, unread=None, recent_unread=None, msg=None):
        """
        .. todo::
            Documenting this

        :param unseen: --
        :param unread: --
        :param recent_unread: --
        :param msg: A full set of the data recieved
        """
        log.info('Inbox event: {}, {}, {}'.format(unseen, unread, recent_unread))

    def onTyping(self, author_id=None, status=None, thread_id=None, thread_type=None, msg=None):
        """
        Called when the client is listening, and somebody starts or stops typing into a chat

        :param author_id: The ID of the person who sent the action
        :param status: The typing status
        :param thread_id: Thread ID that the action was sent to. See :ref:`intro_threads`
        :param thread_type: Type of thread that the action was sent to. See :ref:`intro_threads`
        :param msg: A full set of the data recieved
        :type typing_status: models.TypingStatus
        :type thread_type: models.ThreadType
        """
        pass

    def onGamePlayed(self, mid=None, author_id=None, game_id=None, game_name=None, score=None, leaderboard=None, thread_id=None, thread_type=None, ts=None, metadata=None, msg=None):
        """
        Called when the client is listening, and somebody plays a game

        :param mid: The action ID
        :param author_id: The ID of the person who played the game
        :param game_id: The ID of the game
        :param game_name: Name of the game
        :param score: Score obtained in the game
        :param leaderboard: Actual leaderboard of the game in the thread
        :param thread_id: Thread ID that the action was sent to. See :ref:`intro_threads`
        :param thread_type: Type of thread that the action was sent to. See :ref:`intro_threads`
        :param ts: A timestamp of the action
        :param metadata: Extra metadata about the action
        :param msg: A full set of the data recieved
        :type thread_type: models.ThreadType
        """
        log.info("{} played \"{}\" in {} ({})".format(author_id, game_name, thread_id, thread_type.name))

    def onQprimer(self, ts=None, msg=None):
        """
        Called when the client just started listening

        :param ts: A timestamp of the action
        :param msg: A full set of the data recieved
        """
        pass

    def onChatTimestamp(self, buddylist=None, msg=None):
        """
        Called when the client receives chat online presence update

        :param buddylist: A list of dicts with friend id and last seen timestamp
        :param msg: A full set of the data recieved
        """
        log.debug('Chat Timestamps received: {}'.format(buddylist))

    def onUnknownMesssageType(self, msg=None):
        """
        Called when the client is listening, and some unknown data was recieved

        :param msg: A full set of the data recieved
        """
        log.debug('Unknown message received: {}'.format(msg))

    def onMessageError(self, exception=None, msg=None):
        """
        Called when an error was encountered while parsing recieved data

        :param exception: The exception that was encountered
        :param msg: A full set of the data recieved
        """
        log.exception('Exception in parsing of {}'.format(msg))

    def onCallStarted(self, mid=None, caller_id=None, is_video_call=None, thread_id=None, thread_type=None, ts=None, metadata=None, msg=None):
        """
        .. todo::
            Make this work with private calls

        Called when the client is listening, and somebody starts a call in a group

        :param mid: The action ID
        :param caller_id: The ID of the person who started the call
        :param is_video_call: True if it's video call
        :param thread_id: Thread ID that the action was sent to. See :ref:`intro_threads`
        :param thread_type: Type of thread that the action was sent to. See :ref:`intro_threads`
        :param ts: A timestamp of the action
        :param metadata: Extra metadata about the action
        :param msg: A full set of the data recieved
        :type thread_type: models.ThreadType
        """
        log.info("{} started call in {} ({})".format(caller_id, thread_id, thread_type.name))

    def onCallEnded(self, mid=None, caller_id=None, is_video_call=None, call_duration=None, thread_id=None, thread_type=None, ts=None, metadata=None, msg=None):
        """
        .. todo::
            Make this work with private calls

        Called when the client is listening, and somebody ends a call in a group

        :param mid: The action ID
        :param caller_id: The ID of the person who ended the call
        :param is_video_call: True if it was video call
        :param call_duration: Call duration in seconds
        :param thread_id: Thread ID that the action was sent to. See :ref:`intro_threads`
        :param thread_type: Type of thread that the action was sent to. See :ref:`intro_threads`
        :param ts: A timestamp of the action
        :param metadata: Extra metadata about the action
        :param msg: A full set of the data recieved
        :type thread_type: models.ThreadType
        """
        log.info("{} ended call in {} ({})".format(caller_id, thread_id, thread_type.name))

    def onUserJoinedCall(self, mid=None, joined_id=None, is_video_call=None, thread_id=None, thread_type=None, ts=None, metadata=None, msg=None):
        """
        Called when the client is listening, and somebody joins a group call

        :param mid: The action ID
        :param joined_id: The ID of the person who joined the call
        :param is_video_call: True if it's video call
        :param thread_id: Thread ID that the action was sent to. See :ref:`intro_threads`
        :param thread_type: Type of thread that the action was sent to. See :ref:`intro_threads`
        :param ts: A timestamp of the action
        :param metadata: Extra metadata about the action
        :param msg: A full set of the data recieved
        :type thread_type: models.ThreadType
        """
        log.info("{} joined call in {} ({})".format(joined_id, thread_id, thread_type.name))

    def onPollCreated(self, mid=None, poll=None, author_id=None, thread_id=None, thread_type=None, ts=None, metadata=None, msg=None):
        """
        Called when the client is listening, and somebody creates a group poll

        :param mid: The action ID
        :param poll: Created poll
        :param author_id: The ID of the person who created the poll
        :param thread_id: Thread ID that the action was sent to. See :ref:`intro_threads`
        :param thread_type: Type of thread that the action was sent to. See :ref:`intro_threads`
        :param ts: A timestamp of the action
        :param metadata: Extra metadata about the action
        :param msg: A full set of the data recieved
        :type poll: models.Poll
        :type thread_type: models.ThreadType
        """
        log.info("{} created poll {} in {} ({})".format(author_id, poll, thread_id, thread_type.name))

    def onPollVoted(self, mid=None, poll=None, added_options=None, removed_options=None, author_id=None, thread_id=None, thread_type=None, ts=None, metadata=None, msg=None):
        """
        Called when the client is listening, and somebody votes in a group poll

        :param mid: The action ID
        :param poll: Poll, that user voted in
        :param author_id: The ID of the person who voted in the poll
        :param thread_id: Thread ID that the action was sent to. See :ref:`intro_threads`
        :param thread_type: Type of thread that the action was sent to. See :ref:`intro_threads`
        :param ts: A timestamp of the action
        :param metadata: Extra metadata about the action
        :param msg: A full set of the data recieved
        :type poll: models.Poll
        :type thread_type: models.ThreadType
        """
        log.info("{} voted in poll {} in {} ({})".format(author_id, poll, thread_id, thread_type.name))

    def onPlanCreated(self, mid=None, plan=None, author_id=None, thread_id=None, thread_type=None, ts=None, metadata=None, msg=None):
        """
        Called when the client is listening, and somebody creates a plan

        :param mid: The action ID
        :param plan: Created plan
        :param author_id: The ID of the person who created the plan
        :param thread_id: Thread ID that the action was sent to. See :ref:`intro_threads`
        :param thread_type: Type of thread that the action was sent to. See :ref:`intro_threads`
        :param ts: A timestamp of the action
        :param metadata: Extra metadata about the action
        :param msg: A full set of the data recieved
        :type plan: models.Plan
        :type thread_type: models.ThreadType
        """
        log.info("{} created plan {} in {} ({})".format(author_id, plan, thread_id, thread_type.name))

    def onPlanEnded(self, mid=None, plan=None, thread_id=None, thread_type=None, ts=None, metadata=None, msg=None):
        """
        Called when the client is listening, and a plan ends

        :param mid: The action ID
        :param plan: Ended plan
        :param thread_id: Thread ID that the action was sent to. See :ref:`intro_threads`
        :param thread_type: Type of thread that the action was sent to. See :ref:`intro_threads`
        :param ts: A timestamp of the action
        :param metadata: Extra metadata about the action
        :param msg: A full set of the data recieved
        :type plan: models.Plan
        :type thread_type: models.ThreadType
        """
        log.info("Plan {} has ended in {} ({})".format(plan, thread_id, thread_type.name))

    def onPlanEdited(self, mid=None, plan=None, author_id=None, thread_id=None, thread_type=None, ts=None, metadata=None, msg=None):
        """
        Called when the client is listening, and somebody edits a plan

        :param mid: The action ID
        :param plan: Edited plan
        :param author_id: The ID of the person who edited the plan
        :param thread_id: Thread ID that the action was sent to. See :ref:`intro_threads`
        :param thread_type: Type of thread that the action was sent to. See :ref:`intro_threads`
        :param ts: A timestamp of the action
        :param metadata: Extra metadata about the action
        :param msg: A full set of the data recieved
        :type plan: models.Plan
        :type thread_type: models.ThreadType
        """
        log.info("{} edited plan {} in {} ({})".format(author_id, plan, thread_id, thread_type.name))

    def onPlanDeleted(self, mid=None, plan=None, author_id=None, thread_id=None, thread_type=None, ts=None, metadata=None, msg=None):
        """
        Called when the client is listening, and somebody deletes a plan

        :param mid: The action ID
        :param plan: Deleted plan
        :param author_id: The ID of the person who deleted the plan
        :param thread_id: Thread ID that the action was sent to. See :ref:`intro_threads`
        :param thread_type: Type of thread that the action was sent to. See :ref:`intro_threads`
        :param ts: A timestamp of the action
        :param metadata: Extra metadata about the action
        :param msg: A full set of the data recieved
        :type plan: models.Plan
        :type thread_type: models.ThreadType
        """
        log.info("{} deleted plan {} in {} ({})".format(author_id, plan, thread_id, thread_type.name))

    def onPlanParticipation(self, mid=None, plan=None, take_part=None, author_id=None, thread_id=None, thread_type=None, ts=None, metadata=None, msg=None):
        """
        Called when the client is listening, and somebody takes part in a plan or not

        :param mid: The action ID
        :param plan: Plan
        :param take_part: Whether the person takes part in the plan or not
        :param author_id: The ID of the person who will participate in the plan or not
        :param thread_id: Thread ID that the action was sent to. See :ref:`intro_threads`
        :param thread_type: Type of thread that the action was sent to. See :ref:`intro_threads`
        :param ts: A timestamp of the action
        :param metadata: Extra metadata about the action
        :param msg: A full set of the data recieved
        :type plan: models.Plan
        :type thread_type: models.ThreadType
        """
        if take_part:
            log.info("{} will take part in {} in {} ({})".format(author_id, plan, thread_id, thread_type.name))
        else:
            log.info("{} won't take part in {} in {} ({})".format(author_id, plan, thread_id, thread_type.name))

    """
    END EVENTS
    """
