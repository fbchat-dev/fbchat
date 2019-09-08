import datetime
import time
import json
import requests
from collections import OrderedDict

from ._core import log
from . import _util, _graphql, _state

from ._exception import FBchatException, FBchatFacebookError
from ._thread import ThreadType, ThreadLocation, ThreadColor
from ._user import TypingStatus, User, ActiveStatus
from ._group import Group
from ._page import Page
from ._message import EmojiSize, MessageReaction, Mention, Message
from ._attachment import Attachment
from ._sticker import Sticker
from ._location import LocationAttachment, LiveLocationAttachment
from ._file import ImageAttachment, VideoAttachment
from ._quick_reply import (
    QuickReply,
    QuickReplyText,
    QuickReplyLocation,
    QuickReplyPhoneNumber,
    QuickReplyEmail,
)
from ._poll import Poll, PollOption
from ._plan import Plan


ACONTEXT = {
    "action_history": [
        {"surface": "messenger_chat_tab", "mechanism": "messenger_composer"}
    ]
}


class Client:
    """A client for the Facebook Chat (Messenger).

    This is the main class of ``fbchat``, which contains all the methods you use to
    interact with Facebook. You can extend this class, and overwrite the ``on`` methods,
    to provide custom event handling (mainly useful while listening).
    """

    @property
    def uid(self):
        """The ID of the client.

        Can be used as ``thread_id``. See :ref:`intro_threads` for more info.
        """
        return self._uid

    def __init__(self, email, password, session_cookies=None):
        """Initialize and log in the client.

        Args:
            email: Facebook ``email``, ``id`` or ``phone number``
            password: Facebook account password
            session_cookies (dict): Cookies from a previous session (Will default to login if these are invalid)

        Raises:
            FBchatException: On failed login
        """
        self._sticky, self._pool = (None, None)
        self._seq = "0"
        self._pull_channel = 0
        self._mark_alive = True
        self._buddylist = dict()

        # If session cookies aren't set, not properly loaded or gives us an invalid session, then do the login
        if (
            not session_cookies
            or not self.set_session(session_cookies)
            or not self.is_logged_in()
        ):
            self.login(email, password)

    """
    INTERNAL REQUEST METHODS
    """

    def _get(self, url, params):
        return self._state._get(url, params)

    def _post(self, url, params, files=None):
        return self._state._post(url, params, files=files)

    def _payload_post(self, url, data, files=None):
        return self._state._payload_post(url, data, files=files)

    def graphql_requests(self, *queries):
        """Execute GraphQL queries.

        Args:
            queries (dict): Zero or more dictionaries

        Returns:
            tuple: A tuple containing JSON GraphQL queries

        Raises:
            FBchatException: If request failed
        """
        return tuple(self._state._graphql_requests(*queries))

    def graphql_request(self, query):
        """Shorthand for ``graphql_requests(query)[0]``.

        Raises:
            FBchatException: If request failed
        """
        return self.graphql_requests(query)[0]

    """
    END INTERNAL REQUEST METHODS
    """

    """
    LOGIN METHODS
    """

    def is_logged_in(self):
        """Send a request to Facebook to check the login status.

        Returns:
            bool: True if the client is still logged in
        """
        return self._state.is_logged_in()

    def get_session(self):
        """Retrieve session cookies.

        Returns:
            dict: A dictionary containing session cookies
        """
        return self._state.get_cookies()

    def set_session(self, session_cookies):
        """Load session cookies.

        Args:
            session_cookies (dict): A dictionary containing session cookies

        Returns:
            bool: False if ``session_cookies`` does not contain proper cookies
        """
        try:
            # Load cookies into current session
            self._state = _state.State.from_cookies(session_cookies)
            self._uid = self._state.user_id
        except Exception as e:
            log.exception("Failed loading session")
            return False
        return True

    def login(self, email, password):
        """Login the user, using ``email`` and ``password``.

        If the user is already logged in, this will do a re-login.

        Args:
            email: Facebook ``email`` or ``id`` or ``phone number``
            password: Facebook account password

        Raises:
            FBchatException: On failed login
        """
        self.on_logging_in(email=email)

        if not (email and password):
            raise ValueError("Email and password not set")

        self._state = _state.State.login(
            email, password, on_2fa_callback=self.on_2fa_code
        )
        self._uid = self._state.user_id
        self.on_logged_in(email=email)

    def logout(self):
        """Safely log out the client.

        Returns:
            bool: True if the action was successful
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
    FETCH METHODS
    """

    def _forced_fetch(self, thread_id, mid):
        params = {"thread_and_message_id": {"thread_id": thread_id, "message_id": mid}}
        j, = self.graphql_requests(_graphql.from_doc_id("1768656253222505", params))
        return j

    def fetch_threads(self, thread_location, before=None, after=None, limit=None):
        """Fetch all threads in ``thread_location``.

        Threads will be sorted from newest to oldest.

        Args:
            thread_location (ThreadLocation): INBOX, PENDING, ARCHIVED or OTHER
            before (datetime.datetime): Fetch only threads before this (default all
                threads). Must be timezone-aware!
            after (datetime.datetime): Fetch only threads after this (default all
                threads). Must be timezone-aware!
            limit: The max. amount of threads to fetch (default all threads)

        Returns:
            list: :class:`Thread` objects

        Raises:
            FBchatException: If request failed
        """
        threads = []

        last_thread_dt = None
        while True:
            # break if limit is exceeded
            if limit and len(threads) >= limit:
                break

            # fetch_thread_list returns at max 20 threads before last_thread_dt (included)
            candidates = self.fetch_thread_list(
                before=last_thread_dt, thread_location=thread_location
            )

            if len(candidates) > 1:
                threads += candidates[1:]
            else:  # End of threads
                break

            last_thread_dt = threads[-1].last_active

            # FB returns a sorted list of threads
            if (before is not None and last_thread_dt > before) or (
                after is not None and last_thread_dt < after
            ):
                break

        # Return only threads between before and after (if set)
        if before is not None or after is not None:
            for t in threads:
                if (before is not None and t.last_active > before) or (
                    after is not None and t.last_active < after
                ):
                    threads.remove(t)

        if limit and len(threads) > limit:
            return threads[:limit]

        return threads

    def fetch_all_users_from_threads(self, threads):
        """Fetch all users involved in given threads.

        Args:
            threads: Thread: List of threads to check for users

        Returns:
            list: :class:`User` objects

        Raises:
            FBchatException: If request failed
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
        for user_id, user in self.fetch_user_info(*users_to_fetch).items():
            users.append(user)
        return users

    def fetch_all_users(self):
        """Fetch all users the client is currently chatting with.

        Returns:
            list: :class:`User` objects

        Raises:
            FBchatException: If request failed
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

    def search_for_users(self, name, limit=10):
        """Find and get users by their name.

        Args:
            name: Name of the user
            limit: The max. amount of users to fetch

        Returns:
            list: :class:`User` objects, ordered by relevance

        Raises:
            FBchatException: If request failed
        """
        params = {"search": name, "limit": limit}
        j, = self.graphql_requests(_graphql.from_query(_graphql.SEARCH_USER, params))

        return [User._from_graphql(node) for node in j[name]["users"]["nodes"]]

    def search_for_pages(self, name, limit=10):
        """Find and get pages by their name.

        Args:
            name: Name of the page

        Returns:
            list: :class:`Page` objects, ordered by relevance

        Raises:
            FBchatException: If request failed
        """
        params = {"search": name, "limit": limit}
        j, = self.graphql_requests(_graphql.from_query(_graphql.SEARCH_PAGE, params))

        return [Page._from_graphql(node) for node in j[name]["pages"]["nodes"]]

    def search_for_groups(self, name, limit=10):
        """Find and get group threads by their name.

        Args:
            name: Name of the group thread
            limit: The max. amount of groups to fetch

        Returns:
            list: :class:`Group` objects, ordered by relevance

        Raises:
            FBchatException: If request failed
        """
        params = {"search": name, "limit": limit}
        j, = self.graphql_requests(_graphql.from_query(_graphql.SEARCH_GROUP, params))

        return [Group._from_graphql(node) for node in j["viewer"]["groups"]["nodes"]]

    def search_for_threads(self, name, limit=10):
        """Find and get threads by their name.

        Args:
            name: Name of the thread
            limit: The max. amount of groups to fetch

        Returns:
            list: :class:`User`, :class:`Group` and :class:`Page` objects, ordered by relevance

        Raises:
            FBchatException: If request failed
        """
        params = {"search": name, "limit": limit}
        j, = self.graphql_requests(_graphql.from_query(_graphql.SEARCH_THREAD, params))

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

    def search_for_message_ids(self, query, offset=0, limit=5, thread_id=None):
        """Find and get message IDs by query.

        Args:
            query: Text to search for
            offset (int): Number of messages to skip
            limit (int): Max. number of messages to retrieve
            thread_id: User/Group ID to search in. See :ref:`intro_threads`

        Returns:
            typing.Iterable: Found Message IDs

        Raises:
            FBchatException: If request failed
        """
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

    def search_for_messages(self, query, offset=0, limit=5, thread_id=None):
        """Find and get `Message` objects by query.

        Warning:
            This method sends request for every found message ID.

        Args:
            query: Text to search for
            offset (int): Number of messages to skip
            limit (int): Max. number of messages to retrieve
            thread_id: User/Group ID to search in. See :ref:`intro_threads`

        Returns:
            typing.Iterable: Found :class:`Message` objects

        Raises:
            FBchatException: If request failed
        """
        message_ids = self.search_for_message_ids(
            query, offset=offset, limit=limit, thread_id=thread_id
        )
        for mid in message_ids:
            yield self.fetch_message_info(mid, thread_id)

    def search(self, query, fetch_messages=False, thread_limit=5, message_limit=5):
        """Search for messages in all threads.

        Args:
            query: Text to search for
            fetch_messages: Whether to fetch :class:`Message` objects or IDs only
            thread_limit (int): Max. number of threads to retrieve
            message_limit (int): Max. number of messages to retrieve

        Returns:
            typing.Dict[str, typing.Iterable]: Dictionary with thread IDs as keys and iterables to get messages as values

        Raises:
            FBchatException: If request failed
        """
        data = {"query": query, "snippetLimit": thread_limit}
        j = self._payload_post("/ajax/mercury/search_snippets.php?dpr=1", data)
        result = j["search_snippets"][query]

        if not result:
            return {}

        if fetch_messages:
            search_method = self.search_for_messages
        else:
            search_method = self.search_for_message_ids

        return {
            thread_id: search_method(query, limit=message_limit, thread_id=thread_id)
            for thread_id in result
        }

    def _fetch_info(self, *ids):
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

    def fetch_user_info(self, *user_ids):
        """Fetch users' info from IDs, unordered.

        Warning:
            Sends two requests, to fetch all available info!

        Args:
            user_ids: One or more user ID(s) to query

        Returns:
            dict: :class:`User` objects, labeled by their ID

        Raises:
            FBchatException: If request failed
        """
        threads = self.fetch_thread_info(*user_ids)
        users = {}
        for id_, thread in threads.items():
            if thread.type == ThreadType.USER:
                users[id_] = thread
            else:
                raise ValueError("Thread {} was not a user".format(thread))

        return users

    def fetch_page_info(self, *page_ids):
        """Fetch pages' info from IDs, unordered.

        Warning:
            Sends two requests, to fetch all available info!

        Args:
            page_ids: One or more page ID(s) to query

        Returns:
            dict: :class:`Page` objects, labeled by their ID

        Raises:
            FBchatException: If request failed
        """
        threads = self.fetch_thread_info(*page_ids)
        pages = {}
        for id_, thread in threads.items():
            if thread.type == ThreadType.PAGE:
                pages[id_] = thread
            else:
                raise ValueError("Thread {} was not a page".format(thread))

        return pages

    def fetch_group_info(self, *group_ids):
        """Fetch groups' info from IDs, unordered.

        Args:
            group_ids: One or more group ID(s) to query

        Returns:
            dict: :class:`Group` objects, labeled by their ID

        Raises:
            FBchatException: If request failed
        """
        threads = self.fetch_thread_info(*group_ids)
        groups = {}
        for id_, thread in threads.items():
            if thread.type == ThreadType.GROUP:
                groups[id_] = thread
            else:
                raise ValueError("Thread {} was not a group".format(thread))

        return groups

    def fetch_thread_info(self, *thread_ids):
        """Fetch threads' info from IDs, unordered.

        Warning:
            Sends two requests if users or pages are present, to fetch all available info!

        Args:
            thread_ids: One or more thread ID(s) to query

        Returns:
            dict: :class:`Thread` objects, labeled by their ID

        Raises:
            FBchatException: If request failed
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
            pages_and_users = self._fetch_info(*pages_and_user_ids)

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

    def fetch_thread_messages(self, thread_id=None, limit=20, before=None):
        """Fetch messages in a thread, ordered by most recent.

        Args:
            thread_id: User/Group ID to get messages from. See :ref:`intro_threads`
            limit (int): Max. number of messages to retrieve
            before (datetime.datetime): The point from which to retrieve messages

        Returns:
            list: :class:`Message` objects

        Raises:
            FBchatException: If request failed
        """
        params = {
            "id": thread_id,
            "message_limit": limit,
            "load_messages": True,
            "load_read_receipts": True,
            "before": _util.datetime_to_millis(before) if before else None,
        }
        j, = self.graphql_requests(_graphql.from_doc_id("1860982147341344", params))

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
                if (
                    _util.millis_to_datetime(int(receipt["watermark"]))
                    >= message.created_at
                ):
                    message.read_by.append(receipt["actor"]["id"])

        return messages

    def fetch_thread_list(
        self, limit=20, thread_location=ThreadLocation.INBOX, before=None
    ):
        """Fetch the client's thread list.

        Args:
            limit (int): Max. number of threads to retrieve. Capped at 20
            thread_location (ThreadLocation): INBOX, PENDING, ARCHIVED or OTHER
            before (datetime.datetime): The point from which to retrieve threads

        Returns:
            list: :class:`Thread` objects

        Raises:
            FBchatException: If request failed
        """
        if limit > 20 or limit < 1:
            raise ValueError("`limit` should be between 1 and 20")

        if thread_location in ThreadLocation:
            loc_str = thread_location.value
        else:
            raise TypeError('"thread_location" must be a value of ThreadLocation')

        params = {
            "limit": limit,
            "tags": [loc_str],
            "before": _util.datetime_to_millis(before) if before else None,
            "includeDeliveryReceipts": True,
            "includeSeqID": False,
        }
        j, = self.graphql_requests(_graphql.from_doc_id("1349387578499440", params))

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

    def fetch_unread(self):
        """Fetch unread threads.

        Returns:
            list: List of unread thread ids

        Raises:
            FBchatException: If request failed
        """
        form = {
            "folders[0]": "inbox",
            "client": "mercury",
            "last_action_timestamp": _util.now() - 60 * 1000
            # 'last_action_timestamp': 0
        }
        j = self._payload_post("/ajax/mercury/unread_threads.php", form)

        result = j["unread_thread_fbids"][0]
        return result["thread_fbids"] + result["other_user_fbids"]

    def fetch_unseen(self):
        """Fetch unseen / new threads.

        Returns:
            list: List of unseen thread ids

        Raises:
            FBchatException: If request failed
        """
        j = self._payload_post("/mercury/unseen_thread_ids/", {})

        result = j["unseen_thread_fbids"][0]
        return result["thread_fbids"] + result["other_user_fbids"]

    def fetch_image_url(self, image_id):
        """Fetch URL to download the original image from an image attachment ID.

        Args:
            image_id (str): The image you want to fetch

        Returns:
            str: An URL where you can download the original image

        Raises:
            FBchatException: If request failed
        """
        image_id = str(image_id)
        data = {"photo_id": str(image_id)}
        j = self._post("/mercury/attachments/photo/", data)
        _util.handle_payload_error(j)

        url = _util.get_jsmods_require(j, 3)
        if url is None:
            raise FBchatException("Could not fetch image URL from: {}".format(j))
        return url

    def fetch_message_info(self, mid, thread_id=None):
        """Fetch `Message` object from the given message id.

        Args:
            mid: Message ID to fetch from
            thread_id: User/Group ID to get message info from. See :ref:`intro_threads`

        Returns:
            Message: :class:`Message` object

        Raises:
            FBchatException: If request failed
        """
        message_info = self._forced_fetch(thread_id, mid).get("message")
        return Message._from_graphql(message_info)

    def fetch_poll_options(self, poll_id):
        """Fetch list of `PollOption` objects from the poll id.

        Args:
            poll_id: Poll ID to fetch from

        Returns:
            list

        Raises:
            FBchatException: If request failed
        """
        data = {"question_id": poll_id}
        j = self._payload_post("/ajax/mercury/get_poll_options", data)
        return [PollOption._from_graphql(m) for m in j]

    def fetch_plan_info(self, plan_id):
        """Fetch `Plan` object from the plan id.

        Args:
            plan_id: Plan ID to fetch from

        Returns:
            Plan: :class:`Plan` object

        Raises:
            FBchatException: If request failed
        """
        data = {"event_reminder_id": plan_id}
        j = self._payload_post("/ajax/eventreminder", data)
        return Plan._from_fetch(j)

    def _get_private_data(self):
        j, = self.graphql_requests(_graphql.from_doc_id("1868889766468115", {}))
        return j["viewer"]

    def get_phone_numbers(self):
        """Fetch list of user's phone numbers.

        Returns:
            list: List of phone numbers
        """
        data = self._get_private_data()
        return [
            j["phone_number"]["universal_number"] for j in data["user"]["all_phones"]
        ]

    def get_emails(self):
        """Fetch list of user's emails.

        Returns:
            list: List of emails
        """
        data = self._get_private_data()
        return [j["display_email"] for j in data["all_emails"]]

    def get_user_active_status(self, user_id):
        """Fetch friend active status as an `ActiveStatus` object.

        Return ``None`` if status isn't known.

        Warning:
            Only works when listening.

        Args:
            user_id: ID of the user

        Returns:
            ActiveStatus: Given user active status
        """
        return self._buddylist.get(str(user_id))

    def fetch_thread_images(self, thread_id=None):
        """Fetch images posted in thread.

        Args:
            thread_id: ID of the thread

        Returns:
            typing.Iterable: :class:`ImageAttachment` or :class:`VideoAttachment`
        """
        data = {"id": thread_id, "first": 48}
        thread_id = str(thread_id)
        j, = self.graphql_requests(_graphql.from_query_id("515216185516880", data))
        while True:
            try:
                i = j[thread_id]["message_shared_media"]["edges"][0]
            except IndexError:
                if j[thread_id]["message_shared_media"]["page_info"].get(
                    "has_next_page"
                ):
                    data["after"] = j[thread_id]["message_shared_media"][
                        "page_info"
                    ].get("end_cursor")
                    j, = self.graphql_requests(
                        _graphql.from_query_id("515216185516880", data)
                    )
                    continue
                else:
                    break

            if i["node"].get("__typename") == "MessageImage":
                yield ImageAttachment._from_list(i)
            elif i["node"].get("__typename") == "MessageVideo":
                yield VideoAttachment._from_list(i)
            else:
                yield Attachment(uid=i["node"].get("legacy_attachment_id"))
            del j[thread_id]["message_shared_media"]["edges"][0]

    """
    END FETCH METHODS
    """

    """
    SEND METHODS
    """

    def _old_message(self, message):
        return message if isinstance(message, Message) else Message(text=message)

    def _do_send_request(self, data, get_thread_id=False):
        """Send the data to `SendURL`, and returns the message ID or None on failure."""
        mid, thread_id = self._state._do_send_request(data)
        if get_thread_id:
            return mid, thread_id
        else:
            return mid

    def send(self, message, thread_id=None, thread_type=ThreadType.USER):
        """Send message to a thread.

        Args:
            message (Message): Message to send
            thread_id: User/Group ID to send to. See :ref:`intro_threads`
            thread_type (ThreadType): See :ref:`intro_threads`

        Returns:
            :ref:`Message ID <intro_message_ids>` of the sent message

        Raises:
            FBchatException: If request failed
        """
        thread = thread_type._to_class()(thread_id)
        data = thread._to_send_data()
        data.update(message._to_send_data())
        return self._do_send_request(data)

    def wave(self, wave_first=True, thread_id=None, thread_type=None):
        """Wave hello to a thread.

        Args:
            wave_first: Whether to wave first or wave back
            thread_id: User/Group ID to send to. See :ref:`intro_threads`
            thread_type (ThreadType): See :ref:`intro_threads`

        Returns:
            :ref:`Message ID <intro_message_ids>` of the sent message

        Raises:
            FBchatException: If request failed
        """
        thread = thread_type._to_class()(thread_id)
        data = thread._to_send_data()
        data["action_type"] = "ma-type:user-generated-message"
        data["lightweight_action_attachment[lwa_state]"] = (
            "INITIATED" if wave_first else "RECIPROCATED"
        )
        data["lightweight_action_attachment[lwa_type]"] = "WAVE"
        if thread_type == ThreadType.USER:
            data["specific_to_list[0]"] = "fbid:{}".format(thread_id)
        return self._do_send_request(data)

    def quick_reply(self, quick_reply, payload=None, thread_id=None, thread_type=None):
        """Reply to chosen quick reply.

        Args:
            quick_reply (QuickReply): Quick reply to reply to
            payload: Optional answer to the quick reply
            thread_id: User/Group ID to send to. See :ref:`intro_threads`
            thread_type (ThreadType): See :ref:`intro_threads`

        Returns:
            :ref:`Message ID <intro_message_ids>` of the sent message

        Raises:
            FBchatException: If request failed
        """
        quick_reply.is_response = True
        if isinstance(quick_reply, QuickReplyText):
            return self.send(
                Message(text=quick_reply.title, quick_replies=[quick_reply])
            )
        elif isinstance(quick_reply, QuickReplyLocation):
            if not isinstance(payload, LocationAttachment):
                raise TypeError(
                    "Payload must be an instance of `fbchat.LocationAttachment`"
                )
            return self.send_location(
                payload, thread_id=thread_id, thread_type=thread_type
            )
        elif isinstance(quick_reply, QuickReplyEmail):
            if not payload:
                payload = self.get_emails()[0]
            quick_reply.external_payload = quick_reply.payload
            quick_reply.payload = payload
            return self.send(Message(text=payload, quick_replies=[quick_reply]))
        elif isinstance(quick_reply, QuickReplyPhoneNumber):
            if not payload:
                payload = self.get_phone_numbers()[0]
            quick_reply.external_payload = quick_reply.payload
            quick_reply.payload = payload
            return self.send(Message(text=payload, quick_replies=[quick_reply]))

    def unsend(self, mid):
        """Unsend message by it's ID (removes it for everyone).

        Args:
            mid: :ref:`Message ID <intro_message_ids>` of the message to unsend
        """
        data = {"message_id": mid}
        j = self._payload_post("/messaging/unsend_message/?dpr=1", data)

    def _send_location(
        self, location, current=True, message=None, thread_id=None, thread_type=None
    ):
        thread = thread_type._to_class()(thread_id)
        data = thread._to_send_data()
        if message is not None:
            data.update(message._to_send_data())
        data["action_type"] = "ma-type:user-generated-message"
        data["location_attachment[coordinates][latitude]"] = location.latitude
        data["location_attachment[coordinates][longitude]"] = location.longitude
        data["location_attachment[is_current_location]"] = current
        return self._do_send_request(data)

    def send_location(self, location, message=None, thread_id=None, thread_type=None):
        """Send a given location to a thread as the user's current location.

        Args:
            location (LocationAttachment): Location to send
            message (Message): Additional message
            thread_id: User/Group ID to send to. See :ref:`intro_threads`
            thread_type (ThreadType): See :ref:`intro_threads`

        Returns:
            :ref:`Message ID <intro_message_ids>` of the sent message

        Raises:
            FBchatException: If request failed
        """
        self._send_location(
            location=location,
            current=True,
            message=message,
            thread_id=thread_id,
            thread_type=thread_type,
        )

    def send_pinned_location(
        self, location, message=None, thread_id=None, thread_type=None
    ):
        """Send a given location to a thread as a pinned location.

        Args:
            location (LocationAttachment): Location to send
            message (Message): Additional message
            thread_id: User/Group ID to send to. See :ref:`intro_threads`
            thread_type (ThreadType): See :ref:`intro_threads`

        Returns:
            :ref:`Message ID <intro_message_ids>` of the sent message

        Raises:
            FBchatException: If request failed
        """
        self._send_location(
            location=location,
            current=False,
            message=message,
            thread_id=thread_id,
            thread_type=thread_type,
        )

    def _upload(self, files, voice_clip=False):
        return self._state._upload(files, voice_clip=voice_clip)

    def _send_files(
        self, files, message=None, thread_id=None, thread_type=ThreadType.USER
    ):
        """Send files from file IDs to a thread.

        `files` should be a list of tuples, with a file's ID and mimetype.
        """
        thread = thread_type._to_class()(thread_id)
        data = thread._to_send_data()
        data.update(self._old_message(message)._to_send_data())
        data["action_type"] = "ma-type:user-generated-message"
        data["has_attachment"] = True

        for i, (file_id, mimetype) in enumerate(files):
            data["{}s[{}]".format(_util.mimetype_to_key(mimetype), i)] = file_id

        return self._do_send_request(data)

    def send_remote_files(
        self, file_urls, message=None, thread_id=None, thread_type=ThreadType.USER
    ):
        """Send files from URLs to a thread.

        Args:
            file_urls: URLs of files to upload and send
            message: Additional message
            thread_id: User/Group ID to send to. See :ref:`intro_threads`
            thread_type (ThreadType): See :ref:`intro_threads`

        Returns:
            :ref:`Message ID <intro_message_ids>` of the sent files

        Raises:
            FBchatException: If request failed
        """
        file_urls = _util.require_list(file_urls)
        files = self._upload(_util.get_files_from_urls(file_urls))
        return self._send_files(
            files=files, message=message, thread_id=thread_id, thread_type=thread_type
        )

    def send_local_files(
        self, file_paths, message=None, thread_id=None, thread_type=ThreadType.USER
    ):
        """Send local files to a thread.

        Args:
            file_paths: Paths of files to upload and send
            message: Additional message
            thread_id: User/Group ID to send to. See :ref:`intro_threads`
            thread_type (ThreadType): See :ref:`intro_threads`

        Returns:
            :ref:`Message ID <intro_message_ids>` of the sent files

        Raises:
            FBchatException: If request failed
        """
        file_paths = _util.require_list(file_paths)
        with _util.get_files_from_paths(file_paths) as x:
            files = self._upload(x)
        return self._send_files(
            files=files, message=message, thread_id=thread_id, thread_type=thread_type
        )

    def send_remote_voice_clips(
        self, clip_urls, message=None, thread_id=None, thread_type=ThreadType.USER
    ):
        """Send voice clips from URLs to a thread.

        Args:
            clip_urls: URLs of clips to upload and send
            message: Additional message
            thread_id: User/Group ID to send to. See :ref:`intro_threads`
            thread_type (ThreadType): See :ref:`intro_threads`

        Returns:
            :ref:`Message ID <intro_message_ids>` of the sent files

        Raises:
            FBchatException: If request failed
        """
        clip_urls = _util.require_list(clip_urls)
        files = self._upload(_util.get_files_from_urls(clip_urls), voice_clip=True)
        return self._send_files(
            files=files, message=message, thread_id=thread_id, thread_type=thread_type
        )

    def send_local_voice_clips(
        self, clip_paths, message=None, thread_id=None, thread_type=ThreadType.USER
    ):
        """Send local voice clips to a thread.

        Args:
            clip_paths: Paths of clips to upload and send
            message: Additional message
            thread_id: User/Group ID to send to. See :ref:`intro_threads`
            thread_type (ThreadType): See :ref:`intro_threads`

        Returns:
            :ref:`Message ID <intro_message_ids>` of the sent files

        Raises:
            FBchatException: If request failed
        """
        clip_paths = _util.require_list(clip_paths)
        with _util.get_files_from_paths(clip_paths) as x:
            files = self._upload(x, voice_clip=True)
        return self._send_files(
            files=files, message=message, thread_id=thread_id, thread_type=thread_type
        )

    def forward_attachment(self, attachment_id, thread_id=None):
        """Forward an attachment.

        Args:
            attachment_id: Attachment ID to forward
            thread_id: User/Group ID to send to. See :ref:`intro_threads`

        Raises:
            FBchatException: If request failed
        """
        data = {
            "attachment_id": attachment_id,
            "recipient_map[{}]".format(
                _util.generate_offline_threading_id()
            ): thread_id,
        }
        j = self._payload_post("/mercury/attachments/forward/", data)
        if not j.get("success"):
            raise FBchatFacebookError(
                "Failed forwarding attachment: {}".format(j["error"]),
                fb_error_message=j["error"],
            )

    def create_group(self, message, user_ids):
        """Create a group with the given user ids.

        Args:
            message: The initial message
            user_ids: A list of users to create the group with.

        Returns:
            ID of the new group

        Raises:
            FBchatException: If request failed
        """
        data = self._old_message(message)._to_send_data()

        if len(user_ids) < 2:
            raise ValueError("Error when creating group: Not enough participants")

        for i, user_id in enumerate(user_ids + [self._uid]):
            data["specific_to_list[{}]".format(i)] = "fbid:{}".format(user_id)

        message_id, thread_id = self._do_send_request(data, get_thread_id=True)
        if not thread_id:
            raise FBchatException(
                "Error when creating group: No thread_id could be found"
            )
        return thread_id

    def add_users_to_group(self, user_ids, thread_id=None):
        """Add users to a group.

        Args:
            user_ids (list): One or more user IDs to add
            thread_id: Group ID to add people to. See :ref:`intro_threads`

        Raises:
            FBchatException: If request failed
        """
        data = Group(thread_id)._to_send_data()

        data["action_type"] = "ma-type:log-message"
        data["log_message_type"] = "log:subscribe"

        user_ids = _util.require_list(user_ids)

        for i, user_id in enumerate(user_ids):
            if user_id == self._uid:
                raise ValueError(
                    "Error when adding users: Cannot add self to group thread"
                )
            else:
                data[
                    "log_message_data[added_participants][{}]".format(i)
                ] = "fbid:{}".format(user_id)

        return self._do_send_request(data)

    def remove_user_from_group(self, user_id, thread_id=None):
        """Remove user from a group.

        Args:
            user_id: User ID to remove
            thread_id: Group ID to remove people from. See :ref:`intro_threads`

        Raises:
            FBchatException: If request failed
        """
        data = {"uid": user_id, "tid": thread_id}
        j = self._payload_post("/chat/remove_participants/", data)

    def _admin_status(self, admin_ids, admin, thread_id=None):
        data = {"add": admin, "thread_fbid": thread_id}

        admin_ids = _util.require_list(admin_ids)

        for i, admin_id in enumerate(admin_ids):
            data["admin_ids[{}]".format(i)] = str(admin_id)

        j = self._payload_post("/messaging/save_admins/?dpr=1", data)

    def add_group_admins(self, admin_ids, thread_id=None):
        """Set specified users as group admins.

        Args:
            admin_ids: One or more user IDs to set admin
            thread_id: Group ID to remove people from. See :ref:`intro_threads`

        Raises:
            FBchatException: If request failed
        """
        self._admin_status(admin_ids, True, thread_id)

    def remove_group_admins(self, admin_ids, thread_id=None):
        """Remove admin status from specified users.

        Args:
            admin_ids: One or more user IDs to remove admin
            thread_id: Group ID to remove people from. See :ref:`intro_threads`

        Raises:
            FBchatException: If request failed
        """
        self._admin_status(admin_ids, False, thread_id)

    def change_group_approval_mode(self, require_admin_approval, thread_id=None):
        """Change group's approval mode.

        Args:
            require_admin_approval: True or False
            thread_id: Group ID to remove people from. See :ref:`intro_threads`

        Raises:
            FBchatException: If request failed
        """
        data = {"set_mode": int(require_admin_approval), "thread_fbid": thread_id}
        j = self._payload_post("/messaging/set_approval_mode/?dpr=1", data)

    def _users_approval(self, user_ids, approve, thread_id=None):
        user_ids = _util.require_list(user_ids)

        data = {
            "client_mutation_id": "0",
            "actor_id": self._uid,
            "thread_fbid": thread_id,
            "user_ids": user_ids,
            "response": "ACCEPT" if approve else "DENY",
            "surface": "ADMIN_MODEL_APPROVAL_CENTER",
        }
        j, = self.graphql_requests(
            _graphql.from_doc_id("1574519202665847", {"data": data})
        )

    def accept_users_to_group(self, user_ids, thread_id=None):
        """Accept users to the group from the group's approval.

        Args:
            user_ids: One or more user IDs to accept
            thread_id: Group ID to accept users to. See :ref:`intro_threads`

        Raises:
            FBchatException: If request failed
        """
        self._users_approval(user_ids, True, thread_id)

    def deny_users_from_group(self, user_ids, thread_id=None):
        """Deny users from joining the group.

        Args:
            user_ids: One or more user IDs to deny
            thread_id: Group ID to deny users from. See :ref:`intro_threads`

        Raises:
            FBchatException: If request failed
        """
        self._users_approval(user_ids, False, thread_id)

    def _change_group_image(self, image_id, thread_id=None):
        """Change a thread image from an image id.

        Args:
            image_id: ID of uploaded image
            thread_id: User/Group ID to change image. See :ref:`intro_threads`

        Raises:
            FBchatException: If request failed
        """
        data = {"thread_image_id": image_id, "thread_id": thread_id}

        j = self._payload_post("/messaging/set_thread_image/?dpr=1", data)
        return image_id

    def change_group_image_remote(self, image_url, thread_id=None):
        """Change a thread image from a URL.

        Args:
            image_url: URL of an image to upload and change
            thread_id: User/Group ID to change image. See :ref:`intro_threads`

        Raises:
            FBchatException: If request failed
        """
        (image_id, mimetype), = self._upload(_util.get_files_from_urls([image_url]))
        return self._change_group_image(image_id, thread_id)

    def change_group_image_local(self, image_path, thread_id=None):
        """Change a thread image from a local path.

        Args:
            image_path: Path of an image to upload and change
            thread_id: User/Group ID to change image. See :ref:`intro_threads`

        Raises:
            FBchatException: If request failed
        """
        with _util.get_files_from_paths([image_path]) as files:
            (image_id, mimetype), = self._upload(files)

        return self._change_group_image(image_id, thread_id)

    def change_thread_title(self, title, thread_id=None, thread_type=ThreadType.USER):
        """Change title of a thread.

        If this is executed on a user thread, this will change the nickname of that
        user, effectively changing the title.

        Args:
            title: New group thread title
            thread_id: Group ID to change title of. See :ref:`intro_threads`
            thread_type (ThreadType): See :ref:`intro_threads`

        Raises:
            FBchatException: If request failed
        """
        if thread_type == ThreadType.USER:
            # The thread is a user, so we change the user's nickname
            return self.change_nickname(
                title, thread_id, thread_id=thread_id, thread_type=thread_type
            )

        data = {"thread_name": title, "thread_id": thread_id}
        j = self._payload_post("/messaging/set_thread_name/?dpr=1", data)

    def change_nickname(
        self, nickname, user_id, thread_id=None, thread_type=ThreadType.USER
    ):
        """Change the nickname of a user in a thread.

        Args:
            nickname: New nickname
            user_id: User that will have their nickname changed
            thread_id: User/Group ID to change color of. See :ref:`intro_threads`
            thread_type (ThreadType): See :ref:`intro_threads`

        Raises:
            FBchatException: If request failed
        """
        data = {
            "nickname": nickname,
            "participant_id": user_id,
            "thread_or_other_fbid": thread_id,
        }
        j = self._payload_post(
            "/messaging/save_thread_nickname/?source=thread_settings&dpr=1", data
        )

    def change_thread_color(self, color, thread_id=None):
        """Change thread color.

        Args:
            color (ThreadColor): New thread color
            thread_id: User/Group ID to change color of. See :ref:`intro_threads`

        Raises:
            FBchatException: If request failed
        """
        data = {
            "color_choice": color.value if color != ThreadColor.MESSENGER_BLUE else "",
            "thread_or_other_fbid": thread_id,
        }
        j = self._payload_post(
            "/messaging/save_thread_color/?source=thread_settings&dpr=1", data
        )

    def change_thread_emoji(self, emoji, thread_id=None):
        """Change thread color.

        Note:
            While changing the emoji, the Facebook web client actually sends multiple
            different requests, though only this one is required to make the change.

        Args:
            color: New thread emoji
            thread_id: User/Group ID to change emoji of. See :ref:`intro_threads`

        Raises:
            FBchatException: If request failed
        """
        data = {"emoji_choice": emoji, "thread_or_other_fbid": thread_id}
        j = self._payload_post(
            "/messaging/save_thread_emoji/?source=thread_settings&dpr=1", data
        )

    def react_to_message(self, message_id, reaction):
        """React to a message, or removes reaction.

        Args:
            message_id: :ref:`Message ID <intro_message_ids>` to react to
            reaction (MessageReaction): Reaction emoji to use, if None removes reaction

        Raises:
            FBchatException: If request failed
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
        _util.handle_graphql_errors(j)

    def create_plan(self, plan, thread_id=None):
        """Set a plan.

        Args:
            plan (Plan): Plan to set
            thread_id: User/Group ID to send plan to. See :ref:`intro_threads`

        Raises:
            FBchatException: If request failed
        """
        data = {
            "event_type": "EVENT",
            "event_time": _util.datetime_to_seconds(plan.time),
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

    def edit_plan(self, plan, new_plan):
        """Edit a plan.

        Args:
            plan (Plan): Plan to edit
            new_plan: New plan

        Raises:
            FBchatException: If request failed
        """
        data = {
            "event_reminder_id": plan.uid,
            "delete": "false",
            "date": _util.datetime_to_seconds(new_plan.time),
            "location_name": new_plan.location or "",
            "location_id": new_plan.location_id or "",
            "title": new_plan.title,
            "acontext": ACONTEXT,
        }
        j = self._payload_post("/ajax/eventreminder/submit", data)

    def delete_plan(self, plan):
        """Delete a plan.

        Args:
            plan: Plan to delete

        Raises:
            FBchatException: If request failed
        """
        data = {"event_reminder_id": plan.uid, "delete": "true", "acontext": ACONTEXT}
        j = self._payload_post("/ajax/eventreminder/submit", data)

    def change_plan_participation(self, plan, take_part=True):
        """Change participation in a plan.

        Args:
            plan: Plan to take part in or not
            take_part: Whether to take part in the plan

        Raises:
            FBchatException: If request failed
        """
        data = {
            "event_reminder_id": plan.uid,
            "guest_state": "GOING" if take_part else "DECLINED",
            "acontext": ACONTEXT,
        }
        j = self._payload_post("/ajax/eventreminder/rsvp", data)

    def create_poll(self, poll, thread_id=None):
        """Create poll in a group thread.

        Args:
            poll (Poll): Poll to create
            thread_id: User/Group ID to create poll in. See :ref:`intro_threads`

        Raises:
            FBchatException: If request failed
        """
        # We're using ordered dictionaries, because the Facebook endpoint that parses
        # the POST parameters is badly implemented, and deals with ordering the options
        # wrongly. If you can find a way to fix this for the endpoint, or if you find
        # another endpoint, please do suggest it ;)
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

    def update_poll_vote(self, poll_id, option_ids=[], new_options=[]):
        """Update a poll vote.

        Args:
            poll_id: ID of the poll to update vote
            option_ids: List of the option IDs to vote
            new_options: List of the new option names
            thread_id: User/Group ID to change status in. See :ref:`intro_threads`
            thread_type (ThreadType): See :ref:`intro_threads`

        Raises:
            FBchatException: If request failed
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

    def set_typing_status(self, status, thread_id=None, thread_type=None):
        """Set users typing status in a thread.

        Args:
            status (TypingStatus): Specify the typing status
            thread_id: User/Group ID to change status in. See :ref:`intro_threads`
            thread_type (ThreadType): See :ref:`intro_threads`

        Raises:
            FBchatException: If request failed
        """
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

    def mark_as_delivered(self, thread_id, message_id):
        """Mark a message as delivered.

        Args:
            thread_id: User/Group ID to which the message belongs. See :ref:`intro_threads`
            message_id: Message ID to set as delivered. See :ref:`intro_threads`

        Returns:
            True

        Raises:
            FBchatException: If request failed
        """
        data = {
            "message_ids[0]": message_id,
            "thread_ids[%s][0]" % thread_id: message_id,
        }

        j = self._payload_post("/ajax/mercury/delivery_receipts.php", data)
        return True

    def _read_status(self, read, thread_ids):
        thread_ids = _util.require_list(thread_ids)

        data = {"watermarkTimestamp": _util.now(), "shouldSendReadReceipt": "true"}

        for thread_id in thread_ids:
            data["ids[{}]".format(thread_id)] = "true" if read else "false"

        j = self._payload_post("/ajax/mercury/change_read_status.php", data)

    def mark_as_read(self, thread_ids=None):
        """Mark threads as read.

        All messages inside the specified threads will be marked as read.

        Args:
            thread_ids: User/Group IDs to set as read. See :ref:`intro_threads`

        Raises:
            FBchatException: If request failed
        """
        self._read_status(True, thread_ids)

    def mark_as_unread(self, thread_ids=None):
        """Mark threads as unread.

        All messages inside the specified threads will be marked as unread.

        Args:
            thread_ids: User/Group IDs to set as unread. See :ref:`intro_threads`

        Raises:
            FBchatException: If request failed
        """
        self._read_status(False, thread_ids)

    def mark_as_seen(self):
        """
        Todo:
            Documenting this
        """
        j = self._payload_post(
            "/ajax/mercury/mark_seen.php", {"seen_timestamp": _util.now()}
        )

    def friend_connect(self, friend_id):
        """
        Todo:
            Documenting this
        """
        data = {"to_friend": friend_id, "action": "confirm"}

        j = self._payload_post("/ajax/add_friend/action.php?dpr=1", data)

    def remove_friend(self, friend_id=None):
        """Remove a specified friend from the client's friend list.

        Args:
            friend_id: The ID of the friend that you want to remove

        Returns:
            True

        Raises:
            FBchatException: If request failed
        """
        data = {"uid": friend_id}
        j = self._payload_post("/ajax/profile/removefriendconfirm.php", data)
        return True

    def block_user(self, user_id):
        """Block messages from a specified user.

        Args:
            user_id: The ID of the user that you want to block

        Returns:
            True

        Raises:
            FBchatException: If request failed
        """
        data = {"fbid": user_id}
        j = self._payload_post("/messaging/block_messages/?dpr=1", data)
        return True

    def unblock_user(self, user_id):
        """Unblock a previously blocked user.

        Args:
            user_id: The ID of the user that you want to unblock

        Returns:
            Whether the request was successful

        Raises:
            FBchatException: If request failed
        """
        data = {"fbid": user_id}
        j = self._payload_post("/messaging/unblock_messages/?dpr=1", data)
        return True

    def move_threads(self, location, thread_ids):
        """Move threads to specified location.

        Args:
            location (ThreadLocation): INBOX, PENDING, ARCHIVED or OTHER
            thread_ids: Thread IDs to move. See :ref:`intro_threads`

        Returns:
            True

        Raises:
            FBchatException: If request failed
        """
        thread_ids = _util.require_list(thread_ids)

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

    def delete_threads(self, thread_ids):
        """Delete threads.

        Args:
            thread_ids: Thread IDs to delete. See :ref:`intro_threads`

        Returns:
            True

        Raises:
            FBchatException: If request failed
        """
        thread_ids = _util.require_list(thread_ids)

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

    def mark_as_spam(self, thread_id=None):
        """Mark a thread as spam, and delete it.

        Args:
            thread_id: User/Group ID to mark as spam. See :ref:`intro_threads`

        Returns:
            True

        Raises:
            FBchatException: If request failed
        """
        j = self._payload_post("/ajax/mercury/mark_spam.php?dpr=1", {"id": thread_id})
        return True

    def delete_messages(self, message_ids):
        """Delete specified messages.

        Args:
            message_ids: Message IDs to delete

        Returns:
            True

        Raises:
            FBchatException: If request failed
        """
        message_ids = _util.require_list(message_ids)
        data = dict()
        for i, message_id in enumerate(message_ids):
            data["message_ids[{}]".format(i)] = message_id
        j = self._payload_post("/ajax/mercury/delete_messages.php?dpr=1", data)
        return True

    def mute_thread(self, mute_time=None, thread_id=None):
        """Mute thread.

        Args:
            mute_time (datetime.timedelta): Time to mute, use ``None`` to mute forever
            thread_id: User/Group ID to mute. See :ref:`intro_threads`
        """
        if mute_time is None:
            mute_settings = -1
        else:
            mute_settings = _util.timedelta_to_seconds(mute_time)
        data = {"mute_settings": str(mute_settings), "thread_fbid": thread_id}
        j = self._payload_post("/ajax/mercury/change_mute_thread.php?dpr=1", data)

    def unmute_thread(self, thread_id=None):
        """Unmute thread.

        Args:
            thread_id: User/Group ID to unmute. See :ref:`intro_threads`
        """
        return self.mute_thread(datetime.timedelta(0), thread_id)

    def mute_thread_reactions(self, mute=True, thread_id=None):
        """Mute thread reactions.

        Args:
            mute: Boolean. True to mute, False to unmute
            thread_id: User/Group ID to mute. See :ref:`intro_threads`
        """
        data = {"reactions_mute_mode": int(mute), "thread_fbid": thread_id}
        j = self._payload_post(
            "/ajax/mercury/change_reactions_mute_thread/?dpr=1", data
        )

    def unmute_thread_reactions(self, thread_id=None):
        """Unmute thread reactions.

        Args:
            thread_id: User/Group ID to unmute. See :ref:`intro_threads`
        """
        return self.mute_thread_reactions(False, thread_id)

    def mute_thread_mentions(self, mute=True, thread_id=None):
        """Mute thread mentions.

        Args:
            mute: Boolean. True to mute, False to unmute
            thread_id: User/Group ID to mute. See :ref:`intro_threads`
        """
        data = {"mentions_mute_mode": int(mute), "thread_fbid": thread_id}
        j = self._payload_post("/ajax/mercury/change_mentions_mute_thread/?dpr=1", data)

    def unmute_thread_mentions(self, thread_id=None):
        """Unmute thread mentions.

        Args:
            thread_id: User/Group ID to unmute. See :ref:`intro_threads`
        """
        return self.mute_thread_mentions(False, thread_id)

    """
    LISTEN METHODS
    """

    def _ping(self):
        data = {
            "seq": self._seq,
            "channel": "p_" + self._uid,
            "clientid": self._state._client_id,
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
        _util.handle_payload_error(j)

    def _pull_message(self):
        """Call pull api to fetch message data."""
        data = {
            "seq": self._seq,
            "msgs_recv": 0,
            "sticky_token": self._sticky,
            "sticky_pool": self._pool,
            "clientid": self._state._client_id,
            "state": "active" if self._mark_alive else "offline",
        }
        j = self._get(
            "https://{}-edge-chat.facebook.com/pull".format(self._pull_channel), data
        )
        _util.handle_payload_error(j)
        return j

    def _parse_delta(self, m):
        def get_thread_id_and_thread_type(msg_metadata):
            """Return a tuple consisting of thread ID and thread type."""
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
            at = _util.millis_to_datetime(int(metadata.get("timestamp")))

        # Added participants
        if "addedParticipants" in delta:
            added_ids = [str(x["userFbId"]) for x in delta["addedParticipants"]]
            thread_id = str(metadata["threadKey"]["threadFbId"])
            self.on_people_added(
                mid=mid,
                added_ids=added_ids,
                author_id=author_id,
                thread_id=thread_id,
                at=at,
                msg=m,
            )

        # Left/removed participants
        elif "leftParticipantFbId" in delta:
            removed_id = str(delta["leftParticipantFbId"])
            thread_id = str(metadata["threadKey"]["threadFbId"])
            self.on_person_removed(
                mid=mid,
                removed_id=removed_id,
                author_id=author_id,
                thread_id=thread_id,
                at=at,
                msg=m,
            )

        # Color change
        elif delta_type == "change_thread_theme":
            new_color = ThreadColor._from_graphql(delta["untypedData"]["theme_color"])
            thread_id, thread_type = get_thread_id_and_thread_type(metadata)
            self.on_color_change(
                mid=mid,
                author_id=author_id,
                new_color=new_color,
                thread_id=thread_id,
                thread_type=thread_type,
                at=at,
                metadata=metadata,
                msg=m,
            )

        # Emoji change
        elif delta_type == "change_thread_icon":
            new_emoji = delta["untypedData"]["thread_icon"]
            thread_id, thread_type = get_thread_id_and_thread_type(metadata)
            self.on_emoji_change(
                mid=mid,
                author_id=author_id,
                new_emoji=new_emoji,
                thread_id=thread_id,
                thread_type=thread_type,
                at=at,
                metadata=metadata,
                msg=m,
            )

        # Thread title change
        elif delta_class == "ThreadName":
            new_title = delta["name"]
            thread_id, thread_type = get_thread_id_and_thread_type(metadata)
            self.on_title_change(
                mid=mid,
                author_id=author_id,
                new_title=new_title,
                thread_id=thread_id,
                thread_type=thread_type,
                at=at,
                metadata=metadata,
                msg=m,
            )

        # Forced fetch
        elif delta_class == "ForcedFetch":
            mid = delta.get("messageId")
            if mid is None:
                self.on_unknown_messsage_type(msg=m)
            else:
                thread_id = str(delta["threadKey"]["threadFbId"])
                fetch_info = self._forced_fetch(thread_id, mid)
                fetch_data = fetch_info["message"]
                author_id = fetch_data["message_sender"]["id"]
                at = _util.millis_to_datetime(int(fetch_data["timestamp_precise"]))
                if fetch_data.get("__typename") == "ThreadImageMessage":
                    # Thread image change
                    image_metadata = fetch_data.get("image_with_metadata")
                    image_id = (
                        int(image_metadata["legacy_attachment_id"])
                        if image_metadata
                        else None
                    )
                    self.on_image_change(
                        mid=mid,
                        author_id=author_id,
                        new_image=image_id,
                        thread_id=thread_id,
                        thread_type=ThreadType.GROUP,
                        at=at,
                        msg=m,
                    )

        # Nickname change
        elif delta_type == "change_thread_nickname":
            changed_for = str(delta["untypedData"]["participant_id"])
            new_nickname = delta["untypedData"]["nickname"]
            thread_id, thread_type = get_thread_id_and_thread_type(metadata)
            self.on_nickname_change(
                mid=mid,
                author_id=author_id,
                changed_for=changed_for,
                new_nickname=new_nickname,
                thread_id=thread_id,
                thread_type=thread_type,
                at=at,
                metadata=metadata,
                msg=m,
            )

        # Admin added or removed in a group thread
        elif delta_type == "change_thread_admins":
            thread_id, thread_type = get_thread_id_and_thread_type(metadata)
            target_id = delta["untypedData"]["TARGET_ID"]
            admin_event = delta["untypedData"]["ADMIN_EVENT"]
            if admin_event == "add_admin":
                self.on_admin_added(
                    mid=mid,
                    added_id=target_id,
                    author_id=author_id,
                    thread_id=thread_id,
                    thread_type=thread_type,
                    at=at,
                    msg=m,
                )
            elif admin_event == "remove_admin":
                self.on_admin_removed(
                    mid=mid,
                    removed_id=target_id,
                    author_id=author_id,
                    thread_id=thread_id,
                    thread_type=thread_type,
                    at=at,
                    msg=m,
                )

        # Group approval mode change
        elif delta_type == "change_thread_approval_mode":
            thread_id, thread_type = get_thread_id_and_thread_type(metadata)
            approval_mode = bool(int(delta["untypedData"]["APPROVAL_MODE"]))
            self.on_approval_mode_change(
                mid=mid,
                approval_mode=approval_mode,
                author_id=author_id,
                thread_id=thread_id,
                thread_type=thread_type,
                at=at,
                msg=m,
            )

        # Message delivered
        elif delta_class == "DeliveryReceipt":
            message_ids = delta["messageIds"]
            delivered_for = str(
                delta.get("actorFbId") or delta["threadKey"]["otherUserFbId"]
            )
            at = _util.millis_to_datetime(int(delta["deliveredWatermarkTimestampMs"]))
            thread_id, thread_type = get_thread_id_and_thread_type(delta)
            self.on_message_delivered(
                msg_ids=message_ids,
                delivered_for=delivered_for,
                thread_id=thread_id,
                thread_type=thread_type,
                at=at,
                metadata=metadata,
                msg=m,
            )

        # Message seen
        elif delta_class == "ReadReceipt":
            seen_by = str(delta.get("actorFbId") or delta["threadKey"]["otherUserFbId"])
            seen_at = _util.millis_to_datetime(int(delta["actionTimestampMs"]))
            at = _util.millis_to_datetime(int(delta["watermarkTimestampMs"]))
            thread_id, thread_type = get_thread_id_and_thread_type(delta)
            self.on_message_seen(
                seen_by=seen_by,
                thread_id=thread_id,
                thread_type=thread_type,
                seen_at=seen_at,
                at=at,
                metadata=metadata,
                msg=m,
            )

        # Messages marked as seen
        elif delta_class == "MarkRead":
            seen_at = _util.millis_to_datetime(
                int(delta.get("actionTimestampMs") or delta.get("actionTimestamp"))
            )
            watermark_ts = delta.get("watermarkTimestampMs") or delta.get(
                "watermarkTimestamp"
            )
            at = _util.millis_to_datetime(int(watermark_ts))

            threads = []
            if "folders" not in delta:
                threads = [
                    get_thread_id_and_thread_type({"threadKey": thr})
                    for thr in delta.get("threadKeys")
                ]

            # thread_id, thread_type = get_thread_id_and_thread_type(delta)
            self.on_marked_seen(
                threads=threads, seen_at=seen_at, at=at, metadata=delta, msg=m
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
            thread_id, thread_type = get_thread_id_and_thread_type(metadata)
            self.on_game_played(
                mid=mid,
                author_id=author_id,
                game_id=game_id,
                game_name=game_name,
                score=score,
                leaderboard=leaderboard,
                thread_id=thread_id,
                thread_type=thread_type,
                at=at,
                metadata=metadata,
                msg=m,
            )

        # Group call started/ended
        elif delta_type == "rtc_call_log":
            thread_id, thread_type = get_thread_id_and_thread_type(metadata)
            call_status = delta["untypedData"]["event"]
            call_duration = _util.seconds_to_timedelta(
                int(delta["untypedData"]["call_duration"])
            )
            is_video_call = bool(int(delta["untypedData"]["is_video_call"]))
            if call_status == "call_started":
                self.on_call_started(
                    mid=mid,
                    caller_id=author_id,
                    is_video_call=is_video_call,
                    thread_id=thread_id,
                    thread_type=thread_type,
                    at=at,
                    metadata=metadata,
                    msg=m,
                )
            elif call_status == "call_ended":
                self.on_call_ended(
                    mid=mid,
                    caller_id=author_id,
                    is_video_call=is_video_call,
                    call_duration=call_duration,
                    thread_id=thread_id,
                    thread_type=thread_type,
                    at=at,
                    metadata=metadata,
                    msg=m,
                )

        # User joined to group call
        elif delta_type == "participant_joined_group_call":
            thread_id, thread_type = get_thread_id_and_thread_type(metadata)
            is_video_call = bool(int(delta["untypedData"]["group_call_type"]))
            self.on_user_joined_call(
                mid=mid,
                joined_id=author_id,
                is_video_call=is_video_call,
                thread_id=thread_id,
                thread_type=thread_type,
                at=at,
                metadata=metadata,
                msg=m,
            )

        # Group poll event
        elif delta_type == "group_poll":
            thread_id, thread_type = get_thread_id_and_thread_type(metadata)
            event_type = delta["untypedData"]["event_type"]
            poll_json = json.loads(delta["untypedData"]["question_json"])
            poll = Poll._from_graphql(poll_json)
            if event_type == "question_creation":
                # User created group poll
                self.on_poll_created(
                    mid=mid,
                    poll=poll,
                    author_id=author_id,
                    thread_id=thread_id,
                    thread_type=thread_type,
                    at=at,
                    metadata=metadata,
                    msg=m,
                )
            elif event_type == "update_vote":
                # User voted on group poll
                added_options = json.loads(delta["untypedData"]["added_option_ids"])
                removed_options = json.loads(delta["untypedData"]["removed_option_ids"])
                self.on_poll_voted(
                    mid=mid,
                    poll=poll,
                    added_options=added_options,
                    removed_options=removed_options,
                    author_id=author_id,
                    thread_id=thread_id,
                    thread_type=thread_type,
                    at=at,
                    metadata=metadata,
                    msg=m,
                )

        # Plan created
        elif delta_type == "lightweight_event_create":
            thread_id, thread_type = get_thread_id_and_thread_type(metadata)
            self.on_plan_created(
                mid=mid,
                plan=Plan._from_pull(delta["untypedData"]),
                author_id=author_id,
                thread_id=thread_id,
                thread_type=thread_type,
                at=at,
                metadata=metadata,
                msg=m,
            )

        # Plan ended
        elif delta_type == "lightweight_event_notify":
            thread_id, thread_type = get_thread_id_and_thread_type(metadata)
            self.on_plan_ended(
                mid=mid,
                plan=Plan._from_pull(delta["untypedData"]),
                thread_id=thread_id,
                thread_type=thread_type,
                at=at,
                metadata=metadata,
                msg=m,
            )

        # Plan edited
        elif delta_type == "lightweight_event_update":
            thread_id, thread_type = get_thread_id_and_thread_type(metadata)
            self.on_plan_edited(
                mid=mid,
                plan=Plan._from_pull(delta["untypedData"]),
                author_id=author_id,
                thread_id=thread_id,
                thread_type=thread_type,
                at=at,
                metadata=metadata,
                msg=m,
            )

        # Plan deleted
        elif delta_type == "lightweight_event_delete":
            thread_id, thread_type = get_thread_id_and_thread_type(metadata)
            self.on_plan_deleted(
                mid=mid,
                plan=Plan._from_pull(delta["untypedData"]),
                author_id=author_id,
                thread_id=thread_id,
                thread_type=thread_type,
                at=at,
                metadata=metadata,
                msg=m,
            )

        # Plan participation change
        elif delta_type == "lightweight_event_rsvp":
            thread_id, thread_type = get_thread_id_and_thread_type(metadata)
            take_part = delta["untypedData"]["guest_status"] == "GOING"
            self.on_plan_participation(
                mid=mid,
                plan=Plan._from_pull(delta["untypedData"]),
                take_part=take_part,
                author_id=author_id,
                thread_id=thread_id,
                thread_type=thread_type,
                at=at,
                metadata=metadata,
                msg=m,
            )

        # Client payload (that weird numbers)
        elif delta_class == "ClientPayload":
            payload = json.loads("".join(chr(z) for z in delta["payload"]))
            at = _util.millis_to_datetime(m.get("ofd_ts"))
            for d in payload.get("deltas", []):

                # Message reaction
                if d.get("deltaMessageReaction"):
                    i = d["deltaMessageReaction"]
                    thread_id, thread_type = get_thread_id_and_thread_type(i)
                    mid = i["messageId"]
                    author_id = str(i["userId"])
                    reaction = (
                        MessageReaction(i["reaction"]) if i.get("reaction") else None
                    )
                    add_reaction = not bool(i["action"])
                    if add_reaction:
                        self.on_reaction_added(
                            mid=mid,
                            reaction=reaction,
                            author_id=author_id,
                            thread_id=thread_id,
                            thread_type=thread_type,
                            at=at,
                            msg=m,
                        )
                    else:
                        self.on_reaction_removed(
                            mid=mid,
                            author_id=author_id,
                            thread_id=thread_id,
                            thread_type=thread_type,
                            at=at,
                            msg=m,
                        )

                # Viewer status change
                elif d.get("deltaChangeViewerStatus"):
                    i = d["deltaChangeViewerStatus"]
                    thread_id, thread_type = get_thread_id_and_thread_type(i)
                    author_id = str(i["actorFbid"])
                    reason = i["reason"]
                    can_reply = i["canViewerReply"]
                    if reason == 2:
                        if can_reply:
                            self.on_unblock(
                                author_id=author_id,
                                thread_id=thread_id,
                                thread_type=thread_type,
                                at=at,
                                msg=m,
                            )
                        else:
                            self.on_block(
                                author_id=author_id,
                                thread_id=thread_id,
                                thread_type=thread_type,
                                at=at,
                                msg=m,
                            )

                # Live location info
                elif d.get("liveLocationData"):
                    i = d["liveLocationData"]
                    thread_id, thread_type = get_thread_id_and_thread_type(i)
                    for l in i["messageLiveLocations"]:
                        mid = l["messageId"]
                        author_id = str(l["senderId"])
                        location = LiveLocationAttachment._from_pull(l)
                        self.on_live_location(
                            mid=mid,
                            location=location,
                            author_id=author_id,
                            thread_id=thread_id,
                            thread_type=thread_type,
                            at=at,
                            msg=m,
                        )

                # Message deletion
                elif d.get("deltaRecallMessageData"):
                    i = d["deltaRecallMessageData"]
                    thread_id, thread_type = get_thread_id_and_thread_type(i)
                    mid = i["messageID"]
                    at = _util.millis_to_datetime(i["deletionTimestamp"])
                    author_id = str(i["senderID"])
                    self.on_message_unsent(
                        mid=mid,
                        author_id=author_id,
                        thread_id=thread_id,
                        thread_type=thread_type,
                        at=at,
                        msg=m,
                    )

                elif d.get("deltaMessageReply"):
                    i = d["deltaMessageReply"]
                    metadata = i["message"]["messageMetadata"]
                    thread_id, thread_type = get_thread_id_and_thread_type(metadata)
                    message = Message._from_reply(i["message"])
                    message.replied_to = Message._from_reply(i["repliedToMessage"])
                    message.reply_to_id = message.replied_to.uid
                    self.on_message(
                        mid=message.uid,
                        author_id=message.author,
                        message_object=message,
                        thread_id=thread_id,
                        thread_type=thread_type,
                        at=message.created_at,
                        metadata=metadata,
                        msg=m,
                    )

        # New message
        elif delta.get("class") == "NewMessage":
            thread_id, thread_type = get_thread_id_and_thread_type(metadata)
            self.on_message(
                mid=mid,
                author_id=author_id,
                message_object=Message._from_pull(
                    delta,
                    mid=mid,
                    tags=metadata.get("tags"),
                    author=author_id,
                    created_at=at,
                ),
                thread_id=thread_id,
                thread_type=thread_type,
                at=at,
                metadata=metadata,
                msg=m,
            )

        # Unknown message type
        else:
            self.on_unknown_messsage_type(msg=m)

    def _parse_message(self, content):
        """Get message and author name from content.

        May contain multiple messages in the content.
        """
        self._seq = content.get("seq", "0")

        if "lb_info" in content:
            self._sticky = content["lb_info"]["sticky"]
            self._pool = content["lb_info"]["pool"]

        if "batches" in content:
            for batch in content["batches"]:
                self._parse_message(batch)

        if "ms" not in content:
            return

        for m in content["ms"]:
            mtype = m.get("type")
            try:
                # Things that directly change chat
                if mtype == "delta":
                    self._parse_delta(m)
                # Inbox
                elif mtype == "inbox":
                    self.on_inbox(
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
                    self.on_typing(
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
                #     self.on_seen(m.get('realtime_viewer_fbid'), m.get('reader'), m.get('time'))

                elif mtype in ["jewel_requests_add"]:
                    from_id = m["from"]
                    self.on_friend_request(from_id=from_id, msg=m)

                # Happens on every login
                elif mtype == "qprimer":
                    self.on_qprimer(
                        at=_util.millis_to_datetime(int(m.get("made"))), msg=m
                    )

                # Is sent before any other message
                elif mtype == "deltaflow":
                    pass

                # Chat timestamp
                elif mtype == "chatproxy-presence":
                    statuses = dict()
                    for id_, data in m.get("buddyList", {}).items():
                        statuses[id_] = ActiveStatus._from_chatproxy_presence(id_, data)
                        self._buddylist[id_] = statuses[id_]

                    self.on_chat_timestamp(buddylist=statuses, msg=m)

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

                    self.on_buddylist_overlay(statuses=statuses, msg=m)

                # Unknown message type
                else:
                    self.on_unknown_messsage_type(msg=m)

            except Exception as e:
                self.on_message_error(exception=e, msg=m)

    def _do_one_listen(self):
        try:
            if self._mark_alive:
                self._ping()
            content = self._pull_message()
            if content:
                self._parse_message(content)
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
            else:
                raise e
        except Exception as e:
            return self.on_listen_error(exception=e)

        return True

    def listen(self, markAlive=None):
        """Initialize and runs the listening loop continually.

        Args:
            markAlive (bool): Whether this should ping the Facebook server each time the loop runs
        """
        if markAlive is not None:
            self.set_active_status(markAlive)

        self.on_listening()

        while self._do_one_listen():
            pass

        self._sticky, self._pool = (None, None)

    def set_active_status(self, markAlive):
        """Change active status while listening.

        Args:
            markAlive (bool): Whether to show if client is active
        """
        self._mark_alive = markAlive

    """
    END LISTEN METHODS
    """

    """
    EVENTS
    """

    def on_logging_in(self, email=None):
        """Called when the client is logging in.

        Args:
            email: The email of the client
        """
        log.info("Logging in {}...".format(email))

    def on_2fa_code(self):
        """Called when a 2FA code is needed to progress."""
        return input("Please enter your 2FA code --> ")

    def on_logged_in(self, email=None):
        """Called when the client is successfully logged in.

        Args:
            email: The email of the client
        """
        log.info("Login of {} successful.".format(email))

    def on_listening(self):
        """Called when the client is listening."""
        log.info("Listening...")

    def on_listen_error(self, exception=None):
        """Called when an error was encountered while listening.

        Args:
            exception: The exception that was encountered

        Returns:
            Whether the loop should keep running
        """
        log.exception("Got exception while listening")
        return True

    def on_message(
        self,
        mid=None,
        author_id=None,
        message_object=None,
        thread_id=None,
        thread_type=ThreadType.USER,
        at=None,
        metadata=None,
        msg=None,
    ):
        """Called when the client is listening, and somebody sends a message.

        Args:
            mid: The message ID
            author_id: The ID of the author
            message_object (Message): The message (As a `Message` object)
            thread_id: Thread ID that the message was sent to. See :ref:`intro_threads`
            thread_type (ThreadType): Type of thread that the message was sent to. See :ref:`intro_threads`
            at (datetime.datetime): When the message was sent
            metadata: Extra metadata about the message
            msg: A full set of the data received
        """
        log.info("{} from {} in {}".format(message_object, thread_id, thread_type.name))

    def on_color_change(
        self,
        mid=None,
        author_id=None,
        new_color=None,
        thread_id=None,
        thread_type=ThreadType.USER,
        at=None,
        metadata=None,
        msg=None,
    ):
        """Called when the client is listening, and somebody changes a thread's color.

        Args:
            mid: The action ID
            author_id: The ID of the person who changed the color
            new_color (ThreadColor): The new color
            thread_id: Thread ID that the action was sent to. See :ref:`intro_threads`
            thread_type (ThreadType): Type of thread that the action was sent to. See :ref:`intro_threads`
            at (datetime.datetime): When the action was executed
            metadata: Extra metadata about the action
            msg: A full set of the data received
        """
        log.info(
            "Color change from {} in {} ({}): {}".format(
                author_id, thread_id, thread_type.name, new_color
            )
        )

    def on_emoji_change(
        self,
        mid=None,
        author_id=None,
        new_emoji=None,
        thread_id=None,
        thread_type=ThreadType.USER,
        at=None,
        metadata=None,
        msg=None,
    ):
        """Called when the client is listening, and somebody changes a thread's emoji.

        Args:
            mid: The action ID
            author_id: The ID of the person who changed the emoji
            new_emoji: The new emoji
            thread_id: Thread ID that the action was sent to. See :ref:`intro_threads`
            thread_type (ThreadType): Type of thread that the action was sent to. See :ref:`intro_threads`
            at (datetime.datetime): When the action was executed
            metadata: Extra metadata about the action
            msg: A full set of the data received
        """
        log.info(
            "Emoji change from {} in {} ({}): {}".format(
                author_id, thread_id, thread_type.name, new_emoji
            )
        )

    def on_title_change(
        self,
        mid=None,
        author_id=None,
        new_title=None,
        thread_id=None,
        thread_type=ThreadType.USER,
        at=None,
        metadata=None,
        msg=None,
    ):
        """Called when the client is listening, and somebody changes a thread's title.

        Args:
            mid: The action ID
            author_id: The ID of the person who changed the title
            new_title: The new title
            thread_id: Thread ID that the action was sent to. See :ref:`intro_threads`
            thread_type (ThreadType): Type of thread that the action was sent to. See :ref:`intro_threads`
            at (datetime.datetime): When the action was executed
            metadata: Extra metadata about the action
            msg: A full set of the data received
        """
        log.info(
            "Title change from {} in {} ({}): {}".format(
                author_id, thread_id, thread_type.name, new_title
            )
        )

    def on_image_change(
        self,
        mid=None,
        author_id=None,
        new_image=None,
        thread_id=None,
        thread_type=ThreadType.GROUP,
        at=None,
        msg=None,
    ):
        """Called when the client is listening, and somebody changes a thread's image.

        Args:
            mid: The action ID
            author_id: The ID of the person who changed the image
            new_image: The ID of the new image
            thread_id: Thread ID that the action was sent to. See :ref:`intro_threads`
            thread_type (ThreadType): Type of thread that the action was sent to. See :ref:`intro_threads`
            at (datetime.datetime): When the action was executed
            msg: A full set of the data received
        """
        log.info("{} changed thread image in {}".format(author_id, thread_id))

    def on_nickname_change(
        self,
        mid=None,
        author_id=None,
        changed_for=None,
        new_nickname=None,
        thread_id=None,
        thread_type=ThreadType.USER,
        at=None,
        metadata=None,
        msg=None,
    ):
        """Called when the client is listening, and somebody changes a nickname.

        Args:
            mid: The action ID
            author_id: The ID of the person who changed the nickname
            changed_for: The ID of the person whom got their nickname changed
            new_nickname: The new nickname
            thread_id: Thread ID that the action was sent to. See :ref:`intro_threads`
            thread_type (ThreadType): Type of thread that the action was sent to. See :ref:`intro_threads`
            at (datetime.datetime): When the action was executed
            metadata: Extra metadata about the action
            msg: A full set of the data received
        """
        log.info(
            "Nickname change from {} in {} ({}) for {}: {}".format(
                author_id, thread_id, thread_type.name, changed_for, new_nickname
            )
        )

    def on_admin_added(
        self,
        mid=None,
        added_id=None,
        author_id=None,
        thread_id=None,
        thread_type=ThreadType.GROUP,
        at=None,
        msg=None,
    ):
        """Called when the client is listening, and somebody adds an admin to a group.

        Args:
            mid: The action ID
            added_id: The ID of the admin who got added
            author_id: The ID of the person who added the admins
            thread_id: Thread ID that the action was sent to. See :ref:`intro_threads`
            at (datetime.datetime): When the action was executed
            msg: A full set of the data received
        """
        log.info("{} added admin: {} in {}".format(author_id, added_id, thread_id))

    def on_admin_removed(
        self,
        mid=None,
        removed_id=None,
        author_id=None,
        thread_id=None,
        thread_type=ThreadType.GROUP,
        at=None,
        msg=None,
    ):
        """Called when the client is listening, and somebody is removed as an admin in a group.

        Args:
            mid: The action ID
            removed_id: The ID of the admin who got removed
            author_id: The ID of the person who removed the admins
            thread_id: Thread ID that the action was sent to. See :ref:`intro_threads`
            at (datetime.datetime): When the action was executed
            msg: A full set of the data received
        """
        log.info("{} removed admin: {} in {}".format(author_id, removed_id, thread_id))

    def on_approval_mode_change(
        self,
        mid=None,
        approval_mode=None,
        author_id=None,
        thread_id=None,
        thread_type=ThreadType.GROUP,
        at=None,
        msg=None,
    ):
        """Called when the client is listening, and somebody changes approval mode in a group.

        Args:
            mid: The action ID
            approval_mode: True if approval mode is activated
            author_id: The ID of the person who changed approval mode
            thread_id: Thread ID that the action was sent to. See :ref:`intro_threads`
            at (datetime.datetime): When the action was executed
            msg: A full set of the data received
        """
        if approval_mode:
            log.info("{} activated approval mode in {}".format(author_id, thread_id))
        else:
            log.info("{} disabled approval mode in {}".format(author_id, thread_id))

    def on_message_seen(
        self,
        seen_by=None,
        thread_id=None,
        thread_type=ThreadType.USER,
        seen_at=None,
        at=None,
        metadata=None,
        msg=None,
    ):
        """Called when the client is listening, and somebody marks a message as seen.

        Args:
            seen_by: The ID of the person who marked the message as seen
            thread_id: Thread ID that the action was sent to. See :ref:`intro_threads`
            thread_type (ThreadType): Type of thread that the action was sent to. See :ref:`intro_threads`
            seen_at (datetime.datetime): When the person saw the message
            at (datetime.datetime): When the action was executed
            metadata: Extra metadata about the action
            msg: A full set of the data received
        """
        log.info(
            "Messages seen by {} in {} ({}) at {}".format(
                seen_by, thread_id, thread_type.name, seen_at
            )
        )

    def on_message_delivered(
        self,
        msg_ids=None,
        delivered_for=None,
        thread_id=None,
        thread_type=ThreadType.USER,
        at=None,
        metadata=None,
        msg=None,
    ):
        """Called when the client is listening, and somebody marks messages as delivered.

        Args:
            msg_ids: The messages that are marked as delivered
            delivered_for: The person that marked the messages as delivered
            thread_id: Thread ID that the action was sent to. See :ref:`intro_threads`
            thread_type (ThreadType): Type of thread that the action was sent to. See :ref:`intro_threads`
            at (datetime.datetime): When the action was executed
            metadata: Extra metadata about the action
            msg: A full set of the data received
        """
        log.info(
            "Messages {} delivered to {} in {} ({}) at {}".format(
                msg_ids, delivered_for, thread_id, thread_type.name, at
            )
        )

    def on_marked_seen(
        self, threads=None, seen_at=None, at=None, metadata=None, msg=None
    ):
        """Called when the client is listening, and the client has successfully marked threads as seen.

        Args:
            threads: The threads that were marked
            author_id: The ID of the person who changed the emoji
            seen_at (datetime.datetime): When the threads were seen
            at (datetime.datetime): When the action was executed
            metadata: Extra metadata about the action
            msg: A full set of the data received
        """
        log.info(
            "Marked messages as seen in threads {} at {}".format(
                [(x[0], x[1].name) for x in threads], seen_at
            )
        )

    def on_message_unsent(
        self,
        mid=None,
        author_id=None,
        thread_id=None,
        thread_type=None,
        at=None,
        msg=None,
    ):
        """Called when the client is listening, and someone unsends (deletes for everyone) a message.

        Args:
            mid: ID of the unsent message
            author_id: The ID of the person who unsent the message
            thread_id: Thread ID that the action was sent to. See :ref:`intro_threads`
            thread_type (ThreadType): Type of thread that the action was sent to. See :ref:`intro_threads`
            at (datetime.datetime): When the action was executed
            msg: A full set of the data received
        """
        log.info(
            "{} unsent the message {} in {} ({}) at {}".format(
                author_id, repr(mid), thread_id, thread_type.name, at
            )
        )

    def on_people_added(
        self,
        mid=None,
        added_ids=None,
        author_id=None,
        thread_id=None,
        at=None,
        msg=None,
    ):
        """Called when the client is listening, and somebody adds people to a group thread.

        Args:
            mid: The action ID
            added_ids: The IDs of the people who got added
            author_id: The ID of the person who added the people
            thread_id: Thread ID that the action was sent to. See :ref:`intro_threads`
            at (datetime.datetime): When the action was executed
            msg: A full set of the data received
        """
        log.info(
            "{} added: {} in {}".format(author_id, ", ".join(added_ids), thread_id)
        )

    def on_person_removed(
        self,
        mid=None,
        removed_id=None,
        author_id=None,
        thread_id=None,
        at=None,
        msg=None,
    ):
        """Called when the client is listening, and somebody removes a person from a group thread.

        Args:
            mid: The action ID
            removed_id: The ID of the person who got removed
            author_id: The ID of the person who removed the person
            thread_id: Thread ID that the action was sent to. See :ref:`intro_threads`
            at (datetime.datetime): When the action was executed
            msg: A full set of the data received
        """
        log.info("{} removed: {} in {}".format(author_id, removed_id, thread_id))

    def on_friend_request(self, from_id=None, msg=None):
        """Called when the client is listening, and somebody sends a friend request.

        Args:
            from_id: The ID of the person that sent the request
            msg: A full set of the data received
        """
        log.info("Friend request from {}".format(from_id))

    def on_inbox(self, unseen=None, unread=None, recent_unread=None, msg=None):
        """
        Todo:
            Documenting this

        Args:
            unseen: --
            unread: --
            recent_unread: --
            msg: A full set of the data received
        """
        log.info("Inbox event: {}, {}, {}".format(unseen, unread, recent_unread))

    def on_typing(
        self, author_id=None, status=None, thread_id=None, thread_type=None, msg=None
    ):
        """Called when the client is listening, and somebody starts or stops typing into a chat.

        Args:
            author_id: The ID of the person who sent the action
            status (TypingStatus): The typing status
            thread_id: Thread ID that the action was sent to. See :ref:`intro_threads`
            thread_type (ThreadType): Type of thread that the action was sent to. See :ref:`intro_threads`
            msg: A full set of the data received
        """
        pass

    def on_game_played(
        self,
        mid=None,
        author_id=None,
        game_id=None,
        game_name=None,
        score=None,
        leaderboard=None,
        thread_id=None,
        thread_type=None,
        at=None,
        metadata=None,
        msg=None,
    ):
        """Called when the client is listening, and somebody plays a game.

        Args:
            mid: The action ID
            author_id: The ID of the person who played the game
            game_id: The ID of the game
            game_name: Name of the game
            score: Score obtained in the game
            leaderboard: Actual leader board of the game in the thread
            thread_id: Thread ID that the action was sent to. See :ref:`intro_threads`
            thread_type (ThreadType): Type of thread that the action was sent to. See :ref:`intro_threads`
            at (datetime.datetime): When the action was executed
            metadata: Extra metadata about the action
            msg: A full set of the data received
        """
        log.info(
            '{} played "{}" in {} ({})'.format(
                author_id, game_name, thread_id, thread_type.name
            )
        )

    def on_reaction_added(
        self,
        mid=None,
        reaction=None,
        author_id=None,
        thread_id=None,
        thread_type=None,
        at=None,
        msg=None,
    ):
        """Called when the client is listening, and somebody reacts to a message.

        Args:
            mid: Message ID, that user reacted to
            reaction (MessageReaction): Reaction
            add_reaction: Whether user added or removed reaction
            author_id: The ID of the person who reacted to the message
            thread_id: Thread ID that the action was sent to. See :ref:`intro_threads`
            thread_type (ThreadType): Type of thread that the action was sent to. See :ref:`intro_threads`
            at (datetime.datetime): When the action was executed
            msg: A full set of the data received
        """
        log.info(
            "{} reacted to message {} with {} in {} ({})".format(
                author_id, mid, reaction.name, thread_id, thread_type.name
            )
        )

    def on_reaction_removed(
        self,
        mid=None,
        author_id=None,
        thread_id=None,
        thread_type=None,
        at=None,
        msg=None,
    ):
        """Called when the client is listening, and somebody removes reaction from a message.

        Args:
            mid: Message ID, that user reacted to
            author_id: The ID of the person who removed reaction
            thread_id: Thread ID that the action was sent to. See :ref:`intro_threads`
            thread_type (ThreadType): Type of thread that the action was sent to. See :ref:`intro_threads`
            at (datetime.datetime): When the action was executed
            msg: A full set of the data received
        """
        log.info(
            "{} removed reaction from {} message in {} ({})".format(
                author_id, mid, thread_id, thread_type
            )
        )

    def on_block(
        self, author_id=None, thread_id=None, thread_type=None, at=None, msg=None
    ):
        """Called when the client is listening, and somebody blocks client.

        Args:
            author_id: The ID of the person who blocked
            thread_id: Thread ID that the action was sent to. See :ref:`intro_threads`
            thread_type (ThreadType): Type of thread that the action was sent to. See :ref:`intro_threads`
            at (datetime.datetime): When the action was executed
            msg: A full set of the data received
        """
        log.info(
            "{} blocked {} ({}) thread".format(author_id, thread_id, thread_type.name)
        )

    def on_unblock(
        self, author_id=None, thread_id=None, thread_type=None, at=None, msg=None
    ):
        """Called when the client is listening, and somebody blocks client.

        Args:
            author_id: The ID of the person who unblocked
            thread_id: Thread ID that the action was sent to. See :ref:`intro_threads`
            thread_type (ThreadType): Type of thread that the action was sent to. See :ref:`intro_threads`
            at (datetime.datetime): When the action was executed
            msg: A full set of the data received
        """
        log.info(
            "{} unblocked {} ({}) thread".format(author_id, thread_id, thread_type.name)
        )

    def on_live_location(
        self,
        mid=None,
        location=None,
        author_id=None,
        thread_id=None,
        thread_type=None,
        at=None,
        msg=None,
    ):
        """Called when the client is listening and somebody sends live location info.

        Args:
            mid: The action ID
            location (LiveLocationAttachment): Sent location info
            author_id: The ID of the person who sent location info
            thread_id: Thread ID that the action was sent to. See :ref:`intro_threads`
            thread_type (ThreadType): Type of thread that the action was sent to. See :ref:`intro_threads`
            at (datetime.datetime): When the action was executed
            msg: A full set of the data received
        """
        log.info(
            "{} sent live location info in {} ({}) with latitude {} and longitude {}".format(
                author_id, thread_id, thread_type, location.latitude, location.longitude
            )
        )

    def on_call_started(
        self,
        mid=None,
        caller_id=None,
        is_video_call=None,
        thread_id=None,
        thread_type=None,
        at=None,
        metadata=None,
        msg=None,
    ):
        """Called when the client is listening, and somebody starts a call in a group.

        Todo:
            Make this work with private calls.

        Args:
            mid: The action ID
            caller_id: The ID of the person who started the call
            is_video_call: True if it's video call
            thread_id: Thread ID that the action was sent to. See :ref:`intro_threads`
            thread_type (ThreadType): Type of thread that the action was sent to. See :ref:`intro_threads`
            at (datetime.datetime): When the action was executed
            metadata: Extra metadata about the action
            msg: A full set of the data received
        """
        log.info(
            "{} started call in {} ({})".format(caller_id, thread_id, thread_type.name)
        )

    def on_call_ended(
        self,
        mid=None,
        caller_id=None,
        is_video_call=None,
        call_duration=None,
        thread_id=None,
        thread_type=None,
        at=None,
        metadata=None,
        msg=None,
    ):
        """Called when the client is listening, and somebody ends a call in a group.

        Todo:
            Make this work with private calls.

        Args:
            mid: The action ID
            caller_id: The ID of the person who ended the call
            is_video_call: True if it was video call
            call_duration (datetime.timedelta): Call duration
            thread_id: Thread ID that the action was sent to. See :ref:`intro_threads`
            thread_type (ThreadType): Type of thread that the action was sent to. See :ref:`intro_threads`
            at (datetime.datetime): When the action was executed
            metadata: Extra metadata about the action
            msg: A full set of the data received
        """
        log.info(
            "{} ended call in {} ({})".format(caller_id, thread_id, thread_type.name)
        )

    def on_user_joined_call(
        self,
        mid=None,
        joined_id=None,
        is_video_call=None,
        thread_id=None,
        thread_type=None,
        at=None,
        metadata=None,
        msg=None,
    ):
        """Called when the client is listening, and somebody joins a group call.

        Args:
            mid: The action ID
            joined_id: The ID of the person who joined the call
            is_video_call: True if it's video call
            thread_id: Thread ID that the action was sent to. See :ref:`intro_threads`
            thread_type (ThreadType): Type of thread that the action was sent to. See :ref:`intro_threads`
            at (datetime.datetime): When the action was executed
            metadata: Extra metadata about the action
            msg: A full set of the data received
        """
        log.info(
            "{} joined call in {} ({})".format(joined_id, thread_id, thread_type.name)
        )

    def on_poll_created(
        self,
        mid=None,
        poll=None,
        author_id=None,
        thread_id=None,
        thread_type=None,
        at=None,
        metadata=None,
        msg=None,
    ):
        """Called when the client is listening, and somebody creates a group poll.

        Args:
            mid: The action ID
            poll (Poll): Created poll
            author_id: The ID of the person who created the poll
            thread_id: Thread ID that the action was sent to. See :ref:`intro_threads`
            thread_type (ThreadType): Type of thread that the action was sent to. See :ref:`intro_threads`
            at (datetime.datetime): When the action was executed
            metadata: Extra metadata about the action
            msg: A full set of the data received
        """
        log.info(
            "{} created poll {} in {} ({})".format(
                author_id, poll, thread_id, thread_type.name
            )
        )

    def on_poll_voted(
        self,
        mid=None,
        poll=None,
        added_options=None,
        removed_options=None,
        author_id=None,
        thread_id=None,
        thread_type=None,
        at=None,
        metadata=None,
        msg=None,
    ):
        """Called when the client is listening, and somebody votes in a group poll.

        Args:
            mid: The action ID
            poll (Poll): Poll, that user voted in
            author_id: The ID of the person who voted in the poll
            thread_id: Thread ID that the action was sent to. See :ref:`intro_threads`
            thread_type (ThreadType): Type of thread that the action was sent to. See :ref:`intro_threads`
            at (datetime.datetime): When the action was executed
            metadata: Extra metadata about the action
            msg: A full set of the data received
        """
        log.info(
            "{} voted in poll {} in {} ({})".format(
                author_id, poll, thread_id, thread_type.name
            )
        )

    def on_plan_created(
        self,
        mid=None,
        plan=None,
        author_id=None,
        thread_id=None,
        thread_type=None,
        at=None,
        metadata=None,
        msg=None,
    ):
        """Called when the client is listening, and somebody creates a plan.

        Args:
            mid: The action ID
            plan (Plan): Created plan
            author_id: The ID of the person who created the plan
            thread_id: Thread ID that the action was sent to. See :ref:`intro_threads`
            thread_type (ThreadType): Type of thread that the action was sent to. See :ref:`intro_threads`
            at (datetime.datetime): When the action was executed
            metadata: Extra metadata about the action
            msg: A full set of the data received
        """
        log.info(
            "{} created plan {} in {} ({})".format(
                author_id, plan, thread_id, thread_type.name
            )
        )

    def on_plan_ended(
        self,
        mid=None,
        plan=None,
        thread_id=None,
        thread_type=None,
        at=None,
        metadata=None,
        msg=None,
    ):
        """Called when the client is listening, and a plan ends.

        Args:
            mid: The action ID
            plan (Plan): Ended plan
            thread_id: Thread ID that the action was sent to. See :ref:`intro_threads`
            thread_type (ThreadType): Type of thread that the action was sent to. See :ref:`intro_threads`
            at (datetime.datetime): When the action was executed
            metadata: Extra metadata about the action
            msg: A full set of the data received
        """
        log.info(
            "Plan {} has ended in {} ({})".format(plan, thread_id, thread_type.name)
        )

    def on_plan_edited(
        self,
        mid=None,
        plan=None,
        author_id=None,
        thread_id=None,
        thread_type=None,
        at=None,
        metadata=None,
        msg=None,
    ):
        """Called when the client is listening, and somebody edits a plan.

        Args:
            mid: The action ID
            plan (Plan): Edited plan
            author_id: The ID of the person who edited the plan
            thread_id: Thread ID that the action was sent to. See :ref:`intro_threads`
            thread_type (ThreadType): Type of thread that the action was sent to. See :ref:`intro_threads`
            at (datetime.datetime): When the action was executed
            metadata: Extra metadata about the action
            msg: A full set of the data received
        """
        log.info(
            "{} edited plan {} in {} ({})".format(
                author_id, plan, thread_id, thread_type.name
            )
        )

    def on_plan_deleted(
        self,
        mid=None,
        plan=None,
        author_id=None,
        thread_id=None,
        thread_type=None,
        at=None,
        metadata=None,
        msg=None,
    ):
        """Called when the client is listening, and somebody deletes a plan.

        Args:
            mid: The action ID
            plan (Plan): Deleted plan
            author_id: The ID of the person who deleted the plan
            thread_id: Thread ID that the action was sent to. See :ref:`intro_threads`
            thread_type (ThreadType): Type of thread that the action was sent to. See :ref:`intro_threads`
            at (datetime.datetime): When the action was executed
            metadata: Extra metadata about the action
            msg: A full set of the data received
        """
        log.info(
            "{} deleted plan {} in {} ({})".format(
                author_id, plan, thread_id, thread_type.name
            )
        )

    def on_plan_participation(
        self,
        mid=None,
        plan=None,
        take_part=None,
        author_id=None,
        thread_id=None,
        thread_type=None,
        at=None,
        metadata=None,
        msg=None,
    ):
        """Called when the client is listening, and somebody takes part in a plan or not.

        Args:
            mid: The action ID
            plan (Plan): Plan
            take_part (bool): Whether the person takes part in the plan or not
            author_id: The ID of the person who will participate in the plan or not
            thread_id: Thread ID that the action was sent to. See :ref:`intro_threads`
            thread_type (ThreadType): Type of thread that the action was sent to. See :ref:`intro_threads`
            at (datetime.datetime): When the action was executed
            metadata: Extra metadata about the action
            msg: A full set of the data received
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

    def on_qprimer(self, at=None, msg=None):
        """Called when the client just started listening.

        Args:
            at (datetime.datetime): When the action was executed
            msg: A full set of the data received
        """
        pass

    def on_chat_timestamp(self, buddylist=None, msg=None):
        """Called when the client receives chat online presence update.

        Args:
            buddylist: A list of dictionaries with friend id and last seen timestamp
            msg: A full set of the data received
        """
        log.debug("Chat Timestamps received: {}".format(buddylist))

    def on_buddylist_overlay(self, statuses=None, msg=None):
        """Called when the client is listening and client receives information about friend active status.

        Args:
            statuses (dict): Dictionary with user IDs as keys and :class:`ActiveStatus` as values
            msg: A full set of the data received
        """
        log.debug("Buddylist overlay received: {}".format(statuses))

    def on_unknown_messsage_type(self, msg=None):
        """Called when the client is listening, and some unknown data was received.

        Args:
            msg: A full set of the data received
        """
        log.debug("Unknown message received: {}".format(msg))

    def on_message_error(self, exception=None, msg=None):
        """Called when an error was encountered while parsing received data.

        Args:
            exception: The exception that was encountered
            msg: A full set of the data received
        """
        log.exception("Exception in parsing of {}".format(msg))

    """
    END EVENTS
    """
