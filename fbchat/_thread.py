import abc
import attr
from ._core import attrs_default, Enum, Image
from . import _session
from typing import MutableMapping, Any


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
