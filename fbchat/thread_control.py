# -*- coding: UTF-8 -*-

from __future__ import unicode_literals
from .listener import Listener


class ThreadControl(Listener):
    """Enables the client to control and listen on threads"""

    def add_users(self, thread, users):
        """Add users to a group

        Args:
            thread (`Thread`): Group to add the users to
            users (list): `Thread` objects, denoting the users to add
        """

    def on_users_added(self, thread, actor, subjects):
        """Called when users are added to a thread

        Args:
            thread (`Thread`): Group that the users were added to
            actor (`Thread`): Person that added the users
            subjects (list): `Thread` objects, denoting the added users
        """

    def add_user(self, thread, user):
        """Add a user to a group. Shortcut of `add_users`

        Args:
            thread (`Thread`): Group to add the user to
            user (`Thread`): User to add
        """

    def on_user_added(self, thread, actor, subject):
        """Called when a user is added. Shortcut of `on_users_added`

        Args:
            thread (`Thread`): Group that the user were added to
            actor (`Thread`): Person that added the user
            subject (`Thread`)): The added user
        """

    def remove_user(self, thread, user):
        """Remove/kick a user from a group

        Args:
            thread (`Thread`): Group to remove the user from
            user (`Thread`): User to remove
        """

    def on_user_removed(self, thread, actor, subject):
        """Called when a user is removed/kicked

        Args:
            thread (`Thread`): Group that the user were removed from
            actor (`Thread`): Person that removed the user
            subject (`Thread`)): The removed user
        """


    def add_admin(self, thread, user):
        """Promote a user to admin in a group

        Args:
            thread (`Thread`): Group to promote the user in
            user (`Thread`): User to promote
        """

    def on_admin_added(self, thread, actor, subject):
        """Called when a user is promoted to admin

        Args:
            thread (`Thread`): Group that the user were promoted in
            actor (`Thread`): Person that promoted the user
            subject (`Thread`)): The promoted user
        """

    def remove_admin(self, thread, user):
        """Demote a user from being an admin

        Args:
            thread (`Thread`): Group to demote the user from being an admin in
            user (`Thread`): User to demote
        """

    def on_admin_removed(self, thread, actor, subject):
        """Called when a user is demoted as an admin

        Args:
            thread (`Thread`): Group that the user were demoted in
            actor (`Thread`): Person that demoted the user
            subject (`Thread`)): The demoted user
        """


    def add_thread(self, users):
        """Add/create a group-thread

        Args:
            users (list): `Thread` objects, denoting the users that the group
                should be created with

        Return:
            `Thread`, denoting the newly created group
        """

    def on_thread_added(self, thread, actor):
        """Called when a new thread is added/created

        Args:
            thread (`Thread`): The newly created thread
            actor (`Thread`): Person that created the thread
        """

    def remove_thread(self, thread):
        """Remove/delete a thread

        Warning:
            Will delete the thread without any further warning. Use with
            caution!

        Args:
            thread (`Thread`): Thread to delete
        """

    def on_thread_removed(self, thread, actor):
        """Called when a thread is removed/deleted

        Args:
            thread (`Thread`): The deleted thread
            actor (`Thread`): Person that deleted the thread
        """


    def leave_thread(self, thread):
        """Leave a group. Shortcut of `remove_user`

        Args:
            thread (`Thread`): Group to leave
        """
