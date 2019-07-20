# -*- coding: UTF-8 -*-
from __future__ import unicode_literals

import requests
import urllib
from uuid import uuid1
from random import choice
from bs4 import BeautifulSoup as bs
from mimetypes import guess_type
from collections import OrderedDict
from ._util import *
from .models import *
from . import _graphql
from ._state import State
import time
import json

try:
    from urllib.parse import urlparse, parse_qs
except ImportError:
    from urlparse import urlparse, parse_qs


ACONTEXT = {
    "action_history": [
        {"surface": "messenger_chat_tab", "mechanism": "messenger_composer"}
    ]
}


class Client(object):
    """A client for the Facebook Chat (Messenger).

    This is the main class of ``fbchat``, which contains all the methods you use to
    interact with Facebook. You can extend this class, and overwrite the ``on`` methods,
    to provide custom event handling (mainly useful while listening).
    """

    listening = False
    """Whether the client is listening. Used when creating an external event loop to determine when to stop listening"""

    @property
    def ssl_verify(self):
        """Verify ssl certificate, set to False to allow debugging with a proxy."""
        # TODO: Deprecate this
        return self._state._session.verify

    @ssl_verify.setter
    def ssl_verify(self, value):
        self._state._session.verify = value

    @property
    def uid(self):
        """The ID of the client.

        Can be used as ``thread_id``. See :ref:`intro_threads` for more info.
        """
        return self._uid

    def __init__(
        self,
        email,
        password,
        user_agent=None,
        max_tries=5,
        session_cookies=None,
        logging_level=logging.INFO,
    ):
        """Initialize and log in the client.

        :param email: Facebook ``email``, ``id`` or ``phone number``
        :param password: Facebook account password
        :param user_agent: Custom user agent to use when sending requests. If `None`, user agent will be chosen from a premade list
        :param max_tries: Maximum number of times to try logging in
        :param session_cookies: Cookies from a previous session (Will default to login if these are invalid)
        :param logging_level: Configures the `logging level <https://docs.python.org/3/library/logging.html#logging-levels>`_. Defaults to ``logging.INFO``
        :type max_tries: int
        :type session_cookies: dict
        :type logging_level: int
        :raises: FBchatException on failed login
        """
        self._sticky, self._pool = (None, None)
        self._seq = "0"
        self._client_id = hex(int(random() * 2 ** 31))[2:]
        self._default_thread_id = None
        self._default_thread_type = None
        self._pull_channel = 0
        self._markAlive = True
        self._buddylist = dict()

        handler.setLevel(logging_level)

        # If session cookies aren't set, not properly loaded or gives us an invalid session, then do the login
        if (
            not session_cookies
            or not self.setSession(session_cookies, user_agent=user_agent)
            or not self.isLoggedIn()
        ):
            self.login(email, password, max_tries, user_agent=user_agent)

    """
    INTERNAL REQUEST METHODS
    """

    def _generatePayload(self, query):
        if not query:
            query = {}
        query.update(self._state.get_params())
        return query

    def _do_refresh(self):
        # TODO: Raise the error instead, and make the user do the refresh manually
        # It may be a bad idea to do this in an exception handler, if you have a better method, please suggest it!
        log.warning("Refreshing state and resending request")
        self._state = State.from_session(session=self._state._session)

    def _get(self, url, query=None, error_retries=3):
        payload = self._generatePayload(query)
        r = self._state._session.get(prefix_url(url), params=payload)
        content = check_request(r)
        j = to_json(content)
        try:
            handle_payload_error(j)
        except FBchatPleaseRefresh:
            if error_retries > 0:
                self._do_refresh()
                return self._get(url, query=query, error_retries=error_retries - 1)
            raise
        return j

    def _post(self, url, query=None, files=None, as_graphql=False, error_retries=3):
        payload = self._generatePayload(query)
        r = self._state._session.post(prefix_url(url), data=payload, files=files)
        content = check_request(r)
        try:
            if as_graphql:
                return _graphql.response_to_json(content)
            else:
                j = to_json(content)
                # TODO: Remove this, and move it to _payload_post instead
                # We can't yet, since errors raised in here need to be caught below
                handle_payload_error(j)
                return j
        except FBchatPleaseRefresh:
            if error_retries > 0:
                self._do_refresh()
                return self._post(
                    url,
                    query=query,
                    files=files,
                    as_graphql=as_graphql,
                    error_retries=error_retries - 1,
                )
            raise

    def _payload_post(self, url, data, files=None):
        j = self._post(url, data, files=files)
        try:
            return j["payload"]
        except (KeyError, TypeError):
            raise FBchatException("Missing payload: {}".format(j))

    def graphql_requests(self, *queries):
        """
        :param queries: Zero or more dictionaries
        :type queries: dict

        :raises: FBchatException if request failed
        :return: A tuple containing json graphql queries
        :rtype: tuple
        """
        data = {
            "method": "GET",
            "response_format": "json",
            "queries": _graphql.queries_to_json(*queries),
        }
        return tuple(self._post("/api/graphqlbatch/", data, as_graphql=True))

    def graphql_request(self, query):
        """
        Shorthand for ``graphql_requests(query)[0]``

        :raises: FBchatException if request failed
        """
        return self.graphql_requests(query)[0]

    """
    END INTERNAL REQUEST METHODS
    """

    """
    LOGIN METHODS
    """

    def isLoggedIn(self):
        """
        Sends a request to Facebook to check the login status

        :return: True if the client is still logged in
        :rtype: bool
        """
        return self._state.is_logged_in()

    def getSession(self):
        """Retrieves session cookies

        :return: A dictionay containing session cookies
        :rtype: dict
        """
        return self._state.get_cookies()

    def setSession(self, session_cookies, user_agent=None):
        """Loads session cookies

        :param session_cookies: A dictionay containing session cookies
        :type session_cookies: dict
        :return: False if ``session_cookies`` does not contain proper cookies
        :rtype: bool
        """
        try:
            # Load cookies into current session
            state = State.from_cookies(session_cookies, user_agent=user_agent)
        except Exception as e:
            log.exception("Failed loading session")
            return False
        uid = state.get_user_id()
        if uid is None:
            log.warning("Could not find c_user cookie")
            return False
        self._state = state
        self._uid = uid
        return True

    def login(self, email, password, max_tries=5, user_agent=None):
        """
        Uses ``email`` and ``password`` to login the user (If the user is already logged in, this will do a re-login)

        :param email: Facebook ``email`` or ``id`` or ``phone number``
        :param password: Facebook account password
        :param max_tries: Maximum number of times to try logging in
        :type max_tries: int
        :raises: FBchatException on failed login
        """
        self.onLoggingIn(email=email)

        if max_tries < 1:
            raise FBchatUserError("Cannot login: max_tries should be at least one")

        if not (email and password):
            raise FBchatUserError("Email and password not set")

        for i in range(1, max_tries + 1):
            try:
                state = State.login(
                    email,
                    password,
                    on_2fa_callback=self.on2FACode,
                    user_agent=user_agent,
                )
                uid = state.get_user_id()
                if uid is None:
                    raise FBchatException("Could not find user id")
            except Exception:
                if i >= max_tries:
                    raise
                log.exception("Attempt #{} failed, retrying".format(i))
                time.sleep(1)
            else:
                self._state = state
                self._uid = uid
                self.onLoggedIn(email=email)
                break

    def logout(self):
        """
        Safely logs out the client

        :return: True if the action was successful
        :rtype: bool
        """
        if self._state.logout():
            self._state = None
            self._uid = None
            return True
        return False

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
            if self._default_thread_id is not None:
                return self._default_thread_id, self._default_thread_type
            else:
                raise ValueError("Thread ID is not set")
        else:
            return given_thread_id, given_thread_type

    def setDefaultThread(self, thread_id, thread_type):
        """
        Sets default thread to send messages to

        :param thread_id: User/Group ID to default to. See :ref:`intro_threads`
        :param thread_type: See :ref:`intro_threads`
        :type thread_type: ThreadType
        """
        self._default_thread_id = thread_id
        self._default_thread_type = thread_type

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
        params = {"thread_and_message_id": {"thread_id": thread_id, "message_id": mid}}
        return self.graphql_request(_graphql.from_doc_id("1768656253222505", params))

    def fetchThreads(self, thread_location, before=None, after=None, limit=None):
        """
        Get all threads in thread_location.
        Threads will be sorted from newest to oldest.

        :param thread_location: ThreadLocation: INBOX, PENDING, ARCHIVED or OTHER
        :param before: Fetch only thread before this epoch (in ms) (default all threads)
        :param after: Fetch only thread after this epoch (in ms) (default all threads)
        :param limit: The max. amount of threads to fetch (default all threads)
        :return: :class:`Thread` objects
        :rtype: list
        :raises: FBchatException if request failed
        """
        threads = []

        last_thread_timestamp = None
        while True:
            # break if limit is exceeded
            if limit and len(threads) >= limit:
                break

            # fetchThreadList returns at max 20 threads before last_thread_timestamp (included)
            candidates = self.fetchThreadList(
                before=last_thread_timestamp, thread_location=thread_location
            )

            if len(candidates) > 1:
                threads += candidates[1:]
            else:  # End of threads
                break

            last_thread_timestamp = threads[-1].last_message_timestamp

            # FB returns a sorted list of threads
            if (before is not None and int(last_thread_timestamp) > before) or (
                after is not None and int(last_thread_timestamp) < after
            ):
                break

        # Return only threads between before and after (if set)
        if before is not None or after is not None:
            for t in threads:
                last_message_timestamp = int(t.last_message_timestamp)
                if (before is not None and last_message_timestamp > before) or (
                    after is not None and last_message_timestamp < after
                ):
                    threads.remove(t)

        if limit and len(threads) > limit:
            return threads[:limit]

        return threads

    def fetchAllUsersFromThreads(self, threads):
        """
        Get all users involved in threads.

        :param threads: Thread: List of threads to check for users
        :return: :class:`User` objects
        :rtype: list
        :raises: FBchatException if request failed
        """
        users = []
        users_to_fetch = []  # It's more efficient to fetch all users in one request
        for thread in threads:
            if thread.type == ThreadType.USER:
                if thread.uid not in [user.uid for user in users]:
                    users.append(thread)
            elif thread.type == ThreadType.GROUP:
                for user_id in thread.participants:
                    if (
                        user_id not in [user.uid for user in users]
                        and user_id not in users_to_fetch
                    ):
                        users_to_fetch.append(user_id)
        for user_id, user in self.fetchUserInfo(*users_to_fetch).items():
            users.append(user)
        return users

    def fetchAllUsers(self):
        """
        Gets all users the client is currently chatting with

        :return: :class:`User` objects
        :rtype: list
        :raises: FBchatException if request failed
        """
        data = {"viewer": self._uid}
        j = self._payload_post("/chat/user_info_all", data)

        users = []
        for data in j.values():
            if data["type"] in ["user", "friend"]:
                if data["id"] in ["0", 0]:
                    # Skip invalid users
                    continue
                users.append(User._from_all_fetch(data))
        return users

    def searchForUsers(self, name, limit=10):
        """
        Find and get user by his/her name

        :param name: Name of the user
        :param limit: The max. amount of users to fetch
        :return: :class:`User` objects, ordered by relevance
        :rtype: list
        :raises: FBchatException if request failed
        """
        params = {"search": name, "limit": limit}
        j = self.graphql_request(_graphql.from_query(_graphql.SEARCH_USER, params))

        return [User._from_graphql(node) for node in j[name]["users"]["nodes"]]

    def searchForPages(self, name, limit=10):
        """
        Find and get page by its name

        :param name: Name of the page
        :return: :class:`Page` objects, ordered by relevance
        :rtype: list
        :raises: FBchatException if request failed
        """
        params = {"search": name, "limit": limit}
        j = self.graphql_request(_graphql.from_query(_graphql.SEARCH_PAGE, params))

        return [Page._from_graphql(node) for node in j[name]["pages"]["nodes"]]

    def searchForGroups(self, name, limit=10):
        """
        Find and get group thread by its name

        :param name: Name of the group thread
        :param limit: The max. amount of groups to fetch
        :return: :class:`Group` objects, ordered by relevance
        :rtype: list
        :raises: FBchatException if request failed
        """
        params = {"search": name, "limit": limit}
        j = self.graphql_request(_graphql.from_query(_graphql.SEARCH_GROUP, params))

        return [Group._from_graphql(node) for node in j["viewer"]["groups"]["nodes"]]

    def searchForThreads(self, name, limit=10):
        """
        Find and get a thread by its name

        :param name: Name of the thread
        :param limit: The max. amount of groups to fetch
        :return: :class:`User`, :class:`Group` and :class:`Page` objects, ordered by relevance
        :rtype: list
        :raises: FBchatException if request failed
        """
        params = {"search": name, "limit": limit}
        j = self.graphql_request(_graphql.from_query(_graphql.SEARCH_THREAD, params))

        rtn = []
        for node in j[name]["threads"]["nodes"]:
            if node["__typename"] == "User":
                rtn.append(User._from_graphql(node))
            elif node["__typename"] == "MessageThread":
                # MessageThread => Group thread
                rtn.append(Group._from_graphql(node))
            elif node["__typename"] == "Page":
                rtn.append(Page._from_graphql(node))
            elif node["__typename"] == "Group":
                # We don't handle Facebook "Groups"
                pass
            else:
                log.warning(
                    "Unknown type {} in {}".format(repr(node["__typename"]), node)
                )

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
        :rtype: typing.Iterable
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
        j = self._payload_post("/ajax/mercury/search_snippets.php?dpr=1", data)

        result = j["search_snippets"][query]
        snippets = result[thread_id]["snippets"] if result.get(thread_id) else []
        for snippet in snippets:
            yield snippet["message_id"]

    def searchForMessages(self, query, offset=0, limit=5, thread_id=None):
        """
        Find and get :class:`Message` objects by query

        .. warning::
            This method sends request for every found message ID.

        :param query: Text to search for
        :param offset: Number of messages to skip
        :param limit: Max. number of messages to retrieve
        :param thread_id: User/Group ID to search in. See :ref:`intro_threads`
        :type offset: int
        :type limit: int
        :return: Found :class:`Message` objects
        :rtype: typing.Iterable
        :raises: FBchatException if request failed
        """
        message_ids = self.searchForMessageIDs(
            query, offset=offset, limit=limit, thread_id=thread_id
        )
        for mid in message_ids:
            yield self.fetchMessageInfo(mid, thread_id)

    def search(self, query, fetch_messages=False, thread_limit=5, message_limit=5):
        """
        Searches for messages in all threads

        :param query: Text to search for
        :param fetch_messages: Whether to fetch :class:`Message` objects or IDs only
        :param thread_limit: Max. number of threads to retrieve
        :param message_limit: Max. number of messages to retrieve
        :type thread_limit: int
        :type message_limit: int
        :return: Dictionary with thread IDs as keys and iterables to get messages as values
        :rtype: typing.Dict[str, typing.Iterable]
        :raises: FBchatException if request failed
        """
        data = {"query": query, "snippetLimit": thread_limit}
        j = self._payload_post("/ajax/mercury/search_snippets.php?dpr=1", data)
        result = j["search_snippets"][query]

        if not result:
            return {}

        if fetch_messages:
            search_method = self.searchForMessages
        else:
            search_method = self.searchForMessageIDs

        return {
            thread_id: search_method(query, limit=message_limit, thread_id=thread_id)
            for thread_id in result
        }

    def _fetchInfo(self, *ids):
        data = {"ids[{}]".format(i): _id for i, _id in enumerate(ids)}
        j = self._payload_post("/chat/user_info/", data)

        if j.get("profiles") is None:
            raise FBchatException("No users/pages returned: {}".format(j))

        entries = {}
        for _id in j["profiles"]:
            k = j["profiles"][_id]
            if k["type"] in ["user", "friend"]:
                entries[_id] = {
                    "id": _id,
                    "type": ThreadType.USER,
                    "url": k.get("uri"),
                    "first_name": k.get("firstName"),
                    "is_viewer_friend": k.get("is_friend"),
                    "gender": k.get("gender"),
                    "profile_picture": {"uri": k.get("thumbSrc")},
                    "name": k.get("name"),
                }
            elif k["type"] == "page":
                entries[_id] = {
                    "id": _id,
                    "type": ThreadType.PAGE,
                    "url": k.get("uri"),
                    "profile_picture": {"uri": k.get("thumbSrc")},
                    "name": k.get("name"),
                }
            else:
                raise FBchatException(
                    "{} had an unknown thread type: {}".format(_id, k)
                )

        log.debug(entries)
        return entries

    def fetchUserInfo(self, *user_ids):
        """
        Get users' info from IDs, unordered

        .. warning::
            Sends two requests, to fetch all available info!

        :param user_ids: One or more user ID(s) to query
        :return: :class:`User` objects, labeled by their ID
        :rtype: dict
        :raises: FBchatException if request failed
        """
        threads = self.fetchThreadInfo(*user_ids)
        users = {}
        for id_, thread in threads.items():
            if thread.type == ThreadType.USER:
                users[id_] = thread
            else:
                raise FBchatUserError("Thread {} was not a user".format(thread))

        return users

    def fetchPageInfo(self, *page_ids):
        """
        Get pages' info from IDs, unordered

        .. warning::
            Sends two requests, to fetch all available info!

        :param page_ids: One or more page ID(s) to query
        :return: :class:`Page` objects, labeled by their ID
        :rtype: dict
        :raises: FBchatException if request failed
        """
        threads = self.fetchThreadInfo(*page_ids)
        pages = {}
        for id_, thread in threads.items():
            if thread.type == ThreadType.PAGE:
                pages[id_] = thread
            else:
                raise FBchatUserError("Thread {} was not a page".format(thread))

        return pages

    def fetchGroupInfo(self, *group_ids):
        """
        Get groups' info from IDs, unordered

        :param group_ids: One or more group ID(s) to query
        :return: :class:`Group` objects, labeled by their ID
        :rtype: dict
        :raises: FBchatException if request failed
        """
        threads = self.fetchThreadInfo(*group_ids)
        groups = {}
        for id_, thread in threads.items():
            if thread.type == ThreadType.GROUP:
                groups[id_] = thread
            else:
                raise FBchatUserError("Thread {} was not a group".format(thread))

        return groups

    def fetchThreadInfo(self, *thread_ids):
        """
        Get threads' info from IDs, unordered

        .. warning::
            Sends two requests if users or pages are present, to fetch all available info!

        :param thread_ids: One or more thread ID(s) to query
        :return: :class:`Thread` objects, labeled by their ID
        :rtype: dict
        :raises: FBchatException if request failed
        """
        queries = []
        for thread_id in thread_ids:
            params = {
                "id": thread_id,
                "message_limit": 0,
                "load_messages": False,
                "load_read_receipts": False,
                "before": None,
            }
            queries.append(_graphql.from_doc_id("2147762685294928", params))

        j = self.graphql_requests(*queries)

        for i, entry in enumerate(j):
            if entry.get("message_thread") is None:
                # If you don't have an existing thread with this person, attempt to retrieve user data anyways
                j[i]["message_thread"] = {
                    "thread_key": {"other_user_id": thread_ids[i]},
                    "thread_type": "ONE_TO_ONE",
                }

        pages_and_user_ids = [
            k["message_thread"]["thread_key"]["other_user_id"]
            for k in j
            if k["message_thread"].get("thread_type") == "ONE_TO_ONE"
        ]
        pages_and_users = {}
        if len(pages_and_user_ids) != 0:
            pages_and_users = self._fetchInfo(*pages_and_user_ids)

        rtn = {}
        for i, entry in enumerate(j):
            entry = entry["message_thread"]
            if entry.get("thread_type") == "GROUP":
                _id = entry["thread_key"]["thread_fbid"]
                rtn[_id] = Group._from_graphql(entry)
            elif entry.get("thread_type") == "ONE_TO_ONE":
                _id = entry["thread_key"]["other_user_id"]
                if pages_and_users.get(_id) is None:
                    raise FBchatException("Could not fetch thread {}".format(_id))
                entry.update(pages_and_users[_id])
                if entry["type"] == ThreadType.USER:
                    rtn[_id] = User._from_graphql(entry)
                else:
                    rtn[_id] = Page._from_graphql(entry)
            else:
                raise FBchatException(
                    "{} had an unknown thread type: {}".format(thread_ids[i], entry)
                )

        return rtn

    def fetchThreadMessages(self, thread_id=None, limit=20, before=None):
        """
        Get the last messages in a thread

        :param thread_id: User/Group ID to get messages from. See :ref:`intro_threads`
        :param limit: Max. number of messages to retrieve
        :param before: A timestamp, indicating from which point to retrieve messages
        :type limit: int
        :type before: int
        :return: :class:`Message` objects
        :rtype: list
        :raises: FBchatException if request failed
        """
        thread_id, thread_type = self._getThread(thread_id, None)

        params = {
            "id": thread_id,
            "message_limit": limit,
            "load_messages": True,
            "load_read_receipts": True,
            "before": before,
        }
        j = self.graphql_request(_graphql.from_doc_id("1860982147341344", params))

        if j.get("message_thread") is None:
            raise FBchatException("Could not fetch thread {}: {}".format(thread_id, j))

        messages = [
            Message._from_graphql(message)
            for message in j["message_thread"]["messages"]["nodes"]
        ]
        messages.reverse()

        read_receipts = j["message_thread"]["read_receipts"]["nodes"]

        for message in messages:
            for receipt in read_receipts:
                if int(receipt["watermark"]) >= int(message.timestamp):
                    message.read_by.append(receipt["actor"]["id"])

        return messages

    def fetchThreadList(
        self, offset=None, limit=20, thread_location=ThreadLocation.INBOX, before=None
    ):
        """Get thread list of your facebook account

        :param offset: Deprecated. Do not use!
        :param limit: Max. number of threads to retrieve. Capped at 20
        :param thread_location: ThreadLocation: INBOX, PENDING, ARCHIVED or OTHER
        :param before: A timestamp (in milliseconds), indicating from which point to retrieve threads
        :type limit: int
        :type before: int
        :return: :class:`Thread` objects
        :rtype: list
        :raises: FBchatException if request failed
        """
        if offset is not None:
            log.warning(
                "Using `offset` in `fetchThreadList` is no longer supported, "
                "since Facebook migrated to the use of GraphQL in this request. "
                "Use `before` instead."
            )

        if limit > 20 or limit < 1:
            raise FBchatUserError("`limit` should be between 1 and 20")

        if thread_location in ThreadLocation:
            loc_str = thread_location.value
        else:
            raise FBchatUserError('"thread_location" must be a value of ThreadLocation')

        params = {
            "limit": limit,
            "tags": [loc_str],
            "before": before,
            "includeDeliveryReceipts": True,
            "includeSeqID": False,
        }
        j = self.graphql_request(_graphql.from_doc_id("1349387578499440", params))

        rtn = []
        for node in j["viewer"]["message_threads"]["nodes"]:
            _type = node.get("thread_type")
            if _type == "GROUP":
                rtn.append(Group._from_graphql(node))
            elif _type == "ONE_TO_ONE":
                rtn.append(User._from_thread_fetch(node))
            else:
                raise FBchatException(
                    "Unknown thread type: {}, with data: {}".format(_type, node)
                )
        return rtn

    def fetchUnread(self):
        """
        Get the unread thread list

        :return: List of unread thread ids
        :rtype: list
        :raises: FBchatException if request failed
        """
        form = {
            "folders[0]": "inbox",
            "client": "mercury",
            "last_action_timestamp": now() - 60 * 1000
            # 'last_action_timestamp': 0
        }
        j = self._payload_post("/ajax/mercury/unread_threads.php", form)

        result = j["unread_thread_fbids"][0]
        return result["thread_fbids"] + result["other_user_fbids"]

    def fetchUnseen(self):
        """
        Get the unseen (new) thread list

        :return: List of unseen thread ids
        :rtype: list
        :raises: FBchatException if request failed
        """
        j = self._payload_post("/mercury/unseen_thread_ids/", None)

        result = j["unseen_thread_fbids"][0]
        return result["thread_fbids"] + result["other_user_fbids"]

    def fetchImageUrl(self, image_id):
        """Fetches the url to the original image from an image attachment ID

        :param image_id: The image you want to fethc
        :type image_id: str
        :return: An url where you can download the original image
        :rtype: str
        :raises: FBchatException if request failed
        """
        image_id = str(image_id)
        data = {"photo_id": str(image_id)}
        j = self._post("/mercury/attachments/photo/", data)

        url = get_jsmods_require(j, 3)
        if url is None:
            raise FBchatException("Could not fetch image url from: {}".format(j))
        return url

    def fetchMessageInfo(self, mid, thread_id=None):
        """
        Fetches :class:`Message` object from the message id

        :param mid: Message ID to fetch from
        :param thread_id: User/Group ID to get message info from. See :ref:`intro_threads`
        :return: :class:`Message` object
        :rtype: Message
        :raises: FBchatException if request failed
        """
        thread_id, thread_type = self._getThread(thread_id, None)
        message_info = self._forcedFetch(thread_id, mid).get("message")
        return Message._from_graphql(message_info)

    def fetchPollOptions(self, poll_id):
        """
        Fetches list of :class:`PollOption` objects from the poll id

        :param poll_id: Poll ID to fetch from
        :rtype: list
        :raises: FBchatException if request failed
        """
        data = {"question_id": poll_id}
        j = self._payload_post("/ajax/mercury/get_poll_options", data)
        return [PollOption._from_graphql(m) for m in j]

    def fetchPlanInfo(self, plan_id):
        """
        Fetches a :class:`Plan` object from the plan id

        :param plan_id: Plan ID to fetch from
        :return: :class:`Plan` object
        :rtype: Plan
        :raises: FBchatException if request failed
        """
        data = {"event_reminder_id": plan_id}
        j = self._payload_post("/ajax/eventreminder", data)
        return Plan._from_fetch(j)

    def _getPrivateData(self):
        j = self.graphql_request(_graphql.from_doc_id("1868889766468115", {}))
        return j["viewer"]

    def getPhoneNumbers(self):
        """
        Fetches a list of user phone numbers.

        :return: List of phone numbers
        :rtype: list
        """
        data = self._getPrivateData()
        return [
            j["phone_number"]["universal_number"] for j in data["user"]["all_phones"]
        ]

    def getEmails(self):
        """
        Fetches a list of user emails.

        :return: List of emails
        :rtype: list
        """
        data = self._getPrivateData()
        return [j["display_email"] for j in data["all_emails"]]

    def getUserActiveStatus(self, user_id):
        """
        Gets friend active status as an :class:`ActiveStatus` object.
        Returns ``None`` if status isn't known.

        .. warning::
            Only works when listening.

        :param user_id: ID of the user
        :return: Given user active status
        :rtype: ActiveStatus
        """
        return self._buddylist.get(str(user_id))

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
            "client": "mercury",
            "author": "fbid:{}".format(self._uid),
            "timestamp": timestamp,
            "source": "source:chat:web",
            "offline_threading_id": messageAndOTID,
            "message_id": messageAndOTID,
            "threading_id": generateMessageID(self._client_id),
            "ephemeral_ttl_mode:": "0",
        }

        # Set recipient
        if thread_type in [ThreadType.USER, ThreadType.PAGE]:
            data["other_user_fbid"] = thread_id
        elif thread_type == ThreadType.GROUP:
            data["thread_fbid"] = thread_id

        if message is None:
            message = Message()

        if message.text or message.sticker or message.emoji_size:
            data["action_type"] = "ma-type:user-generated-message"

        if message.text:
            data["body"] = message.text

        for i, mention in enumerate(message.mentions):
            data["profile_xmd[{}][id]".format(i)] = mention.thread_id
            data["profile_xmd[{}][offset]".format(i)] = mention.offset
            data["profile_xmd[{}][length]".format(i)] = mention.length
            data["profile_xmd[{}][type]".format(i)] = "p"

        if message.emoji_size:
            if message.text:
                data["tags[0]"] = "hot_emoji_size:" + message.emoji_size.name.lower()
            else:
                data["sticker_id"] = message.emoji_size.value

        if message.sticker:
            data["sticker_id"] = message.sticker.uid

        if message.quick_replies:
            xmd = {"quick_replies": []}
            for quick_reply in message.quick_replies:
                q = dict()
                q["content_type"] = quick_reply._type
                q["payload"] = quick_reply.payload
                q["external_payload"] = quick_reply.external_payload
                q["data"] = quick_reply.data
                if quick_reply.is_response:
                    q["ignore_for_webhook"] = False
                if isinstance(quick_reply, QuickReplyText):
                    q["title"] = quick_reply.title
                if not isinstance(quick_reply, QuickReplyLocation):
                    q["image_url"] = quick_reply.image_url
                xmd["quick_replies"].append(q)
            if len(message.quick_replies) == 1 and message.quick_replies[0].is_response:
                xmd["quick_replies"] = xmd["quick_replies"][0]
            data["platform_xmd"] = json.dumps(xmd)

        if message.reply_to_id:
            data["replied_to_message_id"] = message.reply_to_id

        return data

    def _doSendRequest(self, data, get_thread_id=False):
        """Sends the data to `SendURL`, and returns the message ID or None on failure"""
        j = self._post("/messaging/send/", data)

        # update JS token if received in response
        fb_dtsg = get_jsmods_require(j, 2)
        if fb_dtsg is not None:
            self._state.fb_dtsg = fb_dtsg

        try:
            message_ids = [
                (action["message_id"], action["thread_fbid"])
                for action in j["payload"]["actions"]
                if "message_id" in action
            ]
            if len(message_ids) != 1:
                log.warning("Got multiple message ids' back: {}".format(message_ids))
            if get_thread_id:
                return message_ids[0]
            else:
                return message_ids[0][0]
        except (KeyError, IndexError, TypeError) as e:
            raise FBchatException(
                "Error when sending message: "
                "No message IDs could be found: {}".format(j)
            )

    def send(self, message, thread_id=None, thread_type=ThreadType.USER):
        """
        Sends a message to a thread

        :param message: Message to send
        :param thread_id: User/Group ID to send to. See :ref:`intro_threads`
        :param thread_type: See :ref:`intro_threads`
        :type message: Message
        :type thread_type: ThreadType
        :return: :ref:`Message ID <intro_message_ids>` of the sent message
        :raises: FBchatException if request failed
        """
        thread_id, thread_type = self._getThread(thread_id, thread_type)
        data = self._getSendData(
            message=message, thread_id=thread_id, thread_type=thread_type
        )
        return self._doSendRequest(data)

    def sendMessage(self, message, thread_id=None, thread_type=ThreadType.USER):
        """
        Deprecated. Use :func:`fbchat.Client.send` instead
        """
        return self.send(
            Message(text=message), thread_id=thread_id, thread_type=thread_type
        )

    def sendEmoji(
        self,
        emoji=None,
        size=EmojiSize.SMALL,
        thread_id=None,
        thread_type=ThreadType.USER,
    ):
        """
        Deprecated. Use :func:`fbchat.Client.send` instead
        """
        return self.send(
            Message(text=emoji, emoji_size=size),
            thread_id=thread_id,
            thread_type=thread_type,
        )

    def wave(self, wave_first=True, thread_id=None, thread_type=None):
        """
        Says hello with a wave to a thread!

        :param wave_first: Whether to wave first or wave back
        :param thread_id: User/Group ID to send to. See :ref:`intro_threads`
        :param thread_type: See :ref:`intro_threads`
        :type thread_type: ThreadType
        :return: :ref:`Message ID <intro_message_ids>` of the sent message
        :raises: FBchatException if request failed
        """
        thread_id, thread_type = self._getThread(thread_id, thread_type)
        data = self._getSendData(thread_id=thread_id, thread_type=thread_type)
        data["action_type"] = "ma-type:user-generated-message"
        data["lightweight_action_attachment[lwa_state]"] = (
            "INITIATED" if wave_first else "RECIPROCATED"
        )
        data["lightweight_action_attachment[lwa_type]"] = "WAVE"
        if thread_type == ThreadType.USER:
            data["specific_to_list[0]"] = "fbid:{}".format(thread_id)
        return self._doSendRequest(data)

    def quickReply(self, quick_reply, payload=None, thread_id=None, thread_type=None):
        """
        Replies to a chosen quick reply

        :param quick_reply: Quick reply to reply to
        :param payload: Optional answer to the quick reply
        :param thread_id: User/Group ID to send to. See :ref:`intro_threads`
        :param thread_type: See :ref:`intro_threads`
        :type quick_reply: QuickReply
        :type thread_type: ThreadType
        :return: :ref:`Message ID <intro_message_ids>` of the sent message
        :raises: FBchatException if request failed
        """
        quick_reply.is_response = True
        if isinstance(quick_reply, QuickReplyText):
            return self.send(
                Message(text=quick_reply.title, quick_replies=[quick_reply])
            )
        elif isinstance(quick_reply, QuickReplyLocation):
            if not isinstance(payload, LocationAttachment):
                raise ValueError(
                    "Payload must be an instance of `fbchat.LocationAttachment`"
                )
            return self.sendLocation(
                payload, thread_id=thread_id, thread_type=thread_type
            )
        elif isinstance(quick_reply, QuickReplyEmail):
            if not payload:
                payload = self.getEmails()[0]
            quick_reply.external_payload = quick_reply.payload
            quick_reply.payload = payload
            return self.send(Message(text=payload, quick_replies=[quick_reply]))
        elif isinstance(quick_reply, QuickReplyPhoneNumber):
            if not payload:
                payload = self.getPhoneNumbers()[0]
            quick_reply.external_payload = quick_reply.payload
            quick_reply.payload = payload
            return self.send(Message(text=payload, quick_replies=[quick_reply]))

    def unsend(self, mid):
        """
        Unsends a message (removes for everyone)

        :param mid: :ref:`Message ID <intro_message_ids>` of the message to unsend
        """
        data = {"message_id": mid}
        j = self._payload_post("/messaging/unsend_message/?dpr=1", data)

    def _sendLocation(
        self, location, current=True, message=None, thread_id=None, thread_type=None
    ):
        thread_id, thread_type = self._getThread(thread_id, thread_type)
        data = self._getSendData(
            message=message, thread_id=thread_id, thread_type=thread_type
        )
        data["action_type"] = "ma-type:user-generated-message"
        data["location_attachment[coordinates][latitude]"] = location.latitude
        data["location_attachment[coordinates][longitude]"] = location.longitude
        data["location_attachment[is_current_location]"] = current
        return self._doSendRequest(data)

    def sendLocation(self, location, message=None, thread_id=None, thread_type=None):
        """
        Sends a given location to a thread as the user's current location

        :param location: Location to send
        :param message: Additional message
        :param thread_id: User/Group ID to send to. See :ref:`intro_threads`
        :param thread_type: See :ref:`intro_threads`
        :type location: LocationAttachment
        :type message: Message
        :type thread_type: ThreadType
        :return: :ref:`Message ID <intro_message_ids>` of the sent message
        :raises: FBchatException if request failed
        """
        self._sendLocation(
            location=location,
            current=True,
            message=message,
            thread_id=thread_id,
            thread_type=thread_type,
        )

    def sendPinnedLocation(
        self, location, message=None, thread_id=None, thread_type=None
    ):
        """
        Sends a given location to a thread as a pinned location

        :param location: Location to send
        :param message: Additional message
        :param thread_id: User/Group ID to send to. See :ref:`intro_threads`
        :param thread_type: See :ref:`intro_threads`
        :type location: LocationAttachment
        :type message: Message
        :type thread_type: ThreadType
        :return: :ref:`Message ID <intro_message_ids>` of the sent message
        :raises: FBchatException if request failed
        """
        self._sendLocation(
            location=location,
            current=False,
            message=message,
            thread_id=thread_id,
            thread_type=thread_type,
        )

    def _upload(self, files, voice_clip=False):
        """
        Uploads files to Facebook

        `files` should be a list of files that requests can upload, see:
        http://docs.python-requests.org/en/master/api/#requests.request

        Returns a list of tuples with a file's ID and mimetype
        """
        file_dict = {"upload_{}".format(i): f for i, f in enumerate(files)}

        data = {"voice_clip": voice_clip}

        j = self._payload_post(
            "https://upload.facebook.com/ajax/mercury/upload.php", data, files=file_dict
        )

        if len(j["metadata"]) != len(files):
            raise FBchatException(
                "Some files could not be uploaded: {}, {}".format(j, files)
            )

        return [
            (data[mimetype_to_key(data["filetype"])], data["filetype"])
            for data in j["metadata"]
        ]

    def _sendFiles(
        self, files, message=None, thread_id=None, thread_type=ThreadType.USER
    ):
        """
        Sends files from file IDs to a thread

        `files` should be a list of tuples, with a file's ID and mimetype
        """
        thread_id, thread_type = self._getThread(thread_id, thread_type)
        data = self._getSendData(
            message=self._oldMessage(message),
            thread_id=thread_id,
            thread_type=thread_type,
        )

        data["action_type"] = "ma-type:user-generated-message"
        data["has_attachment"] = True

        for i, (file_id, mimetype) in enumerate(files):
            data["{}s[{}]".format(mimetype_to_key(mimetype), i)] = file_id

        return self._doSendRequest(data)

    def sendRemoteFiles(
        self, file_urls, message=None, thread_id=None, thread_type=ThreadType.USER
    ):
        """
        Sends files from URLs to a thread

        :param file_urls: URLs of files to upload and send
        :param message: Additional message
        :param thread_id: User/Group ID to send to. See :ref:`intro_threads`
        :param thread_type: See :ref:`intro_threads`
        :type thread_type: ThreadType
        :return: :ref:`Message ID <intro_message_ids>` of the sent files
        :raises: FBchatException if request failed
        """
        file_urls = require_list(file_urls)
        files = self._upload(get_files_from_urls(file_urls))
        return self._sendFiles(
            files=files, message=message, thread_id=thread_id, thread_type=thread_type
        )

    def sendLocalFiles(
        self, file_paths, message=None, thread_id=None, thread_type=ThreadType.USER
    ):
        """
        Sends local files to a thread

        :param file_paths: Paths of files to upload and send
        :param message: Additional message
        :param thread_id: User/Group ID to send to. See :ref:`intro_threads`
        :param thread_type: See :ref:`intro_threads`
        :type thread_type: ThreadType
        :return: :ref:`Message ID <intro_message_ids>` of the sent files
        :raises: FBchatException if request failed
        """
        file_paths = require_list(file_paths)
        with get_files_from_paths(file_paths) as x:
            files = self._upload(x)
        return self._sendFiles(
            files=files, message=message, thread_id=thread_id, thread_type=thread_type
        )

    def sendRemoteVoiceClips(
        self, clip_urls, message=None, thread_id=None, thread_type=ThreadType.USER
    ):
        """
        Sends voice clips from URLs to a thread

        :param clip_urls: URLs of clips to upload and send
        :param message: Additional message
        :param thread_id: User/Group ID to send to. See :ref:`intro_threads`
        :param thread_type: See :ref:`intro_threads`
        :type thread_type: ThreadType
        :return: :ref:`Message ID <intro_message_ids>` of the sent files
        :raises: FBchatException if request failed
        """
        clip_urls = require_list(clip_urls)
        files = self._upload(get_files_from_urls(clip_urls), voice_clip=True)
        return self._sendFiles(
            files=files, message=message, thread_id=thread_id, thread_type=thread_type
        )

    def sendLocalVoiceClips(
        self, clip_paths, message=None, thread_id=None, thread_type=ThreadType.USER
    ):
        """
        Sends local voice clips to a thread

        :param clip_paths: Paths of clips to upload and send
        :param message: Additional message
        :param thread_id: User/Group ID to send to. See :ref:`intro_threads`
        :param thread_type: See :ref:`intro_threads`
        :type thread_type: ThreadType
        :return: :ref:`Message ID <intro_message_ids>` of the sent files
        :raises: FBchatException if request failed
        """
        clip_paths = require_list(clip_paths)
        with get_files_from_paths(clip_paths) as x:
            files = self._upload(x, voice_clip=True)
        return self._sendFiles(
            files=files, message=message, thread_id=thread_id, thread_type=thread_type
        )

    def sendImage(
        self,
        image_id,
        message=None,
        thread_id=None,
        thread_type=ThreadType.USER,
        is_gif=False,
    ):
        """Deprecated."""
        if is_gif:
            mimetype = "image/gif"
        else:
            mimetype = "image/png"
        return self._sendFiles(
            files=[(image_id, mimetype)],
            message=message,
            thread_id=thread_id,
            thread_type=thread_type,
        )

    def sendRemoteImage(
        self, image_url, message=None, thread_id=None, thread_type=ThreadType.USER
    ):
        """
        Deprecated. Use :func:`fbchat.Client.sendRemoteFiles` instead
        """
        return self.sendRemoteFiles(
            file_urls=[image_url],
            message=message,
            thread_id=thread_id,
            thread_type=thread_type,
        )

    def sendLocalImage(
        self, image_path, message=None, thread_id=None, thread_type=ThreadType.USER
    ):
        """
        Deprecated. Use :func:`fbchat.Client.sendLocalFiles` instead
        """
        return self.sendLocalFiles(
            file_paths=[image_path],
            message=message,
            thread_id=thread_id,
            thread_type=thread_type,
        )

    def forwardAttachment(self, attachment_id, thread_id=None):
        """
        Forwards an attachment

        :param attachment_id: Attachment ID to forward
        :param thread_id: User/Group ID to send to. See :ref:`intro_threads`
        :raises: FBchatException if request failed
        """
        thread_id, thread_type = self._getThread(thread_id, None)
        data = {
            "attachment_id": attachment_id,
            "recipient_map[{}]".format(generateOfflineThreadingID()): thread_id,
        }
        j = self._payload_post("/mercury/attachments/forward/", data)
        if not j.get("success"):
            raise FBchatFacebookError(
                "Failed forwarding attachment: {}".format(j["error"]),
                fb_error_message=j["error"],
            )

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

        for i, user_id in enumerate(user_ids + [self._uid]):
            data["specific_to_list[{}]".format(i)] = "fbid:{}".format(user_id)

        message_id, thread_id = self._doSendRequest(data, get_thread_id=True)
        if not thread_id:
            raise FBchatException(
                "Error when creating group: No thread_id could be found"
            )
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

        data["action_type"] = "ma-type:log-message"
        data["log_message_type"] = "log:subscribe"

        user_ids = require_list(user_ids)

        for i, user_id in enumerate(user_ids):
            if user_id == self._uid:
                raise FBchatUserError(
                    "Error when adding users: Cannot add self to group thread"
                )
            else:
                data[
                    "log_message_data[added_participants][{}]".format(i)
                ] = "fbid:{}".format(user_id)

        return self._doSendRequest(data)

    def removeUserFromGroup(self, user_id, thread_id=None):
        """
        Removes users from a group.

        :param user_id: User ID to remove
        :param thread_id: Group ID to remove people from. See :ref:`intro_threads`
        :raises: FBchatException if request failed
        """
        thread_id, thread_type = self._getThread(thread_id, None)

        data = {"uid": user_id, "tid": thread_id}
        j = self._payload_post("/chat/remove_participants/", data)

    def _adminStatus(self, admin_ids, admin, thread_id=None):
        thread_id, thread_type = self._getThread(thread_id, None)

        data = {"add": admin, "thread_fbid": thread_id}

        admin_ids = require_list(admin_ids)

        for i, admin_id in enumerate(admin_ids):
            data["admin_ids[{}]".format(i)] = str(admin_id)

        j = self._payload_post("/messaging/save_admins/?dpr=1", data)

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

        data = {"set_mode": int(require_admin_approval), "thread_fbid": thread_id}
        j = self._payload_post("/messaging/set_approval_mode/?dpr=1", data)

    def _usersApproval(self, user_ids, approve, thread_id=None):
        thread_id, thread_type = self._getThread(thread_id, None)

        user_ids = list(require_list(user_ids))

        data = {
            "client_mutation_id": "0",
            "actor_id": self._uid,
            "thread_fbid": thread_id,
            "user_ids": user_ids,
            "response": "ACCEPT" if approve else "DENY",
            "surface": "ADMIN_MODEL_APPROVAL_CENTER",
        }
        j = self.graphql_request(
            _graphql.from_doc_id("1574519202665847", {"data": data})
        )

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

        data = {"thread_image_id": image_id, "thread_id": thread_id}

        j = self._payload_post("/messaging/set_thread_image/?dpr=1", data)
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
        :type thread_type: ThreadType
        :raises: FBchatException if request failed
        """
        thread_id, thread_type = self._getThread(thread_id, thread_type)

        if thread_type == ThreadType.USER:
            # The thread is a user, so we change the user's nickname
            return self.changeNickname(
                title, thread_id, thread_id=thread_id, thread_type=thread_type
            )

        data = {"thread_name": title, "thread_id": thread_id}
        j = self._payload_post("/messaging/set_thread_name/?dpr=1", data)

    def changeNickname(
        self, nickname, user_id, thread_id=None, thread_type=ThreadType.USER
    ):
        """
        Changes the nickname of a user in a thread

        :param nickname: New nickname
        :param user_id: User that will have their nickname changed
        :param thread_id: User/Group ID to change color of. See :ref:`intro_threads`
        :param thread_type: See :ref:`intro_threads`
        :type thread_type: ThreadType
        :raises: FBchatException if request failed
        """
        thread_id, thread_type = self._getThread(thread_id, thread_type)

        data = {
            "nickname": nickname,
            "participant_id": user_id,
            "thread_or_other_fbid": thread_id,
        }
        j = self._payload_post(
            "/messaging/save_thread_nickname/?source=thread_settings&dpr=1", data
        )

    def changeThreadColor(self, color, thread_id=None):
        """
        Changes thread color

        :param color: New thread color
        :param thread_id: User/Group ID to change color of. See :ref:`intro_threads`
        :type color: ThreadColor
        :raises: FBchatException if request failed
        """
        thread_id, thread_type = self._getThread(thread_id, None)

        data = {
            "color_choice": color.value if color != ThreadColor.MESSENGER_BLUE else "",
            "thread_or_other_fbid": thread_id,
        }
        j = self._payload_post(
            "/messaging/save_thread_color/?source=thread_settings&dpr=1", data
        )

    def changeThreadEmoji(self, emoji, thread_id=None):
        """
        Changes thread color

        Trivia: While changing the emoji, the Facebook web client actually sends multiple different requests, though only this one is required to make the change

        :param color: New thread emoji
        :param thread_id: User/Group ID to change emoji of. See :ref:`intro_threads`
        :raises: FBchatException if request failed
        """
        thread_id, thread_type = self._getThread(thread_id, None)

        data = {"emoji_choice": emoji, "thread_or_other_fbid": thread_id}
        j = self._payload_post(
            "/messaging/save_thread_emoji/?source=thread_settings&dpr=1", data
        )

    def reactToMessage(self, message_id, reaction):
        """
        Reacts to a message, or removes reaction

        :param message_id: :ref:`Message ID <intro_message_ids>` to react to
        :param reaction: Reaction emoji to use, if None removes reaction
        :type reaction: MessageReaction or None
        :raises: FBchatException if request failed
        """
        data = {
            "action": "ADD_REACTION" if reaction else "REMOVE_REACTION",
            "client_mutation_id": "1",
            "actor_id": self._uid,
            "message_id": str(message_id),
            "reaction": reaction.value if reaction else None,
        }
        data = {"doc_id": 1491398900900362, "variables": json.dumps({"data": data})}
        j = self._payload_post("/webgraphql/mutation", data)
        handle_graphql_errors(j)

    def createPlan(self, plan, thread_id=None):
        """
        Sets a plan

        :param plan: Plan to set
        :param thread_id: User/Group ID to send plan to. See :ref:`intro_threads`
        :type plan: Plan
        :raises: FBchatException if request failed
        """
        thread_id, thread_type = self._getThread(thread_id, None)

        data = {
            "event_type": "EVENT",
            "event_time": plan.time,
            "title": plan.title,
            "thread_id": thread_id,
            "location_id": plan.location_id or "",
            "location_name": plan.location or "",
            "acontext": ACONTEXT,
        }
        j = self._payload_post("/ajax/eventreminder/create", data)
        if "error" in j:
            raise FBchatFacebookError(
                "Failed creating plan: {}".format(j["error"]),
                fb_error_message=j["error"],
            )

    def editPlan(self, plan, new_plan):
        """
        Edits a plan

        :param plan: Plan to edit
        :param new_plan: New plan
        :type plan: Plan
        :raises: FBchatException if request failed
        """
        data = {
            "event_reminder_id": plan.uid,
            "delete": "false",
            "date": new_plan.time,
            "location_name": new_plan.location or "",
            "location_id": new_plan.location_id or "",
            "title": new_plan.title,
            "acontext": ACONTEXT,
        }
        j = self._payload_post("/ajax/eventreminder/submit", data)

    def deletePlan(self, plan):
        """
        Deletes a plan

        :param plan: Plan to delete
        :raises: FBchatException if request failed
        """
        data = {"event_reminder_id": plan.uid, "delete": "true", "acontext": ACONTEXT}
        j = self._payload_post("/ajax/eventreminder/submit", data)

    def changePlanParticipation(self, plan, take_part=True):
        """
        Changes participation in a plan

        :param plan: Plan to take part in or not
        :param take_part: Whether to take part in the plan
        :raises: FBchatException if request failed
        """
        data = {
            "event_reminder_id": plan.uid,
            "guest_state": "GOING" if take_part else "DECLINED",
            "acontext": ACONTEXT,
        }
        j = self._payload_post("/ajax/eventreminder/rsvp", data)

    def eventReminder(self, thread_id, time, title, location="", location_id=""):
        """
        Deprecated. Use :func:`fbchat.Client.createPlan` instead
        """
        plan = Plan(time=time, title=title, location=location, location_id=location_id)
        self.createPlan(plan=plan, thread_id=thread_id)

    def createPoll(self, poll, thread_id=None):
        """
        Creates poll in a group thread

        :param poll: Poll to create
        :param thread_id: User/Group ID to create poll in. See :ref:`intro_threads`
        :type poll: Poll
        :raises: FBchatException if request failed
        """
        thread_id, thread_type = self._getThread(thread_id, None)

        # We're using ordered dicts, because the Facebook endpoint that parses the POST
        # parameters is badly implemented, and deals with ordering the options wrongly.
        # If you can find a way to fix this for the endpoint, or if you find another
        # endpoint, please do suggest it ;)
        data = OrderedDict([("question_text", poll.title), ("target_id", thread_id)])

        for i, option in enumerate(poll.options):
            data["option_text_array[{}]".format(i)] = option.text
            data["option_is_selected_array[{}]".format(i)] = str(int(option.vote))

        j = self._payload_post("/messaging/group_polling/create_poll/?dpr=1", data)
        if j.get("status") != "success":
            raise FBchatFacebookError(
                "Failed creating poll: {}".format(j.get("errorTitle")),
                fb_error_message=j.get("errorMessage"),
            )

    def updatePollVote(self, poll_id, option_ids=[], new_options=[]):
        """
        Updates a poll vote

        :param poll_id: ID of the poll to update vote
        :param option_ids: List of the option IDs to vote
        :param new_options: List of the new option names
        :param thread_id: User/Group ID to change status in. See :ref:`intro_threads`
        :param thread_type: See :ref:`intro_threads`
        :type thread_type: ThreadType
        :raises: FBchatException if request failed
        """
        data = {"question_id": poll_id}

        for i, option_id in enumerate(option_ids):
            data["selected_options[{}]".format(i)] = option_id

        for i, option_text in enumerate(new_options):
            data["new_options[{}]".format(i)] = option_text

        j = self._payload_post("/messaging/group_polling/update_vote/?dpr=1", data)
        if j.get("status") != "success":
            raise FBchatFacebookError(
                "Failed updating poll vote: {}".format(j.get("errorTitle")),
                fb_error_message=j.get("errorMessage"),
            )

    def setTypingStatus(self, status, thread_id=None, thread_type=None):
        """
        Sets users typing status in a thread

        :param status: Specify the typing status
        :param thread_id: User/Group ID to change status in. See :ref:`intro_threads`
        :param thread_type: See :ref:`intro_threads`
        :type status: TypingStatus
        :type thread_type: ThreadType
        :raises: FBchatException if request failed
        """
        thread_id, thread_type = self._getThread(thread_id, thread_type)

        data = {
            "typ": status.value,
            "thread": thread_id,
            "to": thread_id if thread_type == ThreadType.USER else "",
            "source": "mercury-chat",
        }
        j = self._payload_post("/ajax/messaging/typ.php", data)

    """
    END SEND METHODS
    """

    def markAsDelivered(self, thread_id, message_id):
        """
        Mark a message as delivered

        :param thread_id: User/Group ID to which the message belongs. See :ref:`intro_threads`
        :param message_id: Message ID to set as delivered. See :ref:`intro_threads`
        :return: True
        :raises: FBchatException if request failed
        """
        data = {
            "message_ids[0]": message_id,
            "thread_ids[%s][0]" % thread_id: message_id,
        }

        j = self._payload_post("/ajax/mercury/delivery_receipts.php", data)
        return True

    def _readStatus(self, read, thread_ids):
        thread_ids = require_list(thread_ids)

        data = {"watermarkTimestamp": now(), "shouldSendReadReceipt": "true"}

        for thread_id in thread_ids:
            data["ids[{}]".format(thread_id)] = "true" if read else "false"

        j = self._payload_post("/ajax/mercury/change_read_status.php", data)

    def markAsRead(self, thread_ids=None):
        """
        Mark threads as read
        All messages inside the threads will be marked as read

        :param thread_ids: User/Group IDs to set as read. See :ref:`intro_threads`
        :raises: FBchatException if request failed
        """
        self._readStatus(True, thread_ids)

    def markAsUnread(self, thread_ids=None):
        """
        Mark threads as unread
        All messages inside the threads will be marked as unread

        :param thread_ids: User/Group IDs to set as unread. See :ref:`intro_threads`
        :raises: FBchatException if request failed
        """
        self._readStatus(False, thread_ids)

    def markAsSeen(self):
        """
        .. todo::
            Documenting this
        """
        j = self._payload_post("/ajax/mercury/mark_seen.php", {"seen_timestamp": now()})

    def friendConnect(self, friend_id):
        """
        .. todo::
            Documenting this
        """
        data = {"to_friend": friend_id, "action": "confirm"}

        j = self._payload_post("/ajax/add_friend/action.php?dpr=1", data)

    def removeFriend(self, friend_id=None):
        """
        Removes a specifed friend from your friend list

        :param friend_id: The ID of the friend that you want to remove
        :return: True
        :raises: FBchatException if request failed
        """
        data = {"uid": friend_id}
        j = self._payload_post("/ajax/profile/removefriendconfirm.php", data)
        return True

    def blockUser(self, user_id):
        """
        Blocks messages from a specifed user

        :param user_id: The ID of the user that you want to block
        :return: True
        :raises: FBchatException if request failed
        """
        data = {"fbid": user_id}
        j = self._payload_post("/messaging/block_messages/?dpr=1", data)
        return True

    def unblockUser(self, user_id):
        """
        Unblocks messages from a blocked user

        :param user_id: The ID of the user that you want to unblock
        :return: Whether the request was successful
        :raises: FBchatException if request failed
        """
        data = {"fbid": user_id}
        j = self._payload_post("/messaging/unblock_messages/?dpr=1", data)
        return True

    def moveThreads(self, location, thread_ids):
        """
        Moves threads to specifed location

        :param location: ThreadLocation: INBOX, PENDING, ARCHIVED or OTHER
        :param thread_ids: Thread IDs to move. See :ref:`intro_threads`
        :return: True
        :raises: FBchatException if request failed
        """
        thread_ids = require_list(thread_ids)

        if location == ThreadLocation.PENDING:
            location = ThreadLocation.OTHER

        if location == ThreadLocation.ARCHIVED:
            data_archive = dict()
            data_unpin = dict()
            for thread_id in thread_ids:
                data_archive["ids[{}]".format(thread_id)] = "true"
                data_unpin["ids[{}]".format(thread_id)] = "false"
            j_archive = self._payload_post(
                "/ajax/mercury/change_archived_status.php?dpr=1", data_archive
            )
            j_unpin = self._payload_post(
                "/ajax/mercury/change_pinned_status.php?dpr=1", data_unpin
            )
        else:
            data = dict()
            for i, thread_id in enumerate(thread_ids):
                data["{}[{}]".format(location.name.lower(), i)] = thread_id
            j = self._payload_post("/ajax/mercury/move_thread.php", data)
        return True

    def deleteThreads(self, thread_ids):
        """
        Deletes threads

        :param thread_ids: Thread IDs to delete. See :ref:`intro_threads`
        :return: True
        :raises: FBchatException if request failed
        """
        thread_ids = require_list(thread_ids)

        data_unpin = dict()
        data_delete = dict()
        for i, thread_id in enumerate(thread_ids):
            data_unpin["ids[{}]".format(thread_id)] = "false"
            data_delete["ids[{}]".format(i)] = thread_id
        j_unpin = self._payload_post(
            "/ajax/mercury/change_pinned_status.php?dpr=1", data_unpin
        )
        j_delete = self._payload_post(
            "/ajax/mercury/delete_thread.php?dpr=1", data_delete
        )
        return True

    def markAsSpam(self, thread_id=None):
        """
        Mark a thread as spam and delete it

        :param thread_id: User/Group ID to mark as spam. See :ref:`intro_threads`
        :return: True
        :raises: FBchatException if request failed
        """
        thread_id, thread_type = self._getThread(thread_id, None)
        j = self._payload_post("/ajax/mercury/mark_spam.php?dpr=1", {"id": thread_id})
        return True

    def deleteMessages(self, message_ids):
        """
        Deletes specifed messages

        :param message_ids: Message IDs to delete
        :return: True
        :raises: FBchatException if request failed
        """
        message_ids = require_list(message_ids)
        data = dict()
        for i, message_id in enumerate(message_ids):
            data["message_ids[{}]".format(i)] = message_id
        j = self._payload_post("/ajax/mercury/delete_messages.php?dpr=1", data)
        return True

    def muteThread(self, mute_time=-1, thread_id=None):
        """
        Mutes thread

        :param mute_time: Mute time in seconds, leave blank to mute forever
        :param thread_id: User/Group ID to mute. See :ref:`intro_threads`
        """
        thread_id, thread_type = self._getThread(thread_id, None)
        data = {"mute_settings": str(mute_time), "thread_fbid": thread_id}
        j = self._payload_post("/ajax/mercury/change_mute_thread.php?dpr=1", data)

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
        data = {"reactions_mute_mode": int(mute), "thread_fbid": thread_id}
        j = self._payload_post(
            "/ajax/mercury/change_reactions_mute_thread/?dpr=1", data
        )

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
        data = {"mentions_mute_mode": int(mute), "thread_fbid": thread_id}
        j = self._payload_post("/ajax/mercury/change_mentions_mute_thread/?dpr=1", data)

    def unmuteThreadMentions(self, thread_id=None):
        """
        Unmutes thread mentions

        :param thread_id: User/Group ID to unmute. See :ref:`intro_threads`
        """
        return self.muteThreadMentions(False, thread_id)

    """
    LISTEN METHODS
    """

    def _ping(self):
        data = {
            "seq": self._seq,
            "channel": "p_" + self._uid,
            "clientid": self._client_id,
            "partition": -2,
            "cap": 0,
            "uid": self._uid,
            "sticky_token": self._sticky,
            "sticky_pool": self._pool,
            "viewer_uid": self._uid,
            "state": "active",
        }
        j = self._get(
            "https://{}-edge-chat.facebook.com/active_ping".format(self._pull_channel),
            data,
        )

    def _pullMessage(self):
        """Call pull api with seq value to get message data."""
        data = {
            "seq": self._seq,
            "msgs_recv": 0,
            "sticky_token": self._sticky,
            "sticky_pool": self._pool,
            "clientid": self._client_id,
            "state": "active" if self._markAlive else "offline",
        }
        return self._get(
            "https://{}-edge-chat.facebook.com/pull".format(self._pull_channel), data
        )

    def _parseDelta(self, m):
        def getThreadIdAndThreadType(msg_metadata):
            """Returns a tuple consisting of thread ID and thread type"""
            id_thread = None
            type_thread = None
            if "threadFbId" in msg_metadata["threadKey"]:
                id_thread = str(msg_metadata["threadKey"]["threadFbId"])
                type_thread = ThreadType.GROUP
            elif "otherUserFbId" in msg_metadata["threadKey"]:
                id_thread = str(msg_metadata["threadKey"]["otherUserFbId"])
                type_thread = ThreadType.USER
            return id_thread, type_thread

        delta = m["delta"]
        delta_type = delta.get("type")
        delta_class = delta.get("class")
        metadata = delta.get("messageMetadata")

        if metadata:
            mid = metadata["messageId"]
            author_id = str(metadata["actorFbId"])
            ts = int(metadata.get("timestamp"))

        # Added participants
        if "addedParticipants" in delta:
            added_ids = [str(x["userFbId"]) for x in delta["addedParticipants"]]
            thread_id = str(metadata["threadKey"]["threadFbId"])
            self.onPeopleAdded(
                mid=mid,
                added_ids=added_ids,
                author_id=author_id,
                thread_id=thread_id,
                ts=ts,
                msg=m,
            )

        # Left/removed participants
        elif "leftParticipantFbId" in delta:
            removed_id = str(delta["leftParticipantFbId"])
            thread_id = str(metadata["threadKey"]["threadFbId"])
            self.onPersonRemoved(
                mid=mid,
                removed_id=removed_id,
                author_id=author_id,
                thread_id=thread_id,
                ts=ts,
                msg=m,
            )

        # Color change
        elif delta_type == "change_thread_theme":
            new_color = ThreadColor._from_graphql(delta["untypedData"]["theme_color"])
            thread_id, thread_type = getThreadIdAndThreadType(metadata)
            self.onColorChange(
                mid=mid,
                author_id=author_id,
                new_color=new_color,
                thread_id=thread_id,
                thread_type=thread_type,
                ts=ts,
                metadata=metadata,
                msg=m,
            )

        # Emoji change
        elif delta_type == "change_thread_icon":
            new_emoji = delta["untypedData"]["thread_icon"]
            thread_id, thread_type = getThreadIdAndThreadType(metadata)
            self.onEmojiChange(
                mid=mid,
                author_id=author_id,
                new_emoji=new_emoji,
                thread_id=thread_id,
                thread_type=thread_type,
                ts=ts,
                metadata=metadata,
                msg=m,
            )

        # Thread title change
        elif delta_class == "ThreadName":
            new_title = delta["name"]
            thread_id, thread_type = getThreadIdAndThreadType(metadata)
            self.onTitleChange(
                mid=mid,
                author_id=author_id,
                new_title=new_title,
                thread_id=thread_id,
                thread_type=thread_type,
                ts=ts,
                metadata=metadata,
                msg=m,
            )

        # Forced fetch
        elif delta_class == "ForcedFetch":
            mid = delta.get("messageId")
            if mid is None:
                self.onUnknownMesssageType(msg=m)
            else:
                thread_id = str(delta["threadKey"]["threadFbId"])
                fetch_info = self._forcedFetch(thread_id, mid)
                fetch_data = fetch_info["message"]
                author_id = fetch_data["message_sender"]["id"]
                ts = fetch_data["timestamp_precise"]
                if fetch_data.get("__typename") == "ThreadImageMessage":
                    # Thread image change
                    image_metadata = fetch_data.get("image_with_metadata")
                    image_id = (
                        int(image_metadata["legacy_attachment_id"])
                        if image_metadata
                        else None
                    )
                    self.onImageChange(
                        mid=mid,
                        author_id=author_id,
                        new_image=image_id,
                        thread_id=thread_id,
                        thread_type=ThreadType.GROUP,
                        ts=ts,
                        msg=m,
                    )

        # Nickname change
        elif delta_type == "change_thread_nickname":
            changed_for = str(delta["untypedData"]["participant_id"])
            new_nickname = delta["untypedData"]["nickname"]
            thread_id, thread_type = getThreadIdAndThreadType(metadata)
            self.onNicknameChange(
                mid=mid,
                author_id=author_id,
                changed_for=changed_for,
                new_nickname=new_nickname,
                thread_id=thread_id,
                thread_type=thread_type,
                ts=ts,
                metadata=metadata,
                msg=m,
            )

        # Admin added or removed in a group thread
        elif delta_type == "change_thread_admins":
            thread_id, thread_type = getThreadIdAndThreadType(metadata)
            target_id = delta["untypedData"]["TARGET_ID"]
            admin_event = delta["untypedData"]["ADMIN_EVENT"]
            if admin_event == "add_admin":
                self.onAdminAdded(
                    mid=mid,
                    added_id=target_id,
                    author_id=author_id,
                    thread_id=thread_id,
                    thread_type=thread_type,
                    ts=ts,
                    msg=m,
                )
            elif admin_event == "remove_admin":
                self.onAdminRemoved(
                    mid=mid,
                    removed_id=target_id,
                    author_id=author_id,
                    thread_id=thread_id,
                    thread_type=thread_type,
                    ts=ts,
                    msg=m,
                )

        # Group approval mode change
        elif delta_type == "change_thread_approval_mode":
            thread_id, thread_type = getThreadIdAndThreadType(metadata)
            approval_mode = bool(int(delta["untypedData"]["APPROVAL_MODE"]))
            self.onApprovalModeChange(
                mid=mid,
                approval_mode=approval_mode,
                author_id=author_id,
                thread_id=thread_id,
                thread_type=thread_type,
                ts=ts,
                msg=m,
            )

        # Message delivered
        elif delta_class == "DeliveryReceipt":
            message_ids = delta["messageIds"]
            delivered_for = str(
                delta.get("actorFbId") or delta["threadKey"]["otherUserFbId"]
            )
            ts = int(delta["deliveredWatermarkTimestampMs"])
            thread_id, thread_type = getThreadIdAndThreadType(delta)
            self.onMessageDelivered(
                msg_ids=message_ids,
                delivered_for=delivered_for,
                thread_id=thread_id,
                thread_type=thread_type,
                ts=ts,
                metadata=metadata,
                msg=m,
            )

        # Message seen
        elif delta_class == "ReadReceipt":
            seen_by = str(delta.get("actorFbId") or delta["threadKey"]["otherUserFbId"])
            seen_ts = int(delta["actionTimestampMs"])
            delivered_ts = int(delta["watermarkTimestampMs"])
            thread_id, thread_type = getThreadIdAndThreadType(delta)
            self.onMessageSeen(
                seen_by=seen_by,
                thread_id=thread_id,
                thread_type=thread_type,
                seen_ts=seen_ts,
                ts=delivered_ts,
                metadata=metadata,
                msg=m,
            )

        # Messages marked as seen
        elif delta_class == "MarkRead":
            seen_ts = int(
                delta.get("actionTimestampMs") or delta.get("actionTimestamp")
            )
            delivered_ts = int(
                delta.get("watermarkTimestampMs") or delta.get("watermarkTimestamp")
            )

            threads = []
            if "folders" not in delta:
                threads = [
                    getThreadIdAndThreadType({"threadKey": thr})
                    for thr in delta.get("threadKeys")
                ]

            # thread_id, thread_type = getThreadIdAndThreadType(delta)
            self.onMarkedSeen(
                threads=threads, seen_ts=seen_ts, ts=delivered_ts, metadata=delta, msg=m
            )

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
            self.onGamePlayed(
                mid=mid,
                author_id=author_id,
                game_id=game_id,
                game_name=game_name,
                score=score,
                leaderboard=leaderboard,
                thread_id=thread_id,
                thread_type=thread_type,
                ts=ts,
                metadata=metadata,
                msg=m,
            )

        # Group call started/ended
        elif delta_type == "rtc_call_log":
            thread_id, thread_type = getThreadIdAndThreadType(metadata)
            call_status = delta["untypedData"]["event"]
            call_duration = int(delta["untypedData"]["call_duration"])
            is_video_call = bool(int(delta["untypedData"]["is_video_call"]))
            if call_status == "call_started":
                self.onCallStarted(
                    mid=mid,
                    caller_id=author_id,
                    is_video_call=is_video_call,
                    thread_id=thread_id,
                    thread_type=thread_type,
                    ts=ts,
                    metadata=metadata,
                    msg=m,
                )
            elif call_status == "call_ended":
                self.onCallEnded(
                    mid=mid,
                    caller_id=author_id,
                    is_video_call=is_video_call,
                    call_duration=call_duration,
                    thread_id=thread_id,
                    thread_type=thread_type,
                    ts=ts,
                    metadata=metadata,
                    msg=m,
                )

        # User joined to group call
        elif delta_type == "participant_joined_group_call":
            thread_id, thread_type = getThreadIdAndThreadType(metadata)
            is_video_call = bool(int(delta["untypedData"]["group_call_type"]))
            self.onUserJoinedCall(
                mid=mid,
                joined_id=author_id,
                is_video_call=is_video_call,
                thread_id=thread_id,
                thread_type=thread_type,
                ts=ts,
                metadata=metadata,
                msg=m,
            )

        # Group poll event
        elif delta_type == "group_poll":
            thread_id, thread_type = getThreadIdAndThreadType(metadata)
            event_type = delta["untypedData"]["event_type"]
            poll_json = json.loads(delta["untypedData"]["question_json"])
            poll = Poll._from_graphql(poll_json)
            if event_type == "question_creation":
                # User created group poll
                self.onPollCreated(
                    mid=mid,
                    poll=poll,
                    author_id=author_id,
                    thread_id=thread_id,
                    thread_type=thread_type,
                    ts=ts,
                    metadata=metadata,
                    msg=m,
                )
            elif event_type == "update_vote":
                # User voted on group poll
                added_options = json.loads(delta["untypedData"]["added_option_ids"])
                removed_options = json.loads(delta["untypedData"]["removed_option_ids"])
                self.onPollVoted(
                    mid=mid,
                    poll=poll,
                    added_options=added_options,
                    removed_options=removed_options,
                    author_id=author_id,
                    thread_id=thread_id,
                    thread_type=thread_type,
                    ts=ts,
                    metadata=metadata,
                    msg=m,
                )

        # Plan created
        elif delta_type == "lightweight_event_create":
            thread_id, thread_type = getThreadIdAndThreadType(metadata)
            self.onPlanCreated(
                mid=mid,
                plan=Plan._from_pull(delta["untypedData"]),
                author_id=author_id,
                thread_id=thread_id,
                thread_type=thread_type,
                ts=ts,
                metadata=metadata,
                msg=m,
            )

        # Plan ended
        elif delta_type == "lightweight_event_notify":
            thread_id, thread_type = getThreadIdAndThreadType(metadata)
            self.onPlanEnded(
                mid=mid,
                plan=Plan._from_pull(delta["untypedData"]),
                thread_id=thread_id,
                thread_type=thread_type,
                ts=ts,
                metadata=metadata,
                msg=m,
            )

        # Plan edited
        elif delta_type == "lightweight_event_update":
            thread_id, thread_type = getThreadIdAndThreadType(metadata)
            self.onPlanEdited(
                mid=mid,
                plan=Plan._from_pull(delta["untypedData"]),
                author_id=author_id,
                thread_id=thread_id,
                thread_type=thread_type,
                ts=ts,
                metadata=metadata,
                msg=m,
            )

        # Plan deleted
        elif delta_type == "lightweight_event_delete":
            thread_id, thread_type = getThreadIdAndThreadType(metadata)
            self.onPlanDeleted(
                mid=mid,
                plan=Plan._from_pull(delta["untypedData"]),
                author_id=author_id,
                thread_id=thread_id,
                thread_type=thread_type,
                ts=ts,
                metadata=metadata,
                msg=m,
            )

        # Plan participation change
        elif delta_type == "lightweight_event_rsvp":
            thread_id, thread_type = getThreadIdAndThreadType(metadata)
            take_part = delta["untypedData"]["guest_status"] == "GOING"
            self.onPlanParticipation(
                mid=mid,
                plan=Plan._from_pull(delta["untypedData"]),
                take_part=take_part,
                author_id=author_id,
                thread_id=thread_id,
                thread_type=thread_type,
                ts=ts,
                metadata=metadata,
                msg=m,
            )

        # Client payload (that weird numbers)
        elif delta_class == "ClientPayload":
            payload = json.loads("".join(chr(z) for z in delta["payload"]))
            ts = m.get("ofd_ts")
            for d in payload.get("deltas", []):

                # Message reaction
                if d.get("deltaMessageReaction"):
                    i = d["deltaMessageReaction"]
                    thread_id, thread_type = getThreadIdAndThreadType(i)
                    mid = i["messageId"]
                    author_id = str(i["userId"])
                    reaction = (
                        MessageReaction(i["reaction"]) if i.get("reaction") else None
                    )
                    add_reaction = not bool(i["action"])
                    if add_reaction:
                        self.onReactionAdded(
                            mid=mid,
                            reaction=reaction,
                            author_id=author_id,
                            thread_id=thread_id,
                            thread_type=thread_type,
                            ts=ts,
                            msg=m,
                        )
                    else:
                        self.onReactionRemoved(
                            mid=mid,
                            author_id=author_id,
                            thread_id=thread_id,
                            thread_type=thread_type,
                            ts=ts,
                            msg=m,
                        )

                # Viewer status change
                elif d.get("deltaChangeViewerStatus"):
                    i = d["deltaChangeViewerStatus"]
                    thread_id, thread_type = getThreadIdAndThreadType(i)
                    author_id = str(i["actorFbid"])
                    reason = i["reason"]
                    can_reply = i["canViewerReply"]
                    if reason == 2:
                        if can_reply:
                            self.onUnblock(
                                author_id=author_id,
                                thread_id=thread_id,
                                thread_type=thread_type,
                                ts=ts,
                                msg=m,
                            )
                        else:
                            self.onBlock(
                                author_id=author_id,
                                thread_id=thread_id,
                                thread_type=thread_type,
                                ts=ts,
                                msg=m,
                            )

                # Live location info
                elif d.get("liveLocationData"):
                    i = d["liveLocationData"]
                    thread_id, thread_type = getThreadIdAndThreadType(i)
                    for l in i["messageLiveLocations"]:
                        mid = l["messageId"]
                        author_id = str(l["senderId"])
                        location = LiveLocationAttachment._from_pull(l)
                        self.onLiveLocation(
                            mid=mid,
                            location=location,
                            author_id=author_id,
                            thread_id=thread_id,
                            thread_type=thread_type,
                            ts=ts,
                            msg=m,
                        )

                # Message deletion
                elif d.get("deltaRecallMessageData"):
                    i = d["deltaRecallMessageData"]
                    thread_id, thread_type = getThreadIdAndThreadType(i)
                    mid = i["messageID"]
                    ts = i["deletionTimestamp"]
                    author_id = str(i["senderID"])
                    self.onMessageUnsent(
                        mid=mid,
                        author_id=author_id,
                        thread_id=thread_id,
                        thread_type=thread_type,
                        ts=ts,
                        msg=m,
                    )

                elif d.get("deltaMessageReply"):
                    i = d["deltaMessageReply"]
                    metadata = i["message"]["messageMetadata"]
                    thread_id, thread_type = getThreadIdAndThreadType(metadata)
                    message = Message._from_reply(i["message"])
                    message.replied_to = Message._from_reply(i["repliedToMessage"])
                    message.reply_to_id = message.replied_to.uid
                    self.onMessage(
                        mid=message.uid,
                        author_id=message.author,
                        message=message.text,
                        message_object=message,
                        thread_id=thread_id,
                        thread_type=thread_type,
                        ts=message.timestamp,
                        metadata=metadata,
                        msg=m,
                    )

        # New message
        elif delta.get("class") == "NewMessage":
            thread_id, thread_type = getThreadIdAndThreadType(metadata)
            self.onMessage(
                mid=mid,
                author_id=author_id,
                message=delta.get("body", ""),
                message_object=Message._from_pull(
                    delta,
                    mid=mid,
                    tags=metadata.get("tags"),
                    author=author_id,
                    timestamp=ts,
                ),
                thread_id=thread_id,
                thread_type=thread_type,
                ts=ts,
                metadata=metadata,
                msg=m,
            )

        # Unknown message type
        else:
            self.onUnknownMesssageType(msg=m)

    def _parseMessage(self, content):
        """Get message and author name from content. May contain multiple messages in the content."""
        self._seq = content.get("seq", "0")

        if "lb_info" in content:
            self._sticky = content["lb_info"]["sticky"]
            self._pool = content["lb_info"]["pool"]

        if "batches" in content:
            for batch in content["batches"]:
                self._parseMessage(batch)

        if "ms" not in content:
            return

        for m in content["ms"]:
            mtype = m.get("type")
            try:
                # Things that directly change chat
                if mtype == "delta":
                    self._parseDelta(m)
                # Inbox
                elif mtype == "inbox":
                    self.onInbox(
                        unseen=m["unseen"],
                        unread=m["unread"],
                        recent_unread=m["recent_unread"],
                        msg=m,
                    )

                # Typing
                elif mtype == "typ" or mtype == "ttyp":
                    author_id = str(m.get("from"))
                    thread_id = m.get("thread_fbid")
                    if thread_id:
                        thread_type = ThreadType.GROUP
                        thread_id = str(thread_id)
                    else:
                        thread_type = ThreadType.USER
                        if author_id == self._uid:
                            thread_id = m.get("to")
                        else:
                            thread_id = author_id
                    typing_status = TypingStatus(m.get("st"))
                    self.onTyping(
                        author_id=author_id,
                        status=typing_status,
                        thread_id=thread_id,
                        thread_type=thread_type,
                        msg=m,
                    )

                # Delivered

                # Seen
                # elif mtype == "m_read_receipt":
                #
                #     self.onSeen(m.get('realtime_viewer_fbid'), m.get('reader'), m.get('time'))

                elif mtype in ["jewel_requests_add"]:
                    from_id = m["from"]
                    self.onFriendRequest(from_id=from_id, msg=m)

                # Happens on every login
                elif mtype == "qprimer":
                    self.onQprimer(ts=m.get("made"), msg=m)

                # Is sent before any other message
                elif mtype == "deltaflow":
                    pass

                # Chat timestamp
                elif mtype == "chatproxy-presence":
                    statuses = dict()
                    for id_, data in m.get("buddyList", {}).items():
                        statuses[id_] = ActiveStatus._from_chatproxy_presence(id_, data)
                        self._buddylist[id_] = statuses[id_]

                    self.onChatTimestamp(buddylist=statuses, msg=m)

                # Buddylist overlay
                elif mtype == "buddylist_overlay":
                    statuses = dict()
                    for id_, data in m.get("overlay", {}).items():
                        old_in_game = None
                        if id_ in self._buddylist:
                            old_in_game = self._buddylist[id_].in_game

                        statuses[id_] = ActiveStatus._from_buddylist_overlay(
                            data, old_in_game
                        )
                        self._buddylist[id_] = statuses[id_]

                    self.onBuddylistOverlay(statuses=statuses, msg=m)

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

    def doOneListen(self, markAlive=None):
        """
        Does one cycle of the listening loop.
        This method is useful if you want to control fbchat from an external event loop

        .. warning::
            ``markAlive`` parameter is deprecated, use :func:`Client.setActiveStatus`
            or ``markAlive`` parameter in :func:`Client.listen` instead.

        :return: Whether the loop should keep running
        :rtype: bool
        """
        if markAlive is not None:
            self._markAlive = markAlive
        try:
            if self._markAlive:
                self._ping()
            content = self._pullMessage()
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
                # Bump pull channel, while contraining withing 0-4
                self._pull_channel = (self._pull_channel + 1) % 5
                self.startListening()
            else:
                raise e
        except Exception as e:
            return self.onListenError(exception=e)

        return True

    def stopListening(self):
        """Cleans up the variables from startListening"""
        self.listening = False
        self._sticky, self._pool = (None, None)

    def listen(self, markAlive=None):
        """
        Initializes and runs the listening loop continually

        :param markAlive: Whether this should ping the Facebook server each time the loop runs
        :type markAlive: bool
        """
        if markAlive is not None:
            self.setActiveStatus(markAlive)

        self.startListening()
        self.onListening()

        while self.listening and self.doOneListen():
            pass

        self.stopListening()

    def setActiveStatus(self, markAlive):
        """
        Changes client active status while listening

        :param markAlive: Whether to show if client is active
        :type markAlive: bool
        """
        self._markAlive = markAlive

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
        return input("Please enter your 2FA code --> ")

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
        log.exception("Got exception while listening")
        return True

    def onMessage(
        self,
        mid=None,
        author_id=None,
        message=None,
        message_object=None,
        thread_id=None,
        thread_type=ThreadType.USER,
        ts=None,
        metadata=None,
        msg=None,
    ):
        """
        Called when the client is listening, and somebody sends a message

        :param mid: The message ID
        :param author_id: The ID of the author
        :param message: (deprecated. Use ``message_object.text`` instead)
        :param message_object: The message (As a `Message` object)
        :param thread_id: Thread ID that the message was sent to. See :ref:`intro_threads`
        :param thread_type: Type of thread that the message was sent to. See :ref:`intro_threads`
        :param ts: The timestamp of the message
        :param metadata: Extra metadata about the message
        :param msg: A full set of the data recieved
        :type message_object: Message
        :type thread_type: ThreadType
        """
        log.info("{} from {} in {}".format(message_object, thread_id, thread_type.name))

    def onColorChange(
        self,
        mid=None,
        author_id=None,
        new_color=None,
        thread_id=None,
        thread_type=ThreadType.USER,
        ts=None,
        metadata=None,
        msg=None,
    ):
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
        :type new_color: ThreadColor
        :type thread_type: ThreadType
        """
        log.info(
            "Color change from {} in {} ({}): {}".format(
                author_id, thread_id, thread_type.name, new_color
            )
        )

    def onEmojiChange(
        self,
        mid=None,
        author_id=None,
        new_emoji=None,
        thread_id=None,
        thread_type=ThreadType.USER,
        ts=None,
        metadata=None,
        msg=None,
    ):
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
        :type thread_type: ThreadType
        """
        log.info(
            "Emoji change from {} in {} ({}): {}".format(
                author_id, thread_id, thread_type.name, new_emoji
            )
        )

    def onTitleChange(
        self,
        mid=None,
        author_id=None,
        new_title=None,
        thread_id=None,
        thread_type=ThreadType.USER,
        ts=None,
        metadata=None,
        msg=None,
    ):
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
        :type thread_type: ThreadType
        """
        log.info(
            "Title change from {} in {} ({}): {}".format(
                author_id, thread_id, thread_type.name, new_title
            )
        )

    def onImageChange(
        self,
        mid=None,
        author_id=None,
        new_image=None,
        thread_id=None,
        thread_type=ThreadType.GROUP,
        ts=None,
        msg=None,
    ):
        """
        Called when the client is listening, and somebody changes the image of a thread

        :param mid: The action ID
        :param author_id: The ID of the person who changed the image
        :param new_image: The ID of the new image
        :param thread_id: Thread ID that the action was sent to. See :ref:`intro_threads`
        :param thread_type: Type of thread that the action was sent to. See :ref:`intro_threads`
        :param ts: A timestamp of the action
        :param msg: A full set of the data recieved
        :type thread_type: ThreadType
        """
        log.info("{} changed thread image in {}".format(author_id, thread_id))

    def onNicknameChange(
        self,
        mid=None,
        author_id=None,
        changed_for=None,
        new_nickname=None,
        thread_id=None,
        thread_type=ThreadType.USER,
        ts=None,
        metadata=None,
        msg=None,
    ):
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
        :type thread_type: ThreadType
        """
        log.info(
            "Nickname change from {} in {} ({}) for {}: {}".format(
                author_id, thread_id, thread_type.name, changed_for, new_nickname
            )
        )

    def onAdminAdded(
        self,
        mid=None,
        added_id=None,
        author_id=None,
        thread_id=None,
        thread_type=ThreadType.GROUP,
        ts=None,
        msg=None,
    ):
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

    def onAdminRemoved(
        self,
        mid=None,
        removed_id=None,
        author_id=None,
        thread_id=None,
        thread_type=ThreadType.GROUP,
        ts=None,
        msg=None,
    ):
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

    def onApprovalModeChange(
        self,
        mid=None,
        approval_mode=None,
        author_id=None,
        thread_id=None,
        thread_type=ThreadType.GROUP,
        ts=None,
        msg=None,
    ):
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

    def onMessageSeen(
        self,
        seen_by=None,
        thread_id=None,
        thread_type=ThreadType.USER,
        seen_ts=None,
        ts=None,
        metadata=None,
        msg=None,
    ):
        """
        Called when the client is listening, and somebody marks a message as seen

        :param seen_by: The ID of the person who marked the message as seen
        :param thread_id: Thread ID that the action was sent to. See :ref:`intro_threads`
        :param thread_type: Type of thread that the action was sent to. See :ref:`intro_threads`
        :param seen_ts: A timestamp of when the person saw the message
        :param ts: A timestamp of the action
        :param metadata: Extra metadata about the action
        :param msg: A full set of the data recieved
        :type thread_type: ThreadType
        """
        log.info(
            "Messages seen by {} in {} ({}) at {}s".format(
                seen_by, thread_id, thread_type.name, seen_ts / 1000
            )
        )

    def onMessageDelivered(
        self,
        msg_ids=None,
        delivered_for=None,
        thread_id=None,
        thread_type=ThreadType.USER,
        ts=None,
        metadata=None,
        msg=None,
    ):
        """
        Called when the client is listening, and somebody marks messages as delivered

        :param msg_ids: The messages that are marked as delivered
        :param delivered_for: The person that marked the messages as delivered
        :param thread_id: Thread ID that the action was sent to. See :ref:`intro_threads`
        :param thread_type: Type of thread that the action was sent to. See :ref:`intro_threads`
        :param ts: A timestamp of the action
        :param metadata: Extra metadata about the action
        :param msg: A full set of the data recieved
        :type thread_type: ThreadType
        """
        log.info(
            "Messages {} delivered to {} in {} ({}) at {}s".format(
                msg_ids, delivered_for, thread_id, thread_type.name, ts / 1000
            )
        )

    def onMarkedSeen(
        self, threads=None, seen_ts=None, ts=None, metadata=None, msg=None
    ):
        """
        Called when the client is listening, and the client has successfully marked threads as seen

        :param threads: The threads that were marked
        :param author_id: The ID of the person who changed the emoji
        :param seen_ts: A timestamp of when the threads were seen
        :param ts: A timestamp of the action
        :param metadata: Extra metadata about the action
        :param msg: A full set of the data recieved
        :type thread_type: ThreadType
        """
        log.info(
            "Marked messages as seen in threads {} at {}s".format(
                [(x[0], x[1].name) for x in threads], seen_ts / 1000
            )
        )

    def onMessageUnsent(
        self,
        mid=None,
        author_id=None,
        thread_id=None,
        thread_type=None,
        ts=None,
        msg=None,
    ):
        """
        Called when the client is listening, and someone unsends (deletes for everyone) a message

        :param mid: ID of the unsent message
        :param author_id: The ID of the person who unsent the message
        :param thread_id: Thread ID that the action was sent to. See :ref:`intro_threads`
        :param thread_type: Type of thread that the action was sent to. See :ref:`intro_threads`
        :param ts: A timestamp of the action
        :param msg: A full set of the data recieved
        :type thread_type: ThreadType
        """
        log.info(
            "{} unsent the message {} in {} ({}) at {}s".format(
                author_id, repr(mid), thread_id, thread_type.name, ts / 1000
            )
        )

    def onPeopleAdded(
        self,
        mid=None,
        added_ids=None,
        author_id=None,
        thread_id=None,
        ts=None,
        msg=None,
    ):
        """
        Called when the client is listening, and somebody adds people to a group thread

        :param mid: The action ID
        :param added_ids: The IDs of the people who got added
        :param author_id: The ID of the person who added the people
        :param thread_id: Thread ID that the action was sent to. See :ref:`intro_threads`
        :param ts: A timestamp of the action
        :param msg: A full set of the data recieved
        """
        log.info(
            "{} added: {} in {}".format(author_id, ", ".join(added_ids), thread_id)
        )

    def onPersonRemoved(
        self,
        mid=None,
        removed_id=None,
        author_id=None,
        thread_id=None,
        ts=None,
        msg=None,
    ):
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
        log.info("Inbox event: {}, {}, {}".format(unseen, unread, recent_unread))

    def onTyping(
        self, author_id=None, status=None, thread_id=None, thread_type=None, msg=None
    ):
        """
        Called when the client is listening, and somebody starts or stops typing into a chat

        :param author_id: The ID of the person who sent the action
        :param status: The typing status
        :param thread_id: Thread ID that the action was sent to. See :ref:`intro_threads`
        :param thread_type: Type of thread that the action was sent to. See :ref:`intro_threads`
        :param msg: A full set of the data recieved
        :type typing_status: TypingStatus
        :type thread_type: ThreadType
        """
        pass

    def onGamePlayed(
        self,
        mid=None,
        author_id=None,
        game_id=None,
        game_name=None,
        score=None,
        leaderboard=None,
        thread_id=None,
        thread_type=None,
        ts=None,
        metadata=None,
        msg=None,
    ):
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
        :type thread_type: ThreadType
        """
        log.info(
            '{} played "{}" in {} ({})'.format(
                author_id, game_name, thread_id, thread_type.name
            )
        )

    def onReactionAdded(
        self,
        mid=None,
        reaction=None,
        author_id=None,
        thread_id=None,
        thread_type=None,
        ts=None,
        msg=None,
    ):
        """
        Called when the client is listening, and somebody reacts to a message

        :param mid: Message ID, that user reacted to
        :param reaction: Reaction
        :param add_reaction: Whether user added or removed reaction
        :param author_id: The ID of the person who reacted to the message
        :param thread_id: Thread ID that the action was sent to. See :ref:`intro_threads`
        :param thread_type: Type of thread that the action was sent to. See :ref:`intro_threads`
        :param ts: A timestamp of the action
        :param msg: A full set of the data recieved
        :type reaction: MessageReaction
        :type thread_type: ThreadType
        """
        log.info(
            "{} reacted to message {} with {} in {} ({})".format(
                author_id, mid, reaction.name, thread_id, thread_type.name
            )
        )

    def onReactionRemoved(
        self,
        mid=None,
        author_id=None,
        thread_id=None,
        thread_type=None,
        ts=None,
        msg=None,
    ):
        """
        Called when the client is listening, and somebody removes reaction from a message

        :param mid: Message ID, that user reacted to
        :param author_id: The ID of the person who removed reaction
        :param thread_id: Thread ID that the action was sent to. See :ref:`intro_threads`
        :param thread_type: Type of thread that the action was sent to. See :ref:`intro_threads`
        :param ts: A timestamp of the action
        :param msg: A full set of the data recieved
        :type thread_type: ThreadType
        """
        log.info(
            "{} removed reaction from {} message in {} ({})".format(
                author_id, mid, thread_id, thread_type
            )
        )

    def onBlock(
        self, author_id=None, thread_id=None, thread_type=None, ts=None, msg=None
    ):
        """
        Called when the client is listening, and somebody blocks client

        :param author_id: The ID of the person who blocked
        :param thread_id: Thread ID that the action was sent to. See :ref:`intro_threads`
        :param thread_type: Type of thread that the action was sent to. See :ref:`intro_threads`
        :param ts: A timestamp of the action
        :param msg: A full set of the data recieved
        :type thread_type: ThreadType
        """
        log.info(
            "{} blocked {} ({}) thread".format(author_id, thread_id, thread_type.name)
        )

    def onUnblock(
        self, author_id=None, thread_id=None, thread_type=None, ts=None, msg=None
    ):
        """
        Called when the client is listening, and somebody blocks client

        :param author_id: The ID of the person who unblocked
        :param thread_id: Thread ID that the action was sent to. See :ref:`intro_threads`
        :param thread_type: Type of thread that the action was sent to. See :ref:`intro_threads`
        :param ts: A timestamp of the action
        :param msg: A full set of the data recieved
        :type thread_type: ThreadType
        """
        log.info(
            "{} unblocked {} ({}) thread".format(author_id, thread_id, thread_type.name)
        )

    def onLiveLocation(
        self,
        mid=None,
        location=None,
        author_id=None,
        thread_id=None,
        thread_type=None,
        ts=None,
        msg=None,
    ):
        """
        Called when the client is listening and somebody sends live location info

        :param mid: The action ID
        :param location: Sent location info
        :param author_id: The ID of the person who sent location info
        :param thread_id: Thread ID that the action was sent to. See :ref:`intro_threads`
        :param thread_type: Type of thread that the action was sent to. See :ref:`intro_threads`
        :param ts: A timestamp of the action
        :param msg: A full set of the data recieved
        :type location: LiveLocationAttachment
        :type thread_type: ThreadType
        """
        log.info(
            "{} sent live location info in {} ({}) with latitude {} and longitude {}".format(
                author_id, thread_id, thread_type, location.latitude, location.longitude
            )
        )

    def onCallStarted(
        self,
        mid=None,
        caller_id=None,
        is_video_call=None,
        thread_id=None,
        thread_type=None,
        ts=None,
        metadata=None,
        msg=None,
    ):
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
        :type thread_type: ThreadType
        """
        log.info(
            "{} started call in {} ({})".format(caller_id, thread_id, thread_type.name)
        )

    def onCallEnded(
        self,
        mid=None,
        caller_id=None,
        is_video_call=None,
        call_duration=None,
        thread_id=None,
        thread_type=None,
        ts=None,
        metadata=None,
        msg=None,
    ):
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
        :type thread_type: ThreadType
        """
        log.info(
            "{} ended call in {} ({})".format(caller_id, thread_id, thread_type.name)
        )

    def onUserJoinedCall(
        self,
        mid=None,
        joined_id=None,
        is_video_call=None,
        thread_id=None,
        thread_type=None,
        ts=None,
        metadata=None,
        msg=None,
    ):
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
        :type thread_type: ThreadType
        """
        log.info(
            "{} joined call in {} ({})".format(joined_id, thread_id, thread_type.name)
        )

    def onPollCreated(
        self,
        mid=None,
        poll=None,
        author_id=None,
        thread_id=None,
        thread_type=None,
        ts=None,
        metadata=None,
        msg=None,
    ):
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
        :type poll: Poll
        :type thread_type: ThreadType
        """
        log.info(
            "{} created poll {} in {} ({})".format(
                author_id, poll, thread_id, thread_type.name
            )
        )

    def onPollVoted(
        self,
        mid=None,
        poll=None,
        added_options=None,
        removed_options=None,
        author_id=None,
        thread_id=None,
        thread_type=None,
        ts=None,
        metadata=None,
        msg=None,
    ):
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
        :type poll: Poll
        :type thread_type: ThreadType
        """
        log.info(
            "{} voted in poll {} in {} ({})".format(
                author_id, poll, thread_id, thread_type.name
            )
        )

    def onPlanCreated(
        self,
        mid=None,
        plan=None,
        author_id=None,
        thread_id=None,
        thread_type=None,
        ts=None,
        metadata=None,
        msg=None,
    ):
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
        :type plan: Plan
        :type thread_type: ThreadType
        """
        log.info(
            "{} created plan {} in {} ({})".format(
                author_id, plan, thread_id, thread_type.name
            )
        )

    def onPlanEnded(
        self,
        mid=None,
        plan=None,
        thread_id=None,
        thread_type=None,
        ts=None,
        metadata=None,
        msg=None,
    ):
        """
        Called when the client is listening, and a plan ends

        :param mid: The action ID
        :param plan: Ended plan
        :param thread_id: Thread ID that the action was sent to. See :ref:`intro_threads`
        :param thread_type: Type of thread that the action was sent to. See :ref:`intro_threads`
        :param ts: A timestamp of the action
        :param metadata: Extra metadata about the action
        :param msg: A full set of the data recieved
        :type plan: Plan
        :type thread_type: ThreadType
        """
        log.info(
            "Plan {} has ended in {} ({})".format(plan, thread_id, thread_type.name)
        )

    def onPlanEdited(
        self,
        mid=None,
        plan=None,
        author_id=None,
        thread_id=None,
        thread_type=None,
        ts=None,
        metadata=None,
        msg=None,
    ):
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
        :type plan: Plan
        :type thread_type: ThreadType
        """
        log.info(
            "{} edited plan {} in {} ({})".format(
                author_id, plan, thread_id, thread_type.name
            )
        )

    def onPlanDeleted(
        self,
        mid=None,
        plan=None,
        author_id=None,
        thread_id=None,
        thread_type=None,
        ts=None,
        metadata=None,
        msg=None,
    ):
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
        :type plan: Plan
        :type thread_type: ThreadType
        """
        log.info(
            "{} deleted plan {} in {} ({})".format(
                author_id, plan, thread_id, thread_type.name
            )
        )

    def onPlanParticipation(
        self,
        mid=None,
        plan=None,
        take_part=None,
        author_id=None,
        thread_id=None,
        thread_type=None,
        ts=None,
        metadata=None,
        msg=None,
    ):
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
        :type plan: Plan
        :type take_part: bool
        :type thread_type: ThreadType
        """
        if take_part:
            log.info(
                "{} will take part in {} in {} ({})".format(
                    author_id, plan, thread_id, thread_type.name
                )
            )
        else:
            log.info(
                "{} won't take part in {} in {} ({})".format(
                    author_id, plan, thread_id, thread_type.name
                )
            )

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
        log.debug("Chat Timestamps received: {}".format(buddylist))

    def onBuddylistOverlay(self, statuses=None, msg=None):
        """
        Called when the client is listening and client receives information about friend active status

        :param statuses: Dictionary with user IDs as keys and :class:`ActiveStatus` as values
        :param msg: A full set of the data recieved
        :type statuses: dict
        """
        log.debug("Buddylist overlay received: {}".format(statuses))

    def onUnknownMesssageType(self, msg=None):
        """
        Called when the client is listening, and some unknown data was recieved

        :param msg: A full set of the data recieved
        """
        log.debug("Unknown message received: {}".format(msg))

    def onMessageError(self, exception=None, msg=None):
        """
        Called when an error was encountered while parsing recieved data

        :param exception: The exception that was encountered
        :param msg: A full set of the data recieved
        """
        log.exception("Exception in parsing of {}".format(msg))

    """
    END EVENTS
    """
