import datetime
import time
import json
import requests

from ._core import log
from . import _util, _graphql, _session

from ._exception import FBchatException, FBchatFacebookError
from ._thread import ThreadLocation, ThreadColor
from ._user import TypingStatus, User, UserData, ActiveStatus
from ._group import Group, GroupData
from ._page import Page, PageData
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
from ._plan import PlanData


class Client:
    """A client for the Facebook Chat (Messenger).

    This contains all the methods you use to interact with Facebook. You can extend this
    class, and overwrite the ``on`` methods, to provide custom event handling (mainly
    useful while listening).
    """

    def __init__(self, session):
        """Initialize the client model.

        Args:
            session: The session to use when making requests.
        """
        self._sticky, self._pool = (None, None)
        self._seq = "0"
        self._pull_channel = 0
        self._mark_alive = True
        self._buddylist = dict()
        self._session = session

    @property
    def session(self):
        """The session that's used when making requests."""
        return self._session

    def __repr__(self):
        return "Client(session={!r})".format(self._session)

    """
    INTERNAL REQUEST METHODS
    """

    def _get(self, url, params):
        return self._session._get(url, params)

    def _post(self, url, params, files=None):
        return self._session._post(url, params, files=files)

    def _payload_post(self, url, data, files=None):
        return self._session._payload_post(url, data, files=files)

    def graphql_requests(self, *queries):
        """Execute GraphQL queries.

        Args:
            queries (dict): Zero or more dictionaries

        Returns:
            tuple: A tuple containing JSON GraphQL queries

        Raises:
            FBchatException: If request failed
        """
        return tuple(self._session._graphql_requests(*queries))

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
    FETCH METHODS
    """

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
            list: `Thread` objects

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
            list: `User` objects

        Raises:
            FBchatException: If request failed
        """
        users = []
        users_to_fetch = []  # It's more efficient to fetch all users in one request
        for thread in threads:
            if isinstance(thread, User):
                if thread.id not in [user.id for user in users]:
                    users.append(thread)
            elif isinstance(thread, Group):
                for user_id in thread.participants:
                    if (
                        user_id not in [user.id for user in users]
                        and user_id not in users_to_fetch
                    ):
                        users_to_fetch.append(user_id)
        for user_id, user in self.fetch_user_info(*users_to_fetch).items():
            users.append(user)
        return users

    def fetch_all_users(self):
        """Fetch all users the client is currently chatting with.

        Returns:
            list: `User` objects

        Raises:
            FBchatException: If request failed
        """
        data = {"viewer": self._session.user_id}
        j = self._payload_post("/chat/user_info_all", data)

        users = []
        for data in j.values():
            if data["type"] in ["user", "friend"]:
                if data["id"] in ["0", 0]:
                    # Skip invalid users
                    continue
                users.append(UserData._from_all_fetch(self.session, data))
        return users

    def search_for_users(self, name, limit=10):
        """Find and get users by their name.

        Args:
            name: Name of the user
            limit: The max. amount of users to fetch

        Returns:
            list: `User` objects, ordered by relevance

        Raises:
            FBchatException: If request failed
        """
        params = {"search": name, "limit": limit}
        (j,) = self.graphql_requests(_graphql.from_query(_graphql.SEARCH_USER, params))

        return [
            UserData._from_graphql(self.session, node)
            for node in j[name]["users"]["nodes"]
        ]

    def search_for_pages(self, name, limit=10):
        """Find and get pages by their name.

        Args:
            name: Name of the page

        Returns:
            list: `Page` objects, ordered by relevance

        Raises:
            FBchatException: If request failed
        """
        params = {"search": name, "limit": limit}
        (j,) = self.graphql_requests(_graphql.from_query(_graphql.SEARCH_PAGE, params))

        return [
            PageData._from_graphql(self.session, node)
            for node in j[name]["pages"]["nodes"]
        ]

    def search_for_groups(self, name, limit=10):
        """Find and get group threads by their name.

        Args:
            name: Name of the group thread
            limit: The max. amount of groups to fetch

        Returns:
            list: `Group` objects, ordered by relevance

        Raises:
            FBchatException: If request failed
        """
        params = {"search": name, "limit": limit}
        (j,) = self.graphql_requests(_graphql.from_query(_graphql.SEARCH_GROUP, params))

        return [
            GroupData._from_graphql(self.session, node)
            for node in j["viewer"]["groups"]["nodes"]
        ]

    def search_for_threads(self, name, limit=10):
        """Find and get threads by their name.

        Args:
            name: Name of the thread
            limit: The max. amount of groups to fetch

        Returns:
            list: `User`, `Group` and `Page` objects, ordered by relevance

        Raises:
            FBchatException: If request failed
        """
        params = {"search": name, "limit": limit}
        (j,) = self.graphql_requests(
            _graphql.from_query(_graphql.SEARCH_THREAD, params)
        )

        rtn = []
        for node in j[name]["threads"]["nodes"]:
            if node["__typename"] == "User":
                rtn.append(UserData._from_graphql(self.session, node))
            elif node["__typename"] == "MessageThread":
                # MessageThread => Group thread
                rtn.append(GroupData._from_graphql(self.session, node))
            elif node["__typename"] == "Page":
                rtn.append(PageData._from_graphql(self.session, node))
            elif node["__typename"] == "Group":
                # We don't handle Facebook "Groups"
                pass
            else:
                log.warning(
                    "Unknown type {} in {}".format(repr(node["__typename"]), node)
                )

        return rtn

    def search(self, query, fetch_messages=False, thread_limit=5, message_limit=5):
        """Search for messages in all threads.

        Args:
            query: Text to search for
            fetch_messages: Whether to fetch `Message` objects or IDs only
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
            dict: `User` objects, labeled by their ID

        Raises:
            FBchatException: If request failed
        """
        threads = self.fetch_thread_info(*user_ids)
        users = {}
        for id_, thread in threads.items():
            if isinstance(thread, User):
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
            dict: `Page` objects, labeled by their ID

        Raises:
            FBchatException: If request failed
        """
        threads = self.fetch_thread_info(*page_ids)
        pages = {}
        for id_, thread in threads.items():
            if isinstance(thread, Page):
                pages[id_] = thread
            else:
                raise ValueError("Thread {} was not a page".format(thread))

        return pages

    def fetch_group_info(self, *group_ids):
        """Fetch groups' info from IDs, unordered.

        Args:
            group_ids: One or more group ID(s) to query

        Returns:
            dict: `Group` objects, labeled by their ID

        Raises:
            FBchatException: If request failed
        """
        threads = self.fetch_thread_info(*group_ids)
        groups = {}
        for id_, thread in threads.items():
            if isinstance(thread, Group):
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
            dict: `Thread` objects, labeled by their ID

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
                rtn[_id] = GroupData._from_graphql(self.session, entry)
            elif entry.get("thread_type") == "ONE_TO_ONE":
                _id = entry["thread_key"]["other_user_id"]
                if pages_and_users.get(_id) is None:
                    raise FBchatException("Could not fetch thread {}".format(_id))
                entry.update(pages_and_users[_id])
                if "first_name" in entry:
                    rtn[_id] = UserData._from_graphql(self.session, entry)
                else:
                    rtn[_id] = PageData._from_graphql(self.session, entry)
            else:
                raise FBchatException(
                    "{} had an unknown thread type: {}".format(thread_ids[i], entry)
                )

        return rtn

    def fetch_thread_list(
        self, limit=20, thread_location=ThreadLocation.INBOX, before=None
    ):
        """Fetch the client's thread list.

        Args:
            limit (int): Max. number of threads to retrieve. Capped at 20
            thread_location (ThreadLocation): INBOX, PENDING, ARCHIVED or OTHER
            before (datetime.datetime): The point from which to retrieve threads

        Returns:
            list: `Thread` objects

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
        (j,) = self.graphql_requests(_graphql.from_doc_id("1349387578499440", params))

        rtn = []
        for node in j["viewer"]["message_threads"]["nodes"]:
            _type = node.get("thread_type")
            if _type == "GROUP":
                rtn.append(GroupData._from_graphql(self.session, node))
            elif _type == "ONE_TO_ONE":
                user = UserData._from_thread_fetch(self.session, node)
                if user:
                    rtn.append(user)
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

    def _get_private_data(self):
        (j,) = self.graphql_requests(_graphql.from_doc_id("1868889766468115", {}))
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

    """
    END FETCH METHODS
    """

    """
    SEND METHODS
    """

    def update_poll_vote(self, poll_id, option_ids=[], new_options=[]):
        """Update a poll vote.

        Args:
            poll_id: ID of the poll to update vote
            option_ids: List of the option IDs to vote
            new_options: List of the new option names

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

    def _read_status(self, read, thread_ids, timestamp=None):
        thread_ids = _util.require_list(thread_ids)

        data = {
            "watermarkTimestamp": _util.datetime_to_millis(timestamp)
            if timestamp
            else _util.now(),
            "shouldSendReadReceipt": "true",
        }

        for thread_id in thread_ids:
            data["ids[{}]".format(thread_id)] = "true" if read else "false"

        j = self._payload_post("/ajax/mercury/change_read_status.php", data)

    def mark_as_read(self, thread_ids=None, timestamp=None):
        """Mark threads as read.

        All messages inside the specified threads will be marked as read.

        Args:
            thread_ids: User/Group IDs to set as read. See :ref:`intro_threads`
            timestamp: Timestamp (as a Datetime) to signal the read cursor at, default is the current time

        Raises:
            FBchatException: If request failed
        """
        self._read_status(True, thread_ids, timestamp)

    def mark_as_unread(self, thread_ids=None, timestamp=None):
        """Mark threads as unread.

        All messages inside the specified threads will be marked as unread.

        Args:
            thread_ids: User/Group IDs to set as unread. See :ref:`intro_threads`
            timestamp: Timestamp (as a Datetime) to signal the read cursor at, default is the current time

        Raises:
            FBchatException: If request failed
        """
        self._read_status(False, thread_ids, timestamp)

    def mark_as_seen(self):
        """
        Todo:
            Documenting this
        """
        j = self._payload_post(
            "/ajax/mercury/mark_seen.php", {"seen_timestamp": _util.now()}
        )

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

    """
    LISTEN METHODS
    """

    def _ping(self):
        data = {
            "seq": self._seq,
            "channel": "p_" + self._session.user_id,
            "clientid": self._session._client_id,
            "partition": -2,
            "cap": 0,
            "uid": self._session.user_id,
            "sticky_token": self._sticky,
            "sticky_pool": self._pool,
            "viewer_uid": self._session.user_id,
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
            "clientid": self._session._client_id,
            "state": "active" if self._mark_alive else "offline",
        }
        j = self._get(
            "https://{}-edge-chat.facebook.com/pull".format(self._pull_channel), data
        )
        _util.handle_payload_error(j)
        return j

    def _parse_delta(self, m):
        def get_thread(data):
            if "threadFbId" in data["threadKey"]:
                group_id = str(data["threadKey"]["threadFbId"])
                return Group(session=self.session, id=group_id)
            elif "otherUserFbId" in data["threadKey"]:
                user_id = str(data["threadKey"]["otherUserFbId"])
                return User(session=self.session, id=user_id)
            return None

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
            self.on_people_added(
                mid=mid,
                added_ids=added_ids,
                author_id=author_id,
                group=get_thread(metadata),
                at=at,
                msg=m,
            )

        # Left/removed participants
        elif "leftParticipantFbId" in delta:
            removed_id = str(delta["leftParticipantFbId"])
            self.on_person_removed(
                mid=mid,
                removed_id=removed_id,
                author_id=author_id,
                group=get_thread(metadata),
                at=at,
                msg=m,
            )

        # Color change
        elif delta_type == "change_thread_theme":
            new_color = ThreadColor._from_graphql(delta["untypedData"]["theme_color"])
            thread = get_thread(metadata)
            self.on_color_change(
                mid=mid,
                author_id=author_id,
                new_color=new_color,
                thread=get_thread(metadata),
                at=at,
                metadata=metadata,
                msg=m,
            )

        # Emoji change
        elif delta_type == "change_thread_icon":
            new_emoji = delta["untypedData"]["thread_icon"]
            self.on_emoji_change(
                mid=mid,
                author_id=author_id,
                new_emoji=new_emoji,
                thread=get_thread(metadata),
                at=at,
                metadata=metadata,
                msg=m,
            )

        # Thread title change
        elif delta_class == "ThreadName":
            new_title = delta["name"]
            self.on_title_change(
                mid=mid,
                author_id=author_id,
                new_title=new_title,
                thread=get_thread(metadata),
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
                group = get_thread(metadata)
                fetch_info = group._forced_fetch(mid)
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
                        group=group,
                        at=at,
                        msg=m,
                    )

        # Nickname change
        elif delta_type == "change_thread_nickname":
            changed_for = str(delta["untypedData"]["participant_id"])
            new_nickname = delta["untypedData"]["nickname"]
            self.on_nickname_change(
                mid=mid,
                author_id=author_id,
                changed_for=changed_for,
                new_nickname=new_nickname,
                thread=get_thread(metadata),
                at=at,
                metadata=metadata,
                msg=m,
            )

        # Admin added or removed in a group thread
        elif delta_type == "change_thread_admins":
            target_id = delta["untypedData"]["TARGET_ID"]
            admin_event = delta["untypedData"]["ADMIN_EVENT"]
            if admin_event == "add_admin":
                self.on_admin_added(
                    mid=mid,
                    added_id=target_id,
                    author_id=author_id,
                    thread=get_thread(metadata),
                    at=at,
                    msg=m,
                )
            elif admin_event == "remove_admin":
                self.on_admin_removed(
                    mid=mid,
                    removed_id=target_id,
                    author_id=author_id,
                    thread=get_thread(metadata),
                    at=at,
                    msg=m,
                )

        # Group approval mode change
        elif delta_type == "change_thread_approval_mode":
            approval_mode = bool(int(delta["untypedData"]["APPROVAL_MODE"]))
            self.on_approval_mode_change(
                mid=mid,
                approval_mode=approval_mode,
                author_id=author_id,
                thread=get_thread(metadata),
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
            self.on_message_delivered(
                msg_ids=message_ids,
                delivered_for=delivered_for,
                thread=get_thread(metadata),
                at=at,
                metadata=metadata,
                msg=m,
            )

        # Message seen
        elif delta_class == "ReadReceipt":
            seen_by = str(delta.get("actorFbId") or delta["threadKey"]["otherUserFbId"])
            seen_at = _util.millis_to_datetime(int(delta["actionTimestampMs"]))
            at = _util.millis_to_datetime(int(delta["watermarkTimestampMs"]))
            self.on_message_seen(
                seen_by=seen_by,
                thread=get_thread(metadata),
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
                    get_thread({"threadKey": thr}) for thr in delta.get("threadKeys")
                ]

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
            self.on_game_played(
                mid=mid,
                author_id=author_id,
                game_id=game_id,
                game_name=game_name,
                score=score,
                leaderboard=leaderboard,
                thread=get_thread(metadata),
                at=at,
                metadata=metadata,
                msg=m,
            )

        # Group call started/ended
        elif delta_type == "rtc_call_log":
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
                    thread=get_thread(metadata),
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
                    thread=get_thread(metadata),
                    at=at,
                    metadata=metadata,
                    msg=m,
                )

        # User joined to group call
        elif delta_type == "participant_joined_group_call":
            is_video_call = bool(int(delta["untypedData"]["group_call_type"]))
            self.on_user_joined_call(
                mid=mid,
                joined_id=author_id,
                is_video_call=is_video_call,
                thread=get_thread(metadata),
                at=at,
                metadata=metadata,
                msg=m,
            )

        # Group poll event
        elif delta_type == "group_poll":
            event_type = delta["untypedData"]["event_type"]
            poll_json = json.loads(delta["untypedData"]["question_json"])
            poll = Poll._from_graphql(poll_json)
            if event_type == "question_creation":
                # User created group poll
                self.on_poll_created(
                    mid=mid,
                    poll=poll,
                    author_id=author_id,
                    thread=get_thread(metadata),
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
                    thread=get_thread(metadata),
                    at=at,
                    metadata=metadata,
                    msg=m,
                )

        # Plan created
        elif delta_type == "lightweight_event_create":
            self.on_plan_created(
                mid=mid,
                plan=PlanData._from_pull(self.session, delta["untypedData"]),
                author_id=author_id,
                thread=get_thread(metadata),
                at=at,
                metadata=metadata,
                msg=m,
            )

        # Plan ended
        elif delta_type == "lightweight_event_notify":
            self.on_plan_ended(
                mid=mid,
                plan=PlanData._from_pull(self.session, delta["untypedData"]),
                thread=get_thread(metadata),
                at=at,
                metadata=metadata,
                msg=m,
            )

        # Plan edited
        elif delta_type == "lightweight_event_update":
            self.on_plan_edited(
                mid=mid,
                plan=PlanData._from_pull(self.session, delta["untypedData"]),
                author_id=author_id,
                thread=get_thread(metadata),
                at=at,
                metadata=metadata,
                msg=m,
            )

        # Plan deleted
        elif delta_type == "lightweight_event_delete":
            self.on_plan_deleted(
                mid=mid,
                plan=PlanData._from_pull(self.session, delta["untypedData"]),
                author_id=author_id,
                thread=get_thread(metadata),
                at=at,
                metadata=metadata,
                msg=m,
            )

        # Plan participation change
        elif delta_type == "lightweight_event_rsvp":
            take_part = delta["untypedData"]["guest_status"] == "GOING"
            self.on_plan_participation(
                mid=mid,
                plan=PlanData._from_pull(self.session, delta["untypedData"]),
                take_part=take_part,
                author_id=author_id,
                thread=get_thread(metadata),
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
                            thread=get_thread(metadata),
                            at=at,
                            msg=m,
                        )
                    else:
                        self.on_reaction_removed(
                            mid=mid,
                            author_id=author_id,
                            thread=get_thread(metadata),
                            at=at,
                            msg=m,
                        )

                # Viewer status change
                elif d.get("deltaChangeViewerStatus"):
                    i = d["deltaChangeViewerStatus"]
                    author_id = str(i["actorFbid"])
                    reason = i["reason"]
                    can_reply = i["canViewerReply"]
                    if reason == 2:
                        if can_reply:
                            self.on_unblock(
                                author_id=author_id,
                                thread=get_thread(metadata),
                                at=at,
                                msg=m,
                            )
                        else:
                            self.on_block(
                                author_id=author_id,
                                thread=get_thread(metadata),
                                at=at,
                                msg=m,
                            )

                # Live location info
                elif d.get("liveLocationData"):
                    i = d["liveLocationData"]
                    for l in i["messageLiveLocations"]:
                        mid = l["messageId"]
                        author_id = str(l["senderId"])
                        location = LiveLocationAttachment._from_pull(l)
                        self.on_live_location(
                            mid=mid,
                            location=location,
                            author_id=author_id,
                            thread=get_thread(metadata),
                            at=at,
                            msg=m,
                        )

                # Message deletion
                elif d.get("deltaRecallMessageData"):
                    i = d["deltaRecallMessageData"]
                    mid = i["messageID"]
                    at = _util.millis_to_datetime(i["deletionTimestamp"])
                    author_id = str(i["senderID"])
                    self.on_message_unsent(
                        mid=mid,
                        author_id=author_id,
                        thread=get_thread(metadata),
                        at=at,
                        msg=m,
                    )

                elif d.get("deltaMessageReply"):
                    i = d["deltaMessageReply"]
                    metadata = i["message"]["messageMetadata"]
                    replied_to = Message._from_reply(
                        self.session, i["repliedToMessage"]
                    )
                    message = Message._from_reply(
                        self.session, i["message"], replied_to
                    )
                    self.on_message(
                        mid=message.id,
                        author_id=message.author,
                        message_object=message,
                        thread=get_thread(metadata),
                        at=message.created_at,
                        metadata=metadata,
                        msg=m,
                    )

        # New message
        elif delta.get("class") == "NewMessage":
            self.on_message(
                mid=mid,
                author_id=author_id,
                message_object=Message._from_pull(
                    self.session,
                    delta,
                    mid=mid,
                    tags=metadata.get("tags"),
                    author=author_id,
                    created_at=at,
                ),
                thread=get_thread(metadata),
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
                        thread = Group(session=self.session, id=str(thread_id))
                    else:
                        if author_id == self.session.user_id:
                            thread_id = m.get("to")
                        else:
                            thread_id = author_id
                        thread = User(session=self.session, id=thread_id)
                    typing_status = TypingStatus(m.get("st"))
                    self.on_typing(
                        author_id=author_id, status=typing_status, thread=thread, msg=m,
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
        thread=None,
        at=None,
        metadata=None,
        msg=None,
    ):
        """Called when the client is listening, and somebody sends a message.

        Args:
            mid: The message ID
            author_id: The ID of the author
            message_object (Message): The message (As a `Message` object)
            thread: Thread that the message was sent to. See :ref:`intro_threads`
            at (datetime.datetime): When the message was sent
            metadata: Extra metadata about the message
            msg: A full set of the data received
        """
        log.info("{} from {} in {}".format(message_object, author_id, thread))

    def on_color_change(
        self,
        mid=None,
        author_id=None,
        new_color=None,
        thread=None,
        at=None,
        metadata=None,
        msg=None,
    ):
        """Called when the client is listening, and somebody changes a thread's color.

        Args:
            mid: The action ID
            author_id: The ID of the person who changed the color
            new_color (ThreadColor): The new color
            thread: Thread that the action was sent to. See :ref:`intro_threads`
            at (datetime.datetime): When the action was executed
            metadata: Extra metadata about the action
            msg: A full set of the data received
        """
        log.info("Color change from {} in {}: {}".format(author_id, thread, new_color))

    def on_emoji_change(
        self,
        mid=None,
        author_id=None,
        new_emoji=None,
        thread=None,
        at=None,
        metadata=None,
        msg=None,
    ):
        """Called when the client is listening, and somebody changes a thread's emoji.

        Args:
            mid: The action ID
            author_id: The ID of the person who changed the emoji
            new_emoji: The new emoji
            thread: Thread that the action was sent to. See :ref:`intro_threads`
            at (datetime.datetime): When the action was executed
            metadata: Extra metadata about the action
            msg: A full set of the data received
        """
        log.info("Emoji change from {} in {}: {}".format(author_id, thread, new_emoji))

    def on_title_change(
        self,
        mid=None,
        author_id=None,
        new_title=None,
        group=None,
        at=None,
        metadata=None,
        msg=None,
    ):
        """Called when the client is listening, and somebody changes a thread's title.

        Args:
            mid: The action ID
            author_id: The ID of the person who changed the title
            new_title: The new title
            group: Group that the action was sent to. See :ref:`intro_threads`
            at (datetime.datetime): When the action was executed
            metadata: Extra metadata about the action
            msg: A full set of the data received
        """
        log.info("Title change from {} in {}: {}".format(author_id, group, new_title))

    def on_image_change(
        self, mid=None, author_id=None, new_image=None, group=None, at=None, msg=None,
    ):
        """Called when the client is listening, and somebody changes a thread's image.

        Args:
            mid: The action ID
            author_id: The ID of the person who changed the image
            new_image: The ID of the new image
            group: Group that the action was sent to. See :ref:`intro_threads`
            at (datetime.datetime): When the action was executed
            msg: A full set of the data received
        """
        log.info("{} changed group image in {}".format(author_id, group))

    def on_nickname_change(
        self,
        mid=None,
        author_id=None,
        changed_for=None,
        new_nickname=None,
        thread=None,
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
            thread: Thread that the action was sent to. See :ref:`intro_threads`
            at (datetime.datetime): When the action was executed
            metadata: Extra metadata about the action
            msg: A full set of the data received
        """
        log.info(
            "Nickname change from {} in {} for {}: {}".format(
                author_id, thread, changed_for, new_nickname
            )
        )

    def on_admin_added(
        self, mid=None, added_id=None, author_id=None, group=None, at=None, msg=None,
    ):
        """Called when the client is listening, and somebody adds an admin to a group.

        Args:
            mid: The action ID
            added_id: The ID of the admin who got added
            author_id: The ID of the person who added the admins
            group: Group that the action was sent to. See :ref:`intro_threads`
            at (datetime.datetime): When the action was executed
            msg: A full set of the data received
        """
        log.info("{} added admin: {} in {}".format(author_id, added_id, group))

    def on_admin_removed(
        self, mid=None, removed_id=None, author_id=None, group=None, at=None, msg=None,
    ):
        """Called when the client is listening, and somebody is removed as an admin in a group.

        Args:
            mid: The action ID
            removed_id: The ID of the admin who got removed
            author_id: The ID of the person who removed the admins
            group: Group that the action was sent to. See :ref:`intro_threads`
            at (datetime.datetime): When the action was executed
            msg: A full set of the data received
        """
        log.info("{} removed admin: {} in {}".format(author_id, removed_id, group))

    def on_approval_mode_change(
        self,
        mid=None,
        approval_mode=None,
        author_id=None,
        group=None,
        at=None,
        msg=None,
    ):
        """Called when the client is listening, and somebody changes approval mode in a group.

        Args:
            mid: The action ID
            approval_mode: True if approval mode is activated
            author_id: The ID of the person who changed approval mode
            group: Group that the action was sent to. See :ref:`intro_threads`
            at (datetime.datetime): When the action was executed
            msg: A full set of the data received
        """
        if approval_mode:
            log.info("{} activated approval mode in {}".format(author_id, group))
        else:
            log.info("{} disabled approval mode in {}".format(author_id, group))

    def on_message_seen(
        self, seen_by=None, thread=None, seen_at=None, at=None, metadata=None, msg=None,
    ):
        """Called when the client is listening, and somebody marks a message as seen.

        Args:
            seen_by: The ID of the person who marked the message as seen
            thread: Thread that the action was sent to. See :ref:`intro_threads`
            seen_at (datetime.datetime): When the person saw the message
            at (datetime.datetime): When the action was executed
            metadata: Extra metadata about the action
            msg: A full set of the data received
        """
        log.info("Messages seen by {} in {} at {}".format(seen_by, thread, seen_at))

    def on_message_delivered(
        self,
        msg_ids=None,
        delivered_for=None,
        thread=None,
        at=None,
        metadata=None,
        msg=None,
    ):
        """Called when the client is listening, and somebody marks messages as delivered.

        Args:
            msg_ids: The messages that are marked as delivered
            delivered_for: The person that marked the messages as delivered
            thread: Thread that the action was sent to. See :ref:`intro_threads`
            at (datetime.datetime): When the action was executed
            metadata: Extra metadata about the action
            msg: A full set of the data received
        """
        log.info(
            "Messages {} delivered to {} in {} at {}".format(
                msg_ids, delivered_for, thread, at
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
        log.info("Marked messages as seen in threads {} at {}".format(threads, seen_at))

    def on_message_unsent(
        self, mid=None, author_id=None, thread=None, at=None, msg=None,
    ):
        """Called when the client is listening, and someone unsends (deletes for everyone) a message.

        Args:
            mid: ID of the unsent message
            author_id: The ID of the person who unsent the message
            thread: Thread that the action was sent to. See :ref:`intro_threads`
            at (datetime.datetime): When the action was executed
            msg: A full set of the data received
        """
        log.info(
            "{} unsent the message {} in {} at {}".format(
                author_id, repr(mid), thread, at
            )
        )

    def on_people_added(
        self, mid=None, added_ids=None, author_id=None, group=None, at=None, msg=None,
    ):
        """Called when the client is listening, and somebody adds people to a group thread.

        Args:
            mid: The action ID
            added_ids: The IDs of the people who got added
            author_id: The ID of the person who added the people
            group: Group that the action was sent to. See :ref:`intro_threads`
            at (datetime.datetime): When the action was executed
            msg: A full set of the data received
        """
        log.info("{} added: {} in {}".format(author_id, ", ".join(added_ids), group))

    def on_person_removed(
        self, mid=None, removed_id=None, author_id=None, group=None, at=None, msg=None,
    ):
        """Called when the client is listening, and somebody removes a person from a group thread.

        Args:
            mid: The action ID
            removed_id: The ID of the person who got removed
            author_id: The ID of the person who removed the person
            group: Group that the action was sent to. See :ref:`intro_threads`
            at (datetime.datetime): When the action was executed
            msg: A full set of the data received
        """
        log.info("{} removed: {} in {}".format(author_id, removed_id, group))

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

    def on_typing(self, author_id=None, status=None, thread=None, msg=None):
        """Called when the client is listening, and somebody starts or stops typing into a chat.

        Args:
            author_id: The ID of the person who sent the action
            status (TypingStatus): The typing status
            thread: Thread that the action was sent to. See :ref:`intro_threads`
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
        thread=None,
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
            thread: Thread that the action was sent to. See :ref:`intro_threads`
            at (datetime.datetime): When the action was executed
            metadata: Extra metadata about the action
            msg: A full set of the data received
        """
        log.info('{} played "{}" in {}'.format(author_id, game_name, thread))

    def on_reaction_added(
        self, mid=None, reaction=None, author_id=None, thread=None, at=None, msg=None,
    ):
        """Called when the client is listening, and somebody reacts to a message.

        Args:
            mid: Message ID, that user reacted to
            reaction (MessageReaction): Reaction
            add_reaction: Whether user added or removed reaction
            author_id: The ID of the person who reacted to the message
            thread: Thread that the action was sent to. See :ref:`intro_threads`
            at (datetime.datetime): When the action was executed
            msg: A full set of the data received
        """
        log.info(
            "{} reacted to message {} with {} in {}".format(
                author_id, mid, reaction.name, thread
            )
        )

    def on_reaction_removed(
        self, mid=None, author_id=None, thread=None, at=None, msg=None,
    ):
        """Called when the client is listening, and somebody removes reaction from a message.

        Args:
            mid: Message ID, that user reacted to
            author_id: The ID of the person who removed reaction
            thread: Thread that the action was sent to. See :ref:`intro_threads`
            at (datetime.datetime): When the action was executed
            msg: A full set of the data received
        """
        log.info(
            "{} removed reaction from {} message in {}".format(author_id, mid, thread)
        )

    def on_block(self, author_id=None, thread=None, at=None, msg=None):
        """Called when the client is listening, and somebody blocks client.

        Args:
            author_id: The ID of the person who blocked
            thread: Thread that the action was sent to. See :ref:`intro_threads`
            at (datetime.datetime): When the action was executed
            msg: A full set of the data received
        """
        log.info("{} blocked {}".format(author_id, thread))

    def on_unblock(self, author_id=None, thread=None, at=None, msg=None):
        """Called when the client is listening, and somebody blocks client.

        Args:
            author_id: The ID of the person who unblocked
            thread: Thread that the action was sent to. See :ref:`intro_threads`
            at (datetime.datetime): When the action was executed
            msg: A full set of the data received
        """
        log.info("{} unblocked {}".format(author_id, thread))

    def on_live_location(
        self, mid=None, location=None, author_id=None, thread=None, at=None, msg=None,
    ):
        """Called when the client is listening and somebody sends live location info.

        Args:
            mid: The action ID
            location (LiveLocationAttachment): Sent location info
            author_id: The ID of the person who sent location info
            thread: Thread that the action was sent to. See :ref:`intro_threads`
            at (datetime.datetime): When the action was executed
            msg: A full set of the data received
        """
        log.info(
            "{} sent live location info in {} with latitude {} and longitude {}".format(
                author_id, thread, location.latitude, location.longitude
            )
        )

    def on_call_started(
        self,
        mid=None,
        caller_id=None,
        is_video_call=None,
        thread=None,
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
            thread: Thread that the action was sent to. See :ref:`intro_threads`
            at (datetime.datetime): When the action was executed
            metadata: Extra metadata about the action
            msg: A full set of the data received
        """
        log.info("{} started call in {}".format(caller_id, thread))

    def on_call_ended(
        self,
        mid=None,
        caller_id=None,
        is_video_call=None,
        call_duration=None,
        thread=None,
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
            thread: Thread that the action was sent to. See :ref:`intro_threads`
            at (datetime.datetime): When the action was executed
            metadata: Extra metadata about the action
            msg: A full set of the data received
        """
        log.info("{} ended call in {}".format(caller_id, thread))

    def on_user_joined_call(
        self,
        mid=None,
        joined_id=None,
        is_video_call=None,
        thread=None,
        at=None,
        metadata=None,
        msg=None,
    ):
        """Called when the client is listening, and somebody joins a group call.

        Args:
            mid: The action ID
            joined_id: The ID of the person who joined the call
            is_video_call: True if it's video call
            thread: Thread that the action was sent to. See :ref:`intro_threads`
            at (datetime.datetime): When the action was executed
            metadata: Extra metadata about the action
            msg: A full set of the data received
        """
        log.info("{} joined call in {}".format(joined_id, thread))

    def on_poll_created(
        self,
        mid=None,
        poll=None,
        author_id=None,
        thread=None,
        at=None,
        metadata=None,
        msg=None,
    ):
        """Called when the client is listening, and somebody creates a group poll.

        Args:
            mid: The action ID
            poll (Poll): Created poll
            author_id: The ID of the person who created the poll
            thread: Thread that the action was sent to. See :ref:`intro_threads`
            at (datetime.datetime): When the action was executed
            metadata: Extra metadata about the action
            msg: A full set of the data received
        """
        log.info("{} created poll {} in {}".format(author_id, poll, thread))

    def on_poll_voted(
        self,
        mid=None,
        poll=None,
        added_options=None,
        removed_options=None,
        author_id=None,
        thread=None,
        at=None,
        metadata=None,
        msg=None,
    ):
        """Called when the client is listening, and somebody votes in a group poll.

        Args:
            mid: The action ID
            poll (Poll): Poll, that user voted in
            author_id: The ID of the person who voted in the poll
            thread: Thread that the action was sent to. See :ref:`intro_threads`
            at (datetime.datetime): When the action was executed
            metadata: Extra metadata about the action
            msg: A full set of the data received
        """
        log.info("{} voted in poll {} in {}".format(author_id, poll, thread))

    def on_plan_created(
        self,
        mid=None,
        plan=None,
        author_id=None,
        thread=None,
        at=None,
        metadata=None,
        msg=None,
    ):
        """Called when the client is listening, and somebody creates a plan.

        Args:
            mid: The action ID
            plan (Plan): Created plan
            author_id: The ID of the person who created the plan
            thread: Thread that the action was sent to. See :ref:`intro_threads`
            at (datetime.datetime): When the action was executed
            metadata: Extra metadata about the action
            msg: A full set of the data received
        """
        log.info("{} created plan {} in {}".format(author_id, plan, thread))

    def on_plan_ended(
        self, mid=None, plan=None, thread=None, at=None, metadata=None, msg=None,
    ):
        """Called when the client is listening, and a plan ends.

        Args:
            mid: The action ID
            plan (Plan): Ended plan
            thread: Thread that the action was sent to. See :ref:`intro_threads`
            at (datetime.datetime): When the action was executed
            metadata: Extra metadata about the action
            msg: A full set of the data received
        """
        log.info("Plan {} has ended in {}".format(plan, thread))

    def on_plan_edited(
        self,
        mid=None,
        plan=None,
        author_id=None,
        thread=None,
        at=None,
        metadata=None,
        msg=None,
    ):
        """Called when the client is listening, and somebody edits a plan.

        Args:
            mid: The action ID
            plan (Plan): Edited plan
            author_id: The ID of the person who edited the plan
            thread: Thread that the action was sent to. See :ref:`intro_threads`
            at (datetime.datetime): When the action was executed
            metadata: Extra metadata about the action
            msg: A full set of the data received
        """
        log.info("{} edited plan {} in {}".format(author_id, plan, thread))

    def on_plan_deleted(
        self,
        mid=None,
        plan=None,
        author_id=None,
        thread=None,
        at=None,
        metadata=None,
        msg=None,
    ):
        """Called when the client is listening, and somebody deletes a plan.

        Args:
            mid: The action ID
            plan (Plan): Deleted plan
            author_id: The ID of the person who deleted the plan
            thread: Thread that the action was sent to. See :ref:`intro_threads`
            at (datetime.datetime): When the action was executed
            metadata: Extra metadata about the action
            msg: A full set of the data received
        """
        log.info("{} deleted plan {} in {}".format(author_id, plan, thread))

    def on_plan_participation(
        self,
        mid=None,
        plan=None,
        take_part=None,
        author_id=None,
        thread=None,
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
            thread: Thread that the action was sent to. See :ref:`intro_threads`
            at (datetime.datetime): When the action was executed
            metadata: Extra metadata about the action
            msg: A full set of the data received
        """
        if take_part:
            log.info(
                "{} will take part in {} in {} ({})".format(author_id, plan, thread)
            )
        else:
            log.info(
                "{} won't take part in {} in {} ({})".format(author_id, plan, thread)
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
            statuses (dict): Dictionary with user IDs as keys and `ActiveStatus` as values
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
