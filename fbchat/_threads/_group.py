import attr
import datetime
from ._abc import ThreadABC
from . import _user
from .._common import attrs_default
from .. import _util, _session, _graphql, _models

from typing import Sequence, Iterable, Set, Mapping, Optional


@attrs_default
class Group(ThreadABC):
    """Represents a Facebook group. Implements `ThreadABC`.

    Example:
        >>> group = fbchat.Group(session=session, id="1234")
    """

    #: The session to use when making requests.
    session = attr.ib(type=_session.Session)
    #: The group's unique identifier.
    id = attr.ib(converter=str, type=str)

    def _to_send_data(self):
        return {"thread_fbid": self.id}

    def _copy(self) -> "Group":
        return Group(session=self.session, id=self.id)

    def add_participants(self, user_ids: Iterable[str]):
        """Add users to the group.

        Args:
            user_ids: One or more user IDs to add

        Example:
            >>> group.add_participants(["1234", "2345"])
        """
        data = self._to_send_data()

        data["action_type"] = "ma-type:log-message"
        data["log_message_type"] = "log:subscribe"

        for i, user_id in enumerate(user_ids):
            if user_id == self.session.user.id:
                raise ValueError(
                    "Error when adding users: Cannot add self to group thread"
                )
            else:
                data[
                    "log_message_data[added_participants][{}]".format(i)
                ] = "fbid:{}".format(user_id)

        return self.session._do_send_request(data)

    def remove_participant(self, user_id: str):
        """Remove user from the group.

        Args:
            user_id: User ID to remove

        Example:
            >>> group.remove_participant("1234")
        """
        data = {"uid": user_id, "tid": self.id}
        j = self.session._payload_post("/chat/remove_participants/", data)

    def _admin_status(self, user_ids: Iterable[str], status: bool):
        data = {"add": status, "thread_fbid": self.id}

        for i, user_id in enumerate(user_ids):
            data["admin_ids[{}]".format(i)] = str(user_id)

        j = self.session._payload_post("/messaging/save_admins/?dpr=1", data)

    def add_admins(self, user_ids: Iterable[str]):
        """Set specified users as group admins.

        Args:
            user_ids: One or more user IDs to set admin

        Example:
            >>> group.add_admins(["1234", "2345"])
        """
        self._admin_status(user_ids, True)

    def remove_admins(self, user_ids: Iterable[str]):
        """Remove admin status from specified users.

        Args:
            user_ids: One or more user IDs to remove admin

        Example:
            >>> group.remove_admins(["1234", "2345"])
        """
        self._admin_status(user_ids, False)

    def set_title(self, title: str):
        """Change title of the group.

        Args:
            title: New title

        Example:
            >>> group.set_title("Abc")
        """
        data = {"thread_name": title, "thread_id": self.id}
        j = self.session._payload_post("/messaging/set_thread_name/?dpr=1", data)

    def set_image(self, image_id: str):
        """Change the group image from an image id.

        Args:
            image_id: ID of uploaded image

        Example:
            Upload an image, and use it as the group image.

            >>> with open("image.png", "rb") as f:
            ...     (file,) = client.upload([("image.png", f, "image/png")])
            ...
            >>> group.set_image(file[0])
        """
        data = {"thread_image_id": image_id, "thread_id": self.id}
        j = self.session._payload_post("/messaging/set_thread_image/?dpr=1", data)

    def set_approval_mode(self, require_admin_approval: bool):
        """Change the group's approval mode.

        Args:
            require_admin_approval: True or False

        Example:
            >>> group.set_approval_mode(False)
        """
        data = {"set_mode": int(require_admin_approval), "thread_fbid": self.id}
        j = self.session._payload_post("/messaging/set_approval_mode/?dpr=1", data)

    def _users_approval(self, user_ids: Iterable[str], approve: bool):
        data = {
            "client_mutation_id": "0",
            "actor_id": self.session.user.id,
            "thread_fbid": self.id,
            "user_ids": list(user_ids),
            "response": "ACCEPT" if approve else "DENY",
            "surface": "ADMIN_MODEL_APPROVAL_CENTER",
        }
        (j,) = self.session._graphql_requests(
            _graphql.from_doc_id("1574519202665847", {"data": data})
        )

    def accept_users(self, user_ids: Iterable[str]):
        """Accept users to the group from the group's approval.

        Args:
            user_ids: One or more user IDs to accept

        Example:
            >>> group.accept_users(["1234", "2345"])
        """
        self._users_approval(user_ids, True)

    def deny_users(self, user_ids: Iterable[str]):
        """Deny users from joining the group.

        Args:
            user_ids: One or more user IDs to deny

        Example:
            >>> group.deny_users(["1234", "2345"])
        """
        self._users_approval(user_ids, False)


