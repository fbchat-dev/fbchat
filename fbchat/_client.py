import attr
import datetime

from ._common import log, attrs_default
from . import _exception, _util, _graphql, _session, _threads, _models

from typing import Sequence, Iterable, Tuple, Optional, Set, BinaryIO


@attrs_default
class Client:
    """A client for Facebook Messenger.

    This contains methods that are generally needed to interact with Facebook.

    Example:
        Create a new client instance.

        >>> client = fbchat.Client(session=session)
    """

    #: The session to use when making requests.
    session = attr.ib(type=_session.Session)

    def fetch_users(self) -> Sequence[_threads.UserData]:
        """Fetch users the client is currently chatting with.

        This is very close to your friend list, with the follow differences:

        It differs by including users that you're not friends with, but have chatted
        with before, and by including accounts that are "Messenger Only".

        But does not include deactivated, deleted or memorialized users (logically,
        since you can't chat with those).

        The order these are returned is arbitrary.

        Example:
            Get the name of an arbitrary user that you're currently chatting with.

            >>> users = client.fetch_users()
            >>> users[0].name
            "A user"
        """
        data = {"viewer": self.session.user.id}
        j = self.session._payload_post("/chat/user_info_all", data)

        users = []
        for data in j.values():
            if data["type"] not in ["user", "friend"] or data["id"] in ["0", 0]:
                log.warning("Invalid user data %s", data)
                continue  # Skip invalid users
            users.append(_threads.UserData._from_all_fetch(self.session, data))
        return users

    def search_for_users(self, name: str, limit: int) -> Iterable[_threads.UserData]:
        """Find and get users by their name.

        The returned users are ordered by relevance.

        Args:
            name: Name of the user
            limit: The max. amount of users to fetch

        Example:
            Get the full name of the first found user.

            >>> (user,) = client.search_for_users("user", limit=1)
            >>> user.name
            "A user"
        """
        params = {"search": name, "limit": limit}
        (j,) = self.session._graphql_requests(
            _graphql.from_query(_graphql.SEARCH_USER, params)
        )

        return (
            _threads.UserData._from_graphql(self.session, node)
            for node in j[name]["users"]["nodes"]
        )

    def search_for_pages(self, name: str, limit: int) -> Iterable[_threads.PageData]:
        """Find and get pages by their name.

        The returned pages are ordered by relevance.

        Args:
            name: Name of the page
            limit: The max. amount of pages to fetch

        Example:
            Get the full name of the first found page.

            >>> (page,) = client.search_for_pages("page", limit=1)
            >>> page.name
            "A page"
        """
        params = {"search": name, "limit": limit}
        (j,) = self.session._graphql_requests(
            _graphql.from_query(_graphql.SEARCH_PAGE, params)
        )

        return (
            _threads.PageData._from_graphql(self.session, node)
            for node in j[name]["pages"]["nodes"]
        )

    def search_for_groups(self, name: str, limit: int) -> Iterable[_threads.GroupData]:
        """Find and get group threads by their name.

        The returned groups are ordered by relevance.

        Args:
            name: Name of the group thread
            limit: The max. amount of groups to fetch

        Example:
            Get the full name of the first found group.

            >>> (group,) = client.search_for_groups("group", limit=1)
            >>> group.name
            "A group"
        """
        params = {"search": name, "limit": limit}
        (j,) = self.session._graphql_requests(
            _graphql.from_query(_graphql.SEARCH_GROUP, params)
        )

        return (
            _threads.GroupData._from_graphql(self.session, node)
            for node in j["viewer"]["groups"]["nodes"]
        )

    def search_for_threads(self, name: str, limit: int) -> Iterable[_threads.ThreadABC]:
        """Find and get threads by their name.

        The returned threads are ordered by relevance.

        Args:
            name: Name of the thread
            limit: The max. amount of threads to fetch

        Example:
            Search for a user, and get the full name of the first found result.

            >>> (user,) = client.search_for_threads("user", limit=1)
            >>> assert isinstance(user, fbchat.User)
            >>> user.name
            "A user"
        """
        params = {"search": name, "limit": limit}
        (j,) = self.session._graphql_requests(
            _graphql.from_query(_graphql.SEARCH_THREAD, params)
        )

        for node in j[name]["threads"]["nodes"]:
            if node["__typename"] == "User":
                yield _threads.UserData._from_graphql(self.session, node)
            elif node["__typename"] == "MessageThread":
                # MessageThread => Group thread
                yield _threads.GroupData._from_graphql(self.session, node)
            elif node["__typename"] == "Page":
                yield _threads.PageData._from_graphql(self.session, node)
            elif node["__typename"] == "Group":
                # We don't handle Facebook "Groups"
                pass
            else:
                log.warning(
                    "Unknown type {} in {}".format(repr(node["__typename"]), node)
                )

    def _search_messages(self, query, offset, limit):
        data = {"query": query, "offset": offset, "limit": limit}
        j = self.session._payload_post("/ajax/mercury/search_snippets.php?dpr=1", data)

        total_snippets = j["search_snippets"][query]

        rtn = []
        for node in j["graphql_payload"]["message_threads"]:
            type_ = node["thread_type"]
            if type_ == "GROUP":
                thread = _threads.Group(
                    session=self.session, id=node["thread_key"]["thread_fbid"]
                )
            elif type_ == "ONE_TO_ONE":
                thread = _threads.Thread(
                    session=self.session, id=node["thread_key"]["other_user_id"]
                )
                # if True:  # TODO: This check!
                #     thread = _threads.UserData._from_graphql(self.session, node)
                # else:
                #     thread = _threads.PageData._from_graphql(self.session, node)
            else:
                thread = None
                log.warning("Unknown thread type %s, data: %s", type_, node)

            if thread:
                rtn.append((thread, total_snippets[thread.id]["num_total_snippets"]))
            else:
                rtn.append((None, 0))

        return rtn

    def search_messages(
        self, query: str, limit: Optional[int]
    ) -> Iterable[Tuple[_threads.ThreadABC, int]]:
        """Search for messages in all threads.

        Intended to be used alongside `ThreadABC.search_messages`.

        Warning! If someone send a message to a thread that matches the query, while
        we're searching, some snippets will get returned twice, and some will be lost.

        This is fundamentally not fixable, it's just how the endpoint is implemented.

        Args:
            query: Text to search for
            limit: Max. number of items to retrieve. If ``None``, all will be retrieved

        Example:
            Search for messages, and print the amount of snippets in each thread.

            >>> for thread, count in client.search_messages("abc", limit=3):
            ...     print(f"{thread.id} matched the search {count} time(s)")
            ...
            1234 matched the search 2 time(s)
            2345 matched the search 1 time(s)
            3456 matched the search 100 time(s)

        Return:
            Iterable with tuples of threads, and the total amount of matches.
        """
        offset = 0
        # The max limit is measured empirically to ~500, safe default chosen below
        for limit in _util.get_limits(limit, max_limit=100):
            data = self._search_messages(query, offset, limit)
            for thread, total_snippets in data:
                if thread:
                    yield (thread, total_snippets)
            if len(data) < limit:
                return  # No more data to fetch
            offset += limit

    def _fetch_info(self, *ids):
        data = {"ids[{}]".format(i): _id for i, _id in enumerate(ids)}
        j = self.session._payload_post("/chat/user_info/", data)

        if j.get("profiles") is None:
            raise _exception.ParseError("No users/pages returned", data=j)

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
                raise _exception.ParseError("Unknown thread type", data=k)

        log.debug(entries)
        return entries

    def fetch_thread_info(self, ids: Iterable[str]) -> Iterable[_threads.ThreadABC]:
        """Fetch threads' info from IDs, unordered.

        Warning:
            Sends two requests if users or pages are present, to fetch all available info!

        Args:
            ids: Thread ids to query

        Example:
            Get data about the user with id "4".

            >>> (user,) = client.fetch_thread_info(["4"])
            >>> user.name
            "Mark Zuckerberg"
        """
        ids = list(ids)
        queries = []
        for thread_id in ids:
            params = {
                "id": thread_id,
                "message_limit": 0,
                "load_messages": False,
                "load_read_receipts": False,
                "before": None,
            }
            queries.append(_graphql.from_doc_id("2147762685294928", params))

        j = self.session._graphql_requests(*queries)

        for i, entry in enumerate(j):
            if entry.get("message_thread") is None:
                # If you don't have an existing thread with this person, attempt to retrieve user data anyways
                j[i]["message_thread"] = {
                    "thread_key": {"other_user_id": ids[i]},
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

        for i, entry in enumerate(j):
            entry = entry["message_thread"]
            if entry.get("thread_type") == "GROUP":
                _id = entry["thread_key"]["thread_fbid"]
                yield _threads.GroupData._from_graphql(self.session, entry)
            elif entry.get("thread_type") == "ONE_TO_ONE":
                _id = entry["thread_key"]["other_user_id"]
                if pages_and_users.get(_id) is None:
                    raise _exception.ParseError(
                        "Could not fetch thread {}".format(_id), data=pages_and_users
                    )
                entry.update(pages_and_users[_id])
                if "first_name" in entry:
                    yield _threads.UserData._from_graphql(self.session, entry)
                else:
                    yield _threads.PageData._from_graphql(self.session, entry)
            else:
                raise _exception.ParseError("Unknown thread type", data=entry)

    def _fetch_threads(self, limit, before, folders):
        params = {
            "limit": limit,
            "tags": folders,
            "before": _util.datetime_to_millis(before) if before else None,
            "includeDeliveryReceipts": True,
            "includeSeqID": False,
        }
        (j,) = self.session._graphql_requests(
            _graphql.from_doc_id("1349387578499440", params)
        )

        rtn = []
        for node in j["viewer"]["message_threads"]["nodes"]:
            _type = node.get("thread_type")
            if _type == "GROUP":
                rtn.append(_threads.GroupData._from_graphql(self.session, node))
            elif _type == "ONE_TO_ONE":
                rtn.append(_threads.UserData._from_thread_fetch(self.session, node))
            else:
                rtn.append(None)
                log.warning("Unknown thread type: %s, data: %s", _type, node)
        return rtn

    def fetch_threads(
        self,
        limit: Optional[int],
        location: _models.ThreadLocation = _models.ThreadLocation.INBOX,
    ) -> Iterable[_threads.ThreadABC]:
        """Fetch the client's thread list.

        The returned threads are ordered by last active first.

        Args:
            limit: Max. number of threads to retrieve. If ``None``, all threads will be
                retrieved.
            location: INBOX, PENDING, ARCHIVED or OTHER

        Example:
            Fetch the last three threads that the user chatted with.

            >>> for thread in client.fetch_threads(limit=3):
            ...     print(f"{thread.id}: {thread.name}")
            ...
            1234: A user
            2345: A group
            3456: A page
        """
        # This is measured empirically as 837, safe default chosen below
        MAX_BATCH_LIMIT = 100

        # TODO: Clean this up after implementing support for more threads types
        seen_ids = set()  # type: Set[str]
        before = None
        for limit in _util.get_limits(limit, MAX_BATCH_LIMIT):
            threads = self._fetch_threads(limit, before, [location.value])

            before = None
            for thread in threads:
                # Don't return seen and unknown threads
                if thread and thread.id not in seen_ids:
                    seen_ids.add(thread.id)
                    # TODO: Ensure type-wise that .last_active is available
                    before = thread.last_active
                    yield thread

            if len(threads) < MAX_BATCH_LIMIT:
                return  # No more data to fetch

            # We check this here in case _fetch_threads only returned `None` threads
            if not before:
                raise ValueError("Too many unknown threads.")

    def fetch_unread(self) -> Sequence[_threads.ThreadABC]:
        """Fetch unread threads.

        Warning:
            This is not finished, and the API may change at any point!
        """
        at = datetime.datetime.utcnow()
        form = {
            "folders[0]": "inbox",
            "client": "mercury",
            "last_action_timestamp": _util.datetime_to_millis(at),
            # 'last_action_timestamp': 0
        }
        j = self.session._payload_post("/ajax/mercury/unread_threads.php", form)

        result = j["unread_thread_fbids"][0]
        # TODO: Parse Pages?
        return [
            _threads.Group(session=self.session, id=id_)
            for id_ in result["thread_fbids"]
        ] + [
            _threads.User(session=self.session, id=id_)
            for id_ in result["other_user_fbids"]
        ]

    def fetch_unseen(self) -> Sequence[_threads.ThreadABC]:
        """Fetch unseen / new threads.

        Warning:
            This is not finished, and the API may change at any point!
        """
        j = self.session._payload_post("/mercury/unseen_thread_ids/", {})

        result = j["unseen_thread_fbids"][0]
        # TODO: Parse Pages?
        return [
            _threads.Group(session=self.session, id=id_)
            for id_ in result["thread_fbids"]
        ] + [
            _threads.User(session=self.session, id=id_)
            for id_ in result["other_user_fbids"]
        ]

    def fetch_image_url(self, image_id: str) -> str:
        """Fetch URL to download the original image from an image attachment ID.

        Args:
            image_id: The image you want to fetch

        Example:
            >>> client.fetch_image_url("1234")
            "https://scontent-arn1-1.xx.fbcdn.net/v/t1.123-4/1_23_45_n.png?..."

        Returns:
            An URL where you can download the original image
        """
        image_id = str(image_id)
        data = {"photo_id": str(image_id)}
        j = self.session._post("/mercury/attachments/photo/", data)
        _exception.handle_payload_error(j)

        if "jsmods" not in j:
            raise _exception.ParseError("No jsmods when fetching image URL", data=j)
        require = _util.get_jsmods_require(j["jsmods"]["require"])
        if "ServerRedirect.redirectPageTo" not in require:
            raise _exception.ParseError("Could not fetch image URL", data=j)
        # Return the first argument
        return require["ServerRedirect.redirectPageTo"][0]

    def _get_private_data(self):
        (j,) = self.session._graphql_requests(
            _graphql.from_doc_id("1868889766468115", {})
        )
        return j["viewer"]

    def get_phone_numbers(self) -> Sequence[str]:
        """Fetch the user's phone numbers."""
        data = self._get_private_data()
        return [
            j["phone_number"]["universal_number"] for j in data["user"]["all_phones"]
        ]

    def get_emails(self) -> Sequence[str]:
        """Fetch the user's emails."""
        data = self._get_private_data()
        return [j["display_email"] for j in data["all_emails"]]

    def upload(
        self, files: Iterable[Tuple[str, BinaryIO, str]], voice_clip: bool = False
    ) -> Sequence[Tuple[str, str]]:
        """Upload files to Facebook.

        `files` should be a list of files that requests can upload, see
        `requests.request <https://docs.python-requests.org/en/master/api/#requests.request>`_.

        Example:
            >>> with open("file.txt", "rb") as f:
            ...     (file,) = client.upload([("file.txt", f, "text/plain")])
            ...
            >>> file
            ("1234", "text/plain")
        Return:
            Tuples with a file's ID and mimetype.
            This result can be passed straight on to `ThreadABC.send_files`, or used in
            `Group.set_image`.
        """
        file_dict = {"upload_{}".format(i): f for i, f in enumerate(files)}

        data = {"voice_clip": voice_clip}

        j = self.session._payload_post(
            "https://upload.messenger.com/ajax/mercury/upload.php",
            data,
            files=file_dict,
        )

        if len(j["metadata"]) != len(file_dict):
            raise _exception.ParseError("Some files could not be uploaded", data=j)

        return [
            (str(item[_util.mimetype_to_key(item["filetype"])]), item["filetype"])
            for item in j["metadata"]
        ]

    def mark_as_delivered(self, message: _models.Message):
        """Mark a message as delivered.

        Warning:
            This is not finished, and the API may change at any point!

        Args:
            message: The message to set as delivered
        """
        data = {
            "message_ids[0]": message.id,
            "thread_ids[%s][0]" % message.thread.id: message.id,
        }
        j = self.session._payload_post("/ajax/mercury/delivery_receipts.php", data)

    def _read_status(self, read, threads, at):
        data = {
            "watermarkTimestamp": _util.datetime_to_millis(at),
            "shouldSendReadReceipt": "true",
        }

        for thread in threads:
            data["ids[{}]".format(thread.id)] = "true" if read else "false"

        j = self.session._payload_post("/ajax/mercury/change_read_status.php", data)

    def mark_as_read(
        self, threads: Iterable[_threads.ThreadABC], at: datetime.datetime
    ):
        """Mark threads as read.

        All messages inside the specified threads will be marked as read.

        Args:
            threads: Threads to set as read
            at: Timestamp to signal the read cursor at
        """
        return self._read_status(True, threads, at)

    def mark_as_unread(
        self, threads: Iterable[_threads.ThreadABC], at: datetime.datetime
    ):
        """Mark threads as unread.

        All messages inside the specified threads will be marked as unread.

        Args:
            threads: Threads to set as unread
            at: Timestamp to signal the read cursor at
        """
        return self._read_status(False, threads, at)

    def mark_as_seen(self, at: datetime.datetime):
        # TODO: Documenting this
        data = {"seen_timestamp": _util.datetime_to_millis(at)}
        j = self.session._payload_post("/ajax/mercury/mark_seen.php", data)

    def move_threads(
        self, location: _models.ThreadLocation, threads: Iterable[_threads.ThreadABC]
    ):
        """Move threads to specified location.

        Args:
            location: INBOX, PENDING, ARCHIVED or OTHER
            threads: Threads to move
        """
        if location == _models.ThreadLocation.PENDING:
            location = _models.ThreadLocation.OTHER

        if location == _models.ThreadLocation.ARCHIVED:
            data_archive = {}
            data_unpin = {}
            for thread in threads:
                data_archive["ids[{}]".format(thread.id)] = "true"
                data_unpin["ids[{}]".format(thread.id)] = "false"
            j_archive = self.session._payload_post(
                "/ajax/mercury/change_archived_status.php?dpr=1", data_archive
            )
            j_unpin = self.session._payload_post(
                "/ajax/mercury/change_pinned_status.php?dpr=1", data_unpin
            )
        else:
            data = {}
            for i, thread in enumerate(threads):
                data["{}[{}]".format(location.name.lower(), i)] = thread.id
            j = self.session._payload_post("/ajax/mercury/move_threads.php", data)

    def delete_threads(self, threads: Iterable[_threads.ThreadABC]):
        """Bulk delete threads.

        Args:
            threads: Threads to delete

        Example:
            >>> group = fbchat.Group(session=session, id="1234")
            >>> client.delete_threads([group])
        """
        _threads.ThreadABC._delete_many(self.session, (t.id for t in threads))

    def delete_messages(self, messages: Iterable[_models.Message]):
        """Bulk delete specified messages.

        Args:
            messages: Messages to delete

        Example:
            >>> message1 = fbchat.Message(thread=thread, id="1234")
            >>> message2 = fbchat.Message(thread=thread, id="2345")
            >>> client.delete_threads([message1, message2])
        """
        _models.Message._delete_many(self.session, (m.id for m in messages))
