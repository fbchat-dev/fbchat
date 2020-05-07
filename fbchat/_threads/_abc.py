import abc
import attr
import collections
import datetime
from .._common import log, attrs_default
from .. import _util, _exception, _session, _graphql, _models
from typing import MutableMapping, Mapping, Any, Iterable, Tuple, Optional


DEFAULT_COLOR = "#0084ff"
SETABLE_COLORS = (
    DEFAULT_COLOR,
    "#44bec7",
    "#ffc300",
    "#fa3c4c",
    "#d696bb",
    "#6699cc",
    "#13cf13",
    "#ff7e29",
    "#e68585",
    "#7646ff",
    "#20cef5",
    "#67b868",
    "#d4a88c",
    "#ff5ca1",
    "#a695c7",
    "#ff7ca8",
    "#1adb5b",
    "#f01d6a",
    "#ff9c19",
    "#0edcde",
)


class ThreadABC(metaclass=abc.ABCMeta):
    """Implemented by thread-like classes.

    This is private to implement.
    """

    @property
    @abc.abstractmethod
    def session(self) -> _session.Session:
        """The session to use when making requests."""
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def id(self) -> str:
        """The unique identifier of the thread."""
        raise NotImplementedError

    @abc.abstractmethod
    def _to_send_data(self) -> MutableMapping[str, str]:
        raise NotImplementedError

    # Note:
    # You can go out of Facebook's spec with `self.session._do_send_request`!
    #
    # A few examples:
    # - You can send a sticker and an emoji at the same time
    # - You can wave, send a sticker and text at the same time
    # - You can reply to a message with a sticker
    #
    # We won't support those use cases, it'll make for a confusing API!
    # If we absolutely need to in the future, we can always add extra functionality

    @abc.abstractmethod
    def _copy(self) -> "ThreadABC":
        """It may or may not be a good idea to attach the current thread to new objects.

        So for now, we use this method to create a new thread.

        This should return the minimal representation of the thread (e.g. not UserData).
        """
        raise NotImplementedError

    def fetch(self):
        # TODO: This
        raise NotImplementedError

    def wave(self, first: bool = True) -> str:
        """Wave hello to the thread.

        Args:
            first: Whether to wave first or wave back

        Example:
            Wave back to the thread.

            >>> thread.wave(False)
        """
        data = self._to_send_data()
        data["action_type"] = "ma-type:user-generated-message"
        data["lightweight_action_attachment[lwa_state]"] = (
            "INITIATED" if first else "RECIPROCATED"
        )
        data["lightweight_action_attachment[lwa_type]"] = "WAVE"
        message_id, thread_id = self.session._do_send_request(data)
        return message_id

    def send_text(
        self,
        text: str,
        mentions: Iterable["_models.Mention"] = None,
        files: Iterable[Tuple[str, str]] = None,
        reply_to_id: str = None,
    ) -> str:
        """Send a message to the thread.

        Args:
            text: Text to send
            mentions: Optional mentions
            files: Optional tuples, each containing an uploaded file's ID and mimetype.
                See `ThreadABC.send_files` for an example.
            reply_to_id: Optional message to reply to

        Example:
            >>> mention = fbchat.Mention(thread_id="1234", offset=5, length=2)
            >>> thread.send_text("A message", mentions=[mention])

        Returns:
            The sent message
        """
        data = self._to_send_data()
        data["action_type"] = "ma-type:user-generated-message"
        if text is not None:  # To support `send_files`
            data["body"] = text

        for i, mention in enumerate(mentions or ()):
            data.update(mention._to_send_data(i))

        if files:
            data["has_attachment"] = True

        for i, (file_id, mimetype) in enumerate(files or ()):
            data["{}s[{}]".format(_util.mimetype_to_key(mimetype), i)] = file_id

        if reply_to_id:
            data["replied_to_message_id"] = reply_to_id

        return self.session._do_send_request(data)

    def send_emoji(self, emoji: str, size: "_models.EmojiSize") -> str:
        """Send an emoji to the thread.

        Args:
            emoji: The emoji to send
            size: The size of the emoji

        Example:
            >>> thread.send_emoji("😀", size=fbchat.EmojiSize.LARGE)

        Returns:
            The sent message
        """
        data = self._to_send_data()
        data["action_type"] = "ma-type:user-generated-message"
        data["body"] = emoji
        data["tags[0]"] = "hot_emoji_size:{}".format(size.name.lower())
        return self.session._do_send_request(data)

    def send_sticker(self, sticker_id: str) -> str:
        """Send a sticker to the thread.

        Args:
            sticker_id: ID of the sticker to send

        Example:
            Send a sticker with the id "1889713947839631"

            >>> thread.send_sticker("1889713947839631")

        Returns:
            The sent message
        """
        data = self._to_send_data()
        data["action_type"] = "ma-type:user-generated-message"
        data["sticker_id"] = sticker_id
        return self.session._do_send_request(data)

    def _send_location(self, current, latitude, longitude):
        data = self._to_send_data()
        data["action_type"] = "ma-type:user-generated-message"
        data["location_attachment[coordinates][latitude]"] = latitude
        data["location_attachment[coordinates][longitude]"] = longitude
        data["location_attachment[is_current_location]"] = current
        return self.session._do_send_request(data)

    def send_location(self, latitude: float, longitude: float):
        """Send a given location to a thread as the user's current location.

        Args:
            latitude: The location latitude
            longitude: The location longitude

        Example:
            Send a location in London, United Kingdom.

            >>> thread.send_location(51.5287718, -0.2416815)
        """
        self._send_location(True, latitude=latitude, longitude=longitude)

    def send_pinned_location(self, latitude: float, longitude: float):
        """Send a given location to a thread as a pinned location.

        Args:
            latitude: The location latitude
            longitude: The location longitude

        Example:
            Send a pinned location in Beijing, China.

            >>> thread.send_pinned_location(39.9390731, 116.117273)
        """
        self._send_location(False, latitude=latitude, longitude=longitude)

    def send_files(self, files: Iterable[Tuple[str, str]]):
        """Send files from file IDs to a thread.

        `files` should be a list of tuples, with a file's ID and mimetype.

        Example:
            Upload and send a video to a thread.

            >>> with open("video.mp4", "rb") as f:
            ...     files = client.upload([("video.mp4", f, "video/mp4")])
            >>>
            >>> thread.send_files(files)
        """
        return self.send_text(text=None, files=files)

    # xmd = {"quick_replies": []}
    # for quick_reply in quick_replies:
    #     # TODO: Move this to `_quick_reply.py`
    #     q = dict()
    #     q["content_type"] = quick_reply._type
    #     q["payload"] = quick_reply.payload
    #     q["external_payload"] = quick_reply.external_payload
    #     q["data"] = quick_reply.data
    #     if quick_reply.is_response:
    #         q["ignore_for_webhook"] = False
    #     if isinstance(quick_reply, _quick_reply.QuickReplyText):
    #         q["title"] = quick_reply.title
    #     if not isinstance(quick_reply, _quick_reply.QuickReplyLocation):
    #         q["image_url"] = quick_reply.image_url
    #     xmd["quick_replies"].append(q)
    # if len(quick_replies) == 1 and quick_replies[0].is_response:
    #     xmd["quick_replies"] = xmd["quick_replies"][0]
    # data["platform_xmd"] = _util.json_minimal(xmd)

    # TODO: This!
    # def quick_reply(self, quick_reply: QuickReply, payload=None):
    #     """Reply to chosen quick reply.
    #
    #     Args:
    #         quick_reply: Quick reply to reply to
    #         payload: Optional answer to the quick reply
    #     """
    #     if isinstance(quick_reply, QuickReplyText):
    #         new = QuickReplyText(
    #             payload=quick_reply.payload,
    #             external_payload=quick_reply.external_payload,
    #             data=quick_reply.data,
    #             is_response=True,
    #             title=quick_reply.title,
    #             image_url=quick_reply.image_url,
    #         )
    #         return self.send(Message(text=quick_reply.title, quick_replies=[new]))
    #     elif isinstance(quick_reply, QuickReplyLocation):
    #         if not isinstance(payload, LocationAttachment):
    #             raise TypeError("Payload must be an instance of `LocationAttachment`")
    #         return self.send_location(payload)
    #     elif isinstance(quick_reply, QuickReplyEmail):
    #         new = QuickReplyEmail(
    #             payload=payload if payload else self.get_emails()[0],
    #             external_payload=quick_reply.payload,
    #             data=quick_reply.data,
    #             is_response=True,
    #             image_url=quick_reply.image_url,
    #         )
    #         return self.send(Message(text=payload, quick_replies=[new]))
    #     elif isinstance(quick_reply, QuickReplyPhoneNumber):
    #         new = QuickReplyPhoneNumber(
    #             payload=payload if payload else self.get_phone_numbers()[0],
    #             external_payload=quick_reply.payload,
    #             data=quick_reply.data,
    #             is_response=True,
    #             image_url=quick_reply.image_url,
    #         )
    #         return self.send(Message(text=payload, quick_replies=[new]))

    def _search_messages(self, query, offset, limit):
        data = {
            "query": query,
            "snippetOffset": offset,
            "snippetLimit": limit,
            "identifier": "thread_fbid",
            "thread_fbid": self.id,
        }
        j = self.session._payload_post("/ajax/mercury/search_snippets.php?dpr=1", data)

        result = j["search_snippets"][query].get(self.id)
        if not result:
            return (0, [])

        thread = self._copy()
        snippets = [
            _models.MessageSnippet._parse(thread, snippet)
            for snippet in result["snippets"]
        ]
        return (result["num_total_snippets"], snippets)

    def search_messages(
        self, query: str, limit: int
    ) -> Iterable[_models.MessageSnippet]:
        """Find and get message IDs by query.

        Warning! If someone send a message to the thread that matches the query, while
        we're searching, some snippets will get returned twice.

        This is fundamentally not fixable, it's just how the endpoint is implemented.

        The returned message snippets are ordered by last sent first.

        Args:
            query: Text to search for
            limit: Max. number of message snippets to retrieve

        Example:
            Fetch the latest message in the thread that matches the query.

            >>> (message,) = thread.search_messages("abc", limit=1)
            >>> message.text
            "Some text and abc"
        """
        offset = 0
        # The max limit is measured empirically to 420, safe default chosen below
        for limit in _util.get_limits(limit, max_limit=50):
            _, snippets = self._search_messages(query, offset, limit)
            yield from snippets
            if len(snippets) < limit:
                return  # No more data to fetch
            offset += limit

    def _fetch_messages(self, limit, before):
        params = {
            "id": self.id,
            "message_limit": limit,
            "load_messages": True,
            "load_read_receipts": True,
            # "load_delivery_receipts": False,
            # "is_work_teamwork_not_putting_muted_in_unreads": False,
            "before": _util.datetime_to_millis(before) if before else None,
        }
        (j,) = self.session._graphql_requests(
            _graphql.from_doc_id("1860982147341344", params)  # 2696825200377124
        )

        if j.get("message_thread") is None:
            raise _exception.ParseError("Could not fetch messages", data=j)

        # TODO: Should we parse the returned thread data, too?

        read_receipts = j["message_thread"]["read_receipts"]["nodes"]

        thread = self._copy()
        return [
            _models.MessageData._from_graphql(thread, message, read_receipts)
            for message in j["message_thread"]["messages"]["nodes"]
        ]

    def fetch_messages(self, limit: Optional[int]) -> Iterable["_models.Message"]:
        """Fetch messages in a thread.

        The returned messages are ordered by last sent first.

        Args:
            limit: Max. number of threads to retrieve. If ``None``, all threads will be
                retrieved.

        Example:
            >>> for message in thread.fetch_messages(limit=5)
            ...     print(message.text)
            ...
            A message
            Another message
            None
            A fourth message
        """
        # This is measured empirically as 210 in extreme cases, fairly safe default
        # chosen below
        MAX_BATCH_LIMIT = 100

        before = None
        for limit in _util.get_limits(limit, MAX_BATCH_LIMIT):
            messages = self._fetch_messages(limit, before)
            messages.reverse()

            if before:
                # Strip the first messages
                yield from messages[1:]
            else:
                yield from messages

            if len(messages) < MAX_BATCH_LIMIT:
                return  # No more data to fetch

            before = messages[-1].created_at

    def _fetch_images(self, limit, after):
        data = {"id": self.id, "first": limit, "after": after}
        (j,) = self.session._graphql_requests(
            _graphql.from_query_id("515216185516880", data)
        )

        if not j[self.id]:
            raise _exception.ParseError("Could not find images", data=j)

        result = j[self.id]["message_shared_media"]

        rtn = []
        for edge in result["edges"]:
            node = edge["node"]
            type_ = node["__typename"]
            if type_ == "MessageImage":
                rtn.append(_models.ImageAttachment._from_list(node))
            elif type_ == "MessageVideo":
                rtn.append(_models.VideoAttachment._from_list(node))
            else:
                log.warning("Unknown image type %s, data: %s", type_, edge)
                rtn.append(None)

        # result["page_info"]["has_next_page"] is not correct when limit > 12
        return (result["page_info"]["end_cursor"], rtn)

    def fetch_images(self, limit: Optional[int]) -> Iterable["_models.Attachment"]:
        """Fetch images/videos posted in the thread.

        The returned images are ordered by last sent first.

        Args:
            limit: Max. number of images to retrieve. If ``None``, all images will be
                retrieved.

        Example:
            >>> for image in thread.fetch_messages(limit=3)
            ...     print(image.id)
            ...
            1234
            2345
        """
        cursor = None
        # The max limit on this request is unknown, so we set it reasonably high
        # This way `limit=None` also still works
        for limit in _util.get_limits(limit, max_limit=1000):
            cursor, images = self._fetch_images(limit, cursor)
            if not images:
                return  # No more data to fetch
            for image in images:
                if image:
                    yield image

    def set_nickname(self, user_id: str, nickname: str):
        """Change the nickname of a user in the thread.

        Args:
            user_id: User that will have their nickname changed
            nickname: New nickname

        Example:
            >>> thread.set_nickname("1234", "A nickname")
        """
        data = {
            "nickname": nickname,
            "participant_id": user_id,
            "thread_or_other_fbid": self.id,
        }
        j = self.session._payload_post(
            "/messaging/save_thread_nickname/?source=thread_settings&dpr=1", data
        )

    def set_color(self, color: str):
        """Change thread color.

        The new color must be one of the following::

            "#0084ff", "#44bec7", "#ffc300", "#fa3c4c", "#d696bb", "#6699cc",
            "#13cf13", "#ff7e29", "#e68585", "#7646ff", "#20cef5", "#67b868",
            "#d4a88c", "#ff5ca1", "#a695c7", "#ff7ca8", "#1adb5b", "#f01d6a",
            "#ff9c19" or "#0edcde".

        This list is subject to change in the future!

        The default when creating a new thread is ``"#0084ff"``.

        Args:
            color: New thread color

        Example:
            Set the thread color to "Coral Pink".

            >>> thread.set_color("#e68585")
        """
        if color not in SETABLE_COLORS:
            raise ValueError(
                "Invalid color! Please use one of: {}".format(SETABLE_COLORS)
            )

        # Set color to "" if DEFAULT_COLOR. Just how the endpoint works...
        if color == DEFAULT_COLOR:
            color = ""

        data = {"color_choice": color, "thread_or_other_fbid": self.id}
        j = self.session._payload_post(
            "/messaging/save_thread_color/?source=thread_settings&dpr=1", data
        )

    # def set_theme(self, theme_id: str):
    #     data = {
    #         "client_mutation_id": "0",
    #         "actor_id": self.session.user.id,
    #         "thread_id": self.id,
    #         "theme_id": theme_id,
    #         "source": "SETTINGS",
    #     }
    #     j = self.session._graphql_requests(
    #         _graphql.from_doc_id("1768656253222505", {"data": data})
    #     )

    def set_emoji(self, emoji: Optional[str]):
        """Change thread emoji.

        Args:
            emoji: New thread emoji. If ``None``, will be set to the default "LIKE" icon

        Example:
            Set the thread emoji to "😊".

            >>> thread.set_emoji("😊")
        """
        data = {"emoji_choice": emoji, "thread_or_other_fbid": self.id}
        # While changing the emoji, the Facebook web client actually sends multiple
        # different requests, though only this one is required to make the change.
        j = self.session._payload_post(
            "/messaging/save_thread_emoji/?source=thread_settings&dpr=1", data
        )

    def forward_attachment(self, attachment_id: str):
        """Forward an attachment.

        Args:
            attachment_id: Attachment ID to forward

        Example:
            >>> thread.forward_attachment("1234")
        """
        data = {
            "attachment_id": attachment_id,
            "recipient_map[{}]".format(_util.generate_offline_threading_id()): self.id,
        }
        j = self.session._payload_post("/mercury/attachments/forward/", data)
        if not j.get("success"):
            raise _exception.ExternalError("Failed forwarding attachment", j["error"])

    def _set_typing(self, typing):
        data = {
            "typ": "1" if typing else "0",
            "thread": self.id,
            # TODO: This
            # "to": self.id if isinstance(self, _user.User) else "",
            "source": "mercury-chat",
        }
        j = self.session._payload_post("/ajax/messaging/typ.php", data)

    def start_typing(self):
        """Set the current user to start typing in the thread.

        Example:
            >>> thread.start_typing()
        """
        self._set_typing(True)

    def stop_typing(self):
        """Set the current user to stop typing in the thread.

        Example:
            >>> thread.stop_typing()
        """
        self._set_typing(False)

    def create_plan(
        self,
        name: str,
        at: datetime.datetime,
        location_name: str = None,
        location_id: str = None,
    ):
        """Create a new plan.

        # TODO: Arguments

        Args:
            name: Name of the new plan
            at: When the plan is for

        Example:
            >>> thread.create_plan(...)
        """
        return _models.Plan._create(self, name, at, location_name, location_id)

    def create_poll(self, question: str, options: Mapping[str, bool]):
        """Create poll in a thread.

        Args:
            question: The question
            options: Options and whether you want to select the option

        Example:
            >>> thread.create_poll("Test poll", {"Option 1": True, "Option 2": False})
        """
        # We're using ordered dictionaries, because the Facebook endpoint that parses
        # the POST parameters is badly implemented, and deals with ordering the options
        # wrongly. If you can find a way to fix this for the endpoint, or if you find
        # another endpoint, please do suggest it ;)
        data = collections.OrderedDict(
            [("question_text", question), ("target_id", self.id)]
        )

        for i, (text, vote) in enumerate(options.items()):
            data["option_text_array[{}]".format(i)] = text
            data["option_is_selected_array[{}]".format(i)] = "1" if vote else "0"

        j = self.session._payload_post(
            "/messaging/group_polling/create_poll/?dpr=1", data
        )
        if j.get("status") != "success":
            raise _exception.ExternalError(
                "Failed creating poll: {}".format(j.get("errorTitle")),
                j.get("errorMessage"),
            )

    def mute(self, duration: datetime.timedelta = None):
        """Mute the thread.

        Args:
            duration: Time to mute, use ``None`` to mute forever

        Example:
            >>> import datetime
            >>> thread.mute(datetime.timedelta(days=2))
        """
        if duration is None:
            setting = "-1"
        else:
            setting = str(_util.timedelta_to_seconds(duration))
        data = {"mute_settings": setting, "thread_fbid": self.id}
        j = self.session._payload_post(
            "/ajax/mercury/change_mute_thread.php?dpr=1", data
        )

    def unmute(self):
        """Unmute the thread.

        Example:
            >>> thread.unmute()
        """
        return self.mute(datetime.timedelta(0))

    def _mute_reactions(self, mode: bool):
        data = {"reactions_mute_mode": "1" if mode else "0", "thread_fbid": self.id}
        j = self.session._payload_post(
            "/ajax/mercury/change_reactions_mute_thread/?dpr=1", data
        )

    def mute_reactions(self):
        """Mute thread reactions."""
        self._mute_reactions(True)

    def unmute_reactions(self):
        """Unmute thread reactions."""
        self._mute_reactions(False)

    def _mute_mentions(self, mode: bool):
        data = {"mentions_mute_mode": "1" if mode else "0", "thread_fbid": self.id}
        j = self.session._payload_post(
            "/ajax/mercury/change_mentions_mute_thread/?dpr=1", data
        )

    def mute_mentions(self):
        """Mute thread mentions."""
        self._mute_mentions(True)

    def unmute_mentions(self):
        """Unmute thread mentions."""
        self._mute_mentions(False)

    def mark_as_spam(self):
        """Mark the thread as spam, and delete it."""
        data = {"id": self.id}
        j = self.session._payload_post("/ajax/mercury/mark_spam.php?dpr=1", data)

    @staticmethod
    def _delete_many(session, thread_ids):
        data = {}
        for i, id_ in enumerate(thread_ids):
            data["ids[{}]".format(i)] = id_
        # Not needed any more
        # j = session._payload_post("/ajax/mercury/change_pinned_status.php?dpr=1", ...)
        # Both /ajax/mercury/delete_threads.php (with an s) doesn't work
        j = session._payload_post("/ajax/mercury/delete_thread.php", data)

    def delete(self):
        """Delete the thread.

        If you want to delete multiple threads, please use `Client.delete_threads`.

        Example:
            >>> message.delete()
        """
        self._delete_many(self.session, [self.id])

    def _forced_fetch(self, message_id: str) -> dict:
        params = {
            "thread_and_message_id": {"thread_id": self.id, "message_id": message_id}
        }
        (j,) = self.session._graphql_requests(
            _graphql.from_doc_id("1768656253222505", params)
        )
        return j

    @staticmethod
    def _parse_color(inp: Optional[str]) -> str:
        if not inp:
            return DEFAULT_COLOR
        # Strip the alpha value, and lower the string
        return "#{}".format(inp[2:].lower())

    @staticmethod
    def _parse_customization_info(data: Any) -> MutableMapping[str, Any]:
        if not data or not data.get("customization_info"):
            return {"emoji": None, "color": DEFAULT_COLOR}
        info = data["customization_info"]

        rtn = {
            "emoji": info.get("emoji"),
            "color": ThreadABC._parse_color(info.get("outgoing_bubble_color")),
        }
        if (
            data.get("thread_type") == "GROUP"
            or data.get("is_group_thread")
            or data.get("thread_key", {}).get("thread_fbid")
        ):
            rtn["nicknames"] = {}
            for k in info.get("participant_customizations", []):
                rtn["nicknames"][k["participant_id"]] = k.get("nickname")
        elif info.get("participant_customizations"):
            user_id = data.get("thread_key", {}).get("other_user_id") or data.get("id")
            pc = info["participant_customizations"]
            if len(pc) > 0:
                if pc[0].get("participant_id") == user_id:
                    rtn["nickname"] = pc[0].get("nickname")
                else:
                    rtn["own_nickname"] = pc[0].get("nickname")
            if len(pc) > 1:
                if pc[1].get("participant_id") == user_id:
                    rtn["nickname"] = pc[1].get("nickname")
                else:
                    rtn["own_nickname"] = pc[1].get("nickname")
        return rtn

    @staticmethod
    def _parse_participants(session, data) -> Iterable["ThreadABC"]:
        from . import _user, _group, _page

        for node in data["nodes"]:
            actor = node["messaging_actor"]
            typename = actor["__typename"]
            thread_id = actor["id"]
            if typename == "User":
                yield _user.User(session=session, id=thread_id)
            elif typename == "MessageThread":
                # MessageThread => Group thread
                yield _group.Group(session=session, id=thread_id)
            elif typename == "Page":
                yield _page.Page(session=session, id=thread_id)
            elif typename == "Group":
                # We don't handle Facebook "Groups"
                pass
            else:
                log.warning("Unknown type %r in %s", typename, data)


@attrs_default
class Thread(ThreadABC):
    """Represents a Facebook thread, where the actual type is unknown.

    Implements parts of `ThreadABC`, call the method to figure out if your use case is
    supported. Otherwise, you'll have to use an `User`/`Group`/`Page` object.

    Note: This list may change in minor versions!
    """

    #: The session to use when making requests.
    session = attr.ib(type=_session.Session)
    #: The unique identifier of the thread.
    id = attr.ib(converter=str, type=str)

    def _to_send_data(self):
        raise NotImplementedError(
            "The method you called is not supported on raw Thread objects."
            " Please use an appropriate User/Group/Page object instead!"
        )

    def _copy(self) -> "Thread":
        return Thread(session=self.session, id=self.id)
