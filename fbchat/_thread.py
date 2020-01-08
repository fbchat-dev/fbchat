import abc
import attr
from ._core import attrs_default, Enum, Image
from . import _util, _session
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
            Message._from_graphql(message, read_receipts)
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
