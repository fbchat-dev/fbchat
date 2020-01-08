import attr
from ._core import attrs_default, Enum, Image
from . import _util, _session, _plan
from ._thread import ThreadType, Thread


GENDERS = {
    # For standard requests
    0: "unknown",
    1: "female_singular",
    2: "male_singular",
    3: "female_singular_guess",
    4: "male_singular_guess",
    5: "mixed",
    6: "neuter_singular",
    7: "unknown_singular",
    8: "female_plural",
    9: "male_plural",
    10: "neuter_plural",
    11: "unknown_plural",
    # For graphql requests
    "UNKNOWN": "unknown",
    "FEMALE": "female_singular",
    "MALE": "male_singular",
    # '': 'female_singular_guess',
    # '': 'male_singular_guess',
    # '': 'mixed',
    "NEUTER": "neuter_singular",
    # '': 'unknown_singular',
    # '': 'female_plural',
    # '': 'male_plural',
    # '': 'neuter_plural',
    # '': 'unknown_plural',
}


class TypingStatus(Enum):
    """Used to specify whether the user is typing or has stopped typing."""

    STOPPED = 0
    TYPING = 1


@attrs_default
class User(Thread):
    """Represents a Facebook user. Inherits `Thread`."""

    type = ThreadType.USER

    #: The session to use when making requests.
    session = attr.ib(type=_session.Session)
    #: The user's unique identifier.
    id = attr.ib(converter=str)
    #: The user's picture
    photo = attr.ib(None)
    #: The name of the user
    name = attr.ib(None)
    #: Datetime when the thread was last active / when the last message was sent
    last_active = attr.ib(None)
    #: Number of messages in the thread
    message_count = attr.ib(None)
    #: Set `Plan`
    plan = attr.ib(None)
    #: The profile URL
    url = attr.ib(None)
    #: The users first name
    first_name = attr.ib(None)
    #: The users last name
    last_name = attr.ib(None)
    #: Whether the user and the client are friends
    is_friend = attr.ib(None)
    #: The user's gender
    gender = attr.ib(None)
    #: From 0 to 1. How close the client is to the user
    affinity = attr.ib(None)
    #: The user's nickname
    nickname = attr.ib(None)
    #: The clients nickname, as seen by the user
    own_nickname = attr.ib(None)
    #: A `ThreadColor`. The message color
    color = attr.ib(None)
    #: The default emoji
    emoji = attr.ib(None)

    @classmethod
    def _from_graphql(cls, session, data):
        if data.get("profile_picture") is None:
            data["profile_picture"] = {}
        c_info = cls._parse_customization_info(data)
        plan = None
        if data.get("event_reminders") and data["event_reminders"].get("nodes"):
            plan = _plan.Plan._from_graphql(data["event_reminders"]["nodes"][0])

        return cls(
            session=session,
            id=data["id"],
            url=data.get("url"),
            first_name=data.get("first_name"),
            last_name=data.get("last_name"),
            is_friend=data.get("is_viewer_friend"),
            gender=GENDERS.get(data.get("gender")),
            affinity=data.get("affinity"),
            nickname=c_info.get("nickname"),
            color=c_info.get("color"),
            emoji=c_info.get("emoji"),
            own_nickname=c_info.get("own_nickname"),
            photo=Image._from_uri(data["profile_picture"]),
            name=data.get("name"),
            message_count=data.get("messages_count"),
            plan=plan,
        )

    @classmethod
    def _from_thread_fetch(cls, session, data):
        if data.get("big_image_src") is None:
            data["big_image_src"] = {}
        c_info = cls._parse_customization_info(data)
        participants = [
            node["messaging_actor"] for node in data["all_participants"]["nodes"]
        ]
        user = next(
            p for p in participants if p["id"] == data["thread_key"]["other_user_id"]
        )
        last_active = None
        if "last_message" in data:
            last_active = _util.millis_to_datetime(
                int(data["last_message"]["nodes"][0]["timestamp_precise"])
            )

        first_name = user.get("short_name")
        if first_name is None:
            last_name = None
        else:
            last_name = user.get("name").split(first_name, 1).pop().strip()

        plan = None
        if data.get("event_reminders") and data["event_reminders"].get("nodes"):
            plan = _plan.Plan._from_graphql(data["event_reminders"]["nodes"][0])

        return cls(
            session=session,
            id=user["id"],
            url=user.get("url"),
            name=user.get("name"),
            first_name=first_name,
            last_name=last_name,
            is_friend=user.get("is_viewer_friend"),
            gender=GENDERS.get(user.get("gender")),
            affinity=user.get("affinity"),
            nickname=c_info.get("nickname"),
            color=c_info.get("color"),
            emoji=c_info.get("emoji"),
            own_nickname=c_info.get("own_nickname"),
            photo=Image._from_uri(user["big_image_src"]),
            message_count=data.get("messages_count"),
            last_active=last_active,
            plan=plan,
        )

    @classmethod
    def _from_all_fetch(cls, session, data):
        return cls(
            session=session,
            id=data["id"],
            first_name=data.get("firstName"),
            url=data.get("uri"),
            photo=Image(url=data.get("thumbSrc")),
            name=data.get("name"),
            is_friend=data.get("is_friend"),
            gender=GENDERS.get(data.get("gender")),
        )


@attr.s
class ActiveStatus:
    #: Whether the user is active now
    active = attr.ib(None)
    #: Datetime when the user was last active
    last_active = attr.ib(None)
    #: Whether the user is playing Messenger game now
    in_game = attr.ib(None)

    @classmethod
    def _from_chatproxy_presence(cls, id_, data):
        return cls(
            active=data["p"] in [2, 3] if "p" in data else None,
            last_active=_util.millis_to_datetime(data.get("lat")),
            in_game=int(id_) in data.get("gamers", {}),
        )

    @classmethod
    def _from_buddylist_overlay(cls, data, in_game=None):
        return cls(
            active=data["a"] in [2, 3] if "a" in data else None,
            last_active=_util.millis_to_datetime(data.get("la")),
            in_game=None,
        )
