import abc
import attr
import datetime
from ._core import attrs_default, Enum, Image
from . import _util, _exception, _session
from typing import MutableMapping, Any, Iterable, Tuple


class ThreadType(Enum):
    """Used to specify what type of Facebook thread is being used.

    See :ref:`intro_threads` for more info.
    """

    USER = 1
    GROUP = 2
    PAGE = 3

    def _to_class(self):
        """Convert this enum value to the corresponding class."""
        from . import _user, _group, _page

        return {
            ThreadType.USER: _user.User,
            ThreadType.GROUP: _group.Group,
            ThreadType.PAGE: _page.Page,
        }[self]


class ThreadLocation(Enum):
    """Used to specify where a thread is located (inbox, pending, archived, other)."""

    INBOX = "INBOX"
    PENDING = "PENDING"
    ARCHIVED = "ARCHIVED"
    OTHER = "OTHER"


class ThreadColor(Enum):
    """Used to specify a thread colors."""

    MESSENGER_BLUE = "#0084ff"
    VIKING = "#44bec7"
    GOLDEN_POPPY = "#ffc300"
    RADICAL_RED = "#fa3c4c"
    SHOCKING = "#d696bb"
    PICTON_BLUE = "#6699cc"
    FREE_SPEECH_GREEN = "#13cf13"
    PUMPKIN = "#ff7e29"
    LIGHT_CORAL = "#e68585"
    MEDIUM_SLATE_BLUE = "#7646ff"
    DEEP_SKY_BLUE = "#20cef5"
    FERN = "#67b868"
    CAMEO = "#d4a88c"
    BRILLIANT_ROSE = "#ff5ca1"
    BILOBA_FLOWER = "#a695c7"
    TICKLE_ME_PINK = "#ff7ca8"
    MALACHITE = "#1adb5b"
    RUBY = "#f01d6a"
    DARK_TANGERINE = "#ff9c19"
    BRIGHT_TURQUOISE = "#0edcde"

    @classmethod
    def _from_graphql(cls, color):
        if color is None:
            return None
        if not color:
            return cls.MESSENGER_BLUE
        color = color[2:]  # Strip the alpha value
        value = "#{}".format(color.lower())
        return cls._extend_if_invalid(value)


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

    def wave(self, first: bool = True) -> str:
        """Wave hello to the thread.

        Args:
            first: Whether to wave first or wave back
        """
        data = self._to_send_data()
        data["action_type"] = "ma-type:user-generated-message"
        data["lightweight_action_attachment[lwa_state]"] = (
            "INITIATED" if first else "RECIPROCATED"
        )
        data["lightweight_action_attachment[lwa_type]"] = "WAVE"
        # TODO: This!
        # if thread_type == ThreadType.USER:
        #     data["specific_to_list[0]"] = "fbid:{}".format(thread_id)
        message_id, thread_id = self.session._do_send_request(data)
        return message_id

    def send(self, message) -> str:
        """Send message to the thread.

        Args:
            message (Message): Message to send

        Returns:
            :ref:`Message ID <intro_message_ids>` of the sent message
        """
        data = self._to_send_data()
        data.update(message._to_send_data())
        return self.session._do_send_request(data)

    def _send_location(self, current, latitude, longitude, message=None) -> str:
        data = self._to_send_data()
        if message is not None:
            data.update(message._to_send_data())
        data["action_type"] = "ma-type:user-generated-message"
        data["location_attachment[coordinates][latitude]"] = latitude
        data["location_attachment[coordinates][longitude]"] = longitude
        data["location_attachment[is_current_location]"] = current
        return self.session._do_send_request(data)

    def send_location(self, latitude: float, longitude: float, message=None):
        """Send a given location to a thread as the user's current location.

        Args:
            latitude: The location latitude
            longitude: The location longitude
            message: Additional message
        """
        self._send_location(
            True, latitude=latitude, longitude=longitude, message=message,
        )

    def send_pinned_location(self, latitude: float, longitude: float, message=None):
        """Send a given location to a thread as a pinned location.

        Args:
            latitude: The location latitude
            longitude: The location longitude
            message: Additional message
        """
        self._send_location(
            False, latitude=latitude, longitude=longitude, message=message,
        )

    def send_files(self, files: Iterable[Tuple[str, str]], message):
        """Send files from file IDs to a thread.

        `files` should be a list of tuples, with a file's ID and mimetype.
        """
        data = self._to_send_data()
        data.update(message._to_send_data())
        data["action_type"] = "ma-type:user-generated-message"
        data["has_attachment"] = True

        for i, (file_id, mimetype) in enumerate(files):
            data["{}s[{}]".format(_util.mimetype_to_key(mimetype), i)] = file_id

        return self.session._do_send_request(data)

    # TODO: This!
    # def quick_reply(self, quick_reply, payload=None):
    #     """Reply to chosen quick reply.
    #
    #     Args:
    #         quick_reply (QuickReply): Quick reply to reply to
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

    def search_messages(
        self, query: str, offset: int = 0, limit: int = 5
    ) -> Iterable[str]:
        """Find and get message IDs by query.

        Args:
            query: Text to search for
            offset (int): Number of messages to skip
            limit (int): Max. number of messages to retrieve

        Returns:
            typing.Iterable: Found Message IDs
        """
        # TODO: Return proper searchable iterator
        data = {
            "query": query,
            "snippetOffset": offset,
            "snippetLimit": limit,
            "identifier": "thread_fbid",
            "thread_fbid": self.id,
        }
        j = self.session._payload_post("/ajax/mercury/search_snippets.php?dpr=1", data)

        result = j["search_snippets"][query]
        snippets = result[self.id]["snippets"] if result.get(self.id) else []
        for snippet in snippets:
            yield snippet["message_id"]

    def fetch_messages(self, limit: int = 20, before: datetime.datetime = None):
        """Fetch messages in a thread, ordered by most recent.

        Args:
            limit: Max. number of messages to retrieve
            before: The point from which to retrieve messages

        Returns:
            list: `Message` objects
        """
        # TODO: Return proper searchable iterator
        params = {
            "id": self.id,
            "message_limit": limit,
            "load_messages": True,
            "load_read_receipts": True,
            "before": _util.datetime_to_millis(before) if before else None,
        }
        (j,) = self.session._graphql_requests(
            _graphql.from_doc_id("1860982147341344", params)
        )

        if j.get("message_thread") is None:
            raise FBchatException("Could not fetch thread {}: {}".format(self.id, j))

        read_receipts = j["message_thread"]["read_receipts"]["nodes"]

        messages = [
            Message._from_graphql(self.session, message, read_receipts)
            for message in j["message_thread"]["messages"]["nodes"]
        ]
        messages.reverse()

        return messages

    def fetch_images(self):
        """Fetch images/videos posted in the thread."""
        # TODO: Return proper searchable iterator
        data = {"id": self.id, "first": 48}
        (j,) = self.session._graphql_requests(
            _graphql.from_query_id("515216185516880", data)
        )
        while True:
            try:
                i = j[self.id]["message_shared_media"]["edges"][0]
            except IndexError:
                if j[self.id]["message_shared_media"]["page_info"].get("has_next_page"):
                    data["after"] = j[self.id]["message_shared_media"]["page_info"].get(
                        "end_cursor"
                    )
                    (j,) = self.session._graphql_requests(
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
                yield Attachment(id=i["node"].get("legacy_attachment_id"))
            del j[self.id]["message_shared_media"]["edges"][0]

    def set_nickname(self, user_id: str, nickname: str):
        """Change the nickname of a user in the thread.

        Args:
            user_id: User that will have their nickname changed
            nickname: New nickname
        """
        data = {
            "nickname": nickname,
            "participant_id": user_id,
            "thread_or_other_fbid": self.id,
        }
        j = self.session._payload_post(
            "/messaging/save_thread_nickname/?source=thread_settings&dpr=1", data
        )

    def set_color(self, color: ThreadColor):
        """Change thread color.

        Args:
            color: New thread color
        """
        data = {
            "color_choice": color.value if color != ThreadColor.MESSENGER_BLUE else "",
            "thread_or_other_fbid": self.id,
        }
        j = self.session._payload_post(
            "/messaging/save_thread_color/?source=thread_settings&dpr=1", data
        )

    def set_emoji(self, emoji: str):
        """Change thread color.

        Args:
            emoji: New thread emoji
        """
        data = {"emoji_choice": emoji, "thread_or_other_fbid": self.id}
        # While changing the emoji, the Facebook web client actually sends multiple
        # different requests, though only this one is required to make the change.
        j = self.session._payload_post(
            "/messaging/save_thread_emoji/?source=thread_settings&dpr=1", data
        )

    def forward_attachment(self, attachment_id):
        """Forward an attachment.

        Args:
            attachment_id: Attachment ID to forward
        """
        data = {
            "attachment_id": attachment_id,
            "recipient_map[{}]".format(_util.generate_offline_threading_id()): self.id,
        }
        j = self.session._payload_post("/mercury/attachments/forward/", data)
        if not j.get("success"):
            raise _exception.FBchatFacebookError(
                "Failed forwarding attachment: {}".format(j["error"]),
                fb_error_message=j["error"],
            )

    def _set_typing(self, typing):
        data = {
            "typ": "1" if typing else "0",
            "thread": self.id,
            # TODO: This
            "to": self.id if thread_type == ThreadType.USER else "",
            "source": "mercury-chat",
        }
        j = self.session._payload_post("/ajax/messaging/typ.php", data)

    def start_typing(self):
        """Set the current user to start typing in the thread."""
        self._set_typing(True)

    def stop_typing(self):
        """Set the current user to stop typing in the thread."""
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
            title: Name of the new plan
            at: When the plan is for
        """
        data = {
            "event_type": "EVENT",
            "event_time": _util.datetime_to_seconds(at),
            "title": name,
            "thread_id": self.id,
            "location_id": location_id or "",
            "location_name": location or "",
            "acontext": ACONTEXT,
        }
        j = self.session._payload_post("/ajax/eventreminder/create", data)
        if "error" in j:
            raise _exception.FBchatFacebookError(
                "Failed creating plan: {}".format(j["error"]),
                fb_error_message=j["error"],
            )

    def create_poll(self, question: str, options=Iterable[Tuple[str, bool]]):
        """Create poll in a thread.

        # TODO: Arguments
        """
        # We're using ordered dictionaries, because the Facebook endpoint that parses
        # the POST parameters is badly implemented, and deals with ordering the options
        # wrongly. If you can find a way to fix this for the endpoint, or if you find
        # another endpoint, please do suggest it ;)
        data = OrderedDict([("question_text", question), ("target_id", self.id)])

        for i, (text, vote) in enumerate(options):
            data["option_text_array[{}]".format(i)] = text
            data["option_is_selected_array[{}]".format(i)] = str(int(vote))

        j = self.session._payload_post(
            "/messaging/group_polling/create_poll/?dpr=1", data
        )
        if j.get("status") != "success":
            raise _exception.FBchatFacebookError(
                "Failed creating poll: {}".format(j.get("errorTitle")),
                fb_error_message=j.get("errorMessage"),
            )

    def mute(self, duration: datetime.timedelta = None):
        """Mute the thread.

        Args:
            duration: Time to mute, use ``None`` to mute forever
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
        """Unmute the thread."""
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

    def _forced_fetch(self, message_id: str) -> dict:
        params = {
            "thread_and_message_id": {"thread_id": self.id, "message_id": message_id}
        }
        (j,) = self.session._graphql_requests(
            _graphql.from_doc_id("1768656253222505", params)
        )
        return j

    @staticmethod
    def _parse_customization_info(data: Any) -> MutableMapping[str, Any]:
        if data is None or data.get("customization_info") is None:
            return {}
        info = data["customization_info"]

        rtn = {
            "emoji": info.get("emoji"),
            "color": ThreadColor._from_graphql(info.get("outgoing_bubble_color")),
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
    id = attr.ib(converter=str)

    def _to_send_data(self):
        raise NotImplementedError(
            "The method you called is not supported on raw Thread objects."
            " Please use an appropriate User/Group/Page object instead!"
        )
