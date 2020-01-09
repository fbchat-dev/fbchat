import attr
from ._core import log, attrs_default, Enum, Image
from . import _util, _session, _plan, _thread


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
class User(_thread.ThreadABC):
    """Represents a Facebook user. Implements `ThreadABC`."""

    #: The session to use when making requests.
    session = attr.ib(type=_session.Session)
    #: The user's unique identifier.
    id = attr.ib(converter=str)

    def _to_send_data(self):
        return {"other_user_fbid": self.id}

    def confirm_friend_request(self):
        """Confirm a friend request, adding the user to your friend list."""
        data = {"to_friend": self.id, "action": "confirm"}
        j = self.session._payload_post("/ajax/add_friend/action.php?dpr=1", data)

    def remove_friend(self):
        """Remove the user from the client's friend list."""
        data = {"uid": self.id}
        j = self.session._payload_post("/ajax/profile/removefriendconfirm.php", data)

    def block(self):
        """Block messages from the user."""
        data = {"fbid": self.id}
        j = self.session._payload_post("/messaging/block_messages/?dpr=1", data)

    def unblock(self):
        """Unblock a previously blocked user."""
        data = {"fbid": self.id}
        j = self.session._payload_post("/messaging/unblock_messages/?dpr=1", data)


@attrs_default
class UserData(User):
    """Represents data about a Facebook user.

    Inherits `User`, and implements `ThreadABC`.
    """

    #: The user's picture
    photo = attr.ib()
    #: The name of the user
    name = attr.ib()
    #: Whether the user and the client are friends
    is_friend = attr.ib()
    #: The users first name
    first_name = attr.ib()
    #: The users last name
    last_name = attr.ib(None)
    #: Datetime when the thread was last active / when the last message was sent
    last_active = attr.ib(None)
    #: Number of messages in the thread
    message_count = attr.ib(None)
    #: Set `Plan`
    plan = attr.ib(None)
    #: The profile URL. ``None`` for Messenger-only users
    url = attr.ib(None)
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
            plan = _plan.PlanData._from_graphql(
                session, data["event_reminders"]["nodes"][0]
            )

        return cls(
            session=session,
            id=data["id"],
            url=data["url"],
            first_name=data["first_name"],
            last_name=data.get("last_name"),
            is_friend=data["is_viewer_friend"],
            gender=GENDERS.get(data["gender"]),
            affinity=data.get("viewer_affinity"),
            nickname=c_info.get("nickname"),
            color=c_info.get("color"),
            emoji=c_info.get("emoji"),
            own_nickname=c_info.get("own_nickname"),
            photo=Image._from_uri(data["profile_picture"]),
            name=data["name"],
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
        if user["__typename"] != "User":
            # TODO: Add Page._from_thread_fetch, and parse it there
            log.warning("Tried to parse %s as a user.", user["__typename"])
            return None

        last_active = None
        if "last_message" in data:
            last_active = _util.millis_to_datetime(
                int(data["last_message"]["nodes"][0]["timestamp_precise"])
            )

        first_name = user["short_name"]
        last_name = user.get("name").split(first_name, 1).pop().strip()

        plan = None
        if data.get("event_reminders") and data["event_reminders"].get("nodes"):
            plan = _plan.PlanData._from_graphql(
                session, data["event_reminders"]["nodes"][0]
            )

        return cls(
            session=session,
            id=user["id"],
            url=user["url"],
            name=user["name"],
            first_name=first_name,
            last_name=last_name,
            is_friend=user["is_viewer_friend"],
            gender=GENDERS.get(user["gender"]),
            nickname=c_info.get("nickname"),
            color=c_info.get("color"),
            emoji=c_info.get("emoji"),
            own_nickname=c_info.get("own_nickname"),
            photo=Image._from_uri(user["big_image_src"]),
            message_count=data["messages_count"],
            last_active=last_active,
            plan=plan,
        )

    @classmethod
    def _from_all_fetch(cls, session, data):
        return cls(
            session=session,
            id=data["id"],
            first_name=data["firstName"],
            url=data["uri"],
            photo=Image(url=data["thumbSrc"]),
            name=data["name"],
            is_friend=data["is_friend"],
            gender=GENDERS.get(data["gender"]),
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