@attrs_default
class GroupData(Group):
    """Represents data about a Facebook group.

    Inherits `Group`, and implements `ThreadABC`.
    """

    #: The group's picture
    photo = attr.ib(None, type=Optional[_models.Image])
    #: The name of the group
    name = attr.ib(None, type=Optional[str])
    #: When the group was last active / when the last message was sent
    last_active = attr.ib(None, type=Optional[datetime.datetime])
    #: Number of messages in the group
    message_count = attr.ib(None, type=Optional[int])
    #: Set `Plan`
    plan = attr.ib(None, type=Optional[_models.PlanData])
    #: The group thread's participant user ids
    participants = attr.ib(factory=set, type=Set[str])
    #: A dictionary, containing user nicknames mapped to their IDs
    nicknames = attr.ib(factory=dict, type=Mapping[str, str])
    #: The groups's message color
    color = attr.ib(None, type=Optional[str])
    #: The groups's default emoji
    emoji = attr.ib(None, type=Optional[str])
    # User ids of thread admins
    admins = attr.ib(factory=set, type=Set[str])
    # True if users need approval to join
    approval_mode = attr.ib(None, type=Optional[bool])
    # Set containing user IDs requesting to join
    approval_requests = attr.ib(factory=set, type=Set[str])
    # Link for joining group
    join_link = attr.ib(None, type=Optional[str])

    @classmethod
    def _from_graphql(cls, session, data):
        if data.get("image") is None:
            data["image"] = {}
        c_info = cls._parse_customization_info(data)
        last_active = None
        if "last_message" in data:
            last_active = _util.millis_to_datetime(
                int(data["last_message"]["nodes"][0]["timestamp_precise"])
            )
        plan = None
        if data.get("event_reminders") and data["event_reminders"].get("nodes"):
            plan = _models.PlanData._from_graphql(
                session, data["event_reminders"]["nodes"][0]
            )

        return cls(
            session=session,
            id=data["thread_key"]["thread_fbid"],
            participants=list(
                cls._parse_participants(session, data["all_participants"])
            ),
            nicknames=c_info.get("nicknames"),
            color=c_info["color"],
            emoji=c_info["emoji"],
            admins=set([node.get("id") for node in data.get("thread_admins")]),
            approval_mode=bool(data.get("approval_mode"))
            if data.get("approval_mode") is not None
            else None,
            approval_requests=set(
                node["requester"]["id"]
                for node in data["group_approval_queue"]["nodes"]
            )
            if data.get("group_approval_queue")
            else None,
            join_link=data["joinable_mode"].get("link"),
            photo=_models.Image._from_uri_or_none(data["image"]),
            name=data.get("name"),
            message_count=data.get("messages_count"),
            last_active=last_active,
            plan=plan,
        )


@attrs_default
class NewGroup(ThreadABC):
    """Helper class to create new groups.

    TODO: Complete this!

    Construct this class with the desired users, and call a method like `wave`, to...
    """

    #: The session to use when making requests.
    session = attr.ib(type=_session.Session)
    #: The users that should be added to the group.
    _users = attr.ib(type=Sequence["_user.User"])

    @property
    def id(self):
        raise NotImplementedError(
            "The method you called is not supported on NewGroup objects."
            " Please use the supported methods to create the group, before attempting"
            " to call the method."
        )

    def _to_send_data(self) -> dict:
        return {
            "specific_to_list[{}]".format(i): "fbid:{}".format(user.id)
            for i, user in enumerate(self._users)
        }
