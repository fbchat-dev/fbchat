# -*- coding: UTF-8 -*-

from __future__ import unicode_literals

from .listen import ListenerClient


__all__ = ("GroupControllerClient",)


class GroupControllerClient(ListenerClient):
    """Enables the client to control groups and listen to those events"""

    def add_users(self, group, users):
        """Add users to a group

        Args:
            group (`Group`): Group to add the users to
            users (list): `User`\s, denoting the users to add
        """

    def on_users_added(self, group, actor, users):
        """Called when users are added to a group

        Args:
            group (`Group`): Group that the users were added to
            actor (`User`): Person that added the users
            users (list): `User`\s, denoting the added users
        """

    def add_user(self, group, user):
        """Add a user to a group. Shortcut of `add_users`

        Args:
            group (`Group`): Group to add the user to
            user (`User`): Person to add
        """

    def on_user_added(self, group, actor, user):
        """Called when a user is added. Shortcut of `on_users_added`

        Args:
            group (`Group`): Group that the user were added to
            actor (`User`): Person that added the user
            user (`User`): The added user
        """

    def remove_user(self, group, user):
        """Remove/kick a user from a group

        Args:
            group (`Group`): Group to remove the user from
            user (`User`): Person to remove
        """

    def on_user_removed(self, group, actor, user):
        """Called when a user is removed/kicked

        Args:
            group (`Group`): Group that the user were removed from
            actor (`User`): Person that removed the user
            user (`User`): The removed user
        """

    def add_admin(self, group, user):
        """Promote a user to admin in a group

        Args:
            group (`Group`): Group to promote the user in
            user (`User`): Person to promote
        """

    def on_admin_added(self, group, actor, user):
        """Called when a user is promoted to admin

        Args:
            group (`Group`): Group that the user were promoted in
            actor (`User`): Person that promoted the user
            user (`User`): The promoted user
        """

    def remove_admin(self, group, user):
        """Demote a user from being an admin

        Args:
            group (`Group`): Group to demote the user from being an admin in
            user (`User`): User to demote
        """

    def on_admin_removed(self, group, actor, user):
        """Called when a user is demoted as an admin

        Args:
            group (`Group`): Group that the user were demoted in
            actor (`User`): Person that demoted the user
            user (`User`)): The demoted user
        """

    def add_group(self, users):
        """Add/create a group

        Args:
            users (list): `User` objects, denoting the users that the group
                should be created with

        Return:
            `Group`, denoting the newly created group
        """

    def on_group_added(self, group, actor):
        """Called when a new group is added/created

        Args:
            group (`Group`): The newly created group
            actor (`User`): Person that created the group
        """

    def remove_group(self, group):
        """Remove/delete a group

        Warning:
            Will delete the group without any further warning. Use with
            caution!

        Args:
            group (`Group`): Group to delete
        """

    def on_group_removed(self, group, actor):
        """Called when a group is removed/deleted

        Args:
            group (`Group`): The deleted group
            actor (`User`): Person that deleted the group
        """

    def leave_group(self, group):
        """Leave a group. Shortcut of `remove_user`

        Args:
            group (`Group`): Group to leave
        """
