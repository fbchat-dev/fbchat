from typing import List

from .core import Core
from ..models import GroupChannel, User
from ..models.incomplete import GroupChannelData

__all__ = ("GroupControl",)


class GroupControl(Core):
    """Contains methods to control groups"""

    async def add_participants(
        self, group_channel: GroupChannel, users: List[User]
    ) -> None:
        """Add users to a group channel

        Args:
            group: Group to add the users to
            users: Users to add
        """

    async def remove_participants(
        self, group_channel: GroupChannel, users: List[User]
    ) -> None:
        """Remove/kick users from a group

        Args:
            group: Group to remove the user from
            users: Users to remove
        """

    async def add_admins(self, group_channel: GroupChannel, users: List[User]) -> None:
        """Promote users to admins in a group

        Args:
            group: Group to promote the user in
            users: Users to promote
        """

    async def remove_admins(
        self, group_channel: GroupChannel, users: List[User]
    ) -> None:
        """Demote users from being admins

        Args:
            group: Group to demote the users from being admin in
            users: Users to demote
        """

    async def add_group_channel(self, users: List[User]) -> GroupChannelData:
        """Add/create a group

        Args:
            users: Users that the group should be created with

        Return:
            Data about the newly created group
        """

    async def remove_group_channel(self, group_channel: GroupChannel) -> None:
        """Remove/delete a group

        Warning:
            Will delete the group without any further warning. Use with caution!

        Args:
            group: Group to delete
        """
