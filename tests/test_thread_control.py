# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from os import environ
from pytest import mark, fixture


@fixture
def users(user):
    return [user]


def test_add_users(mocker, listener, client, users, group):
    with listener('on_users_added'), listener('on_user_added') as on_users_added, on_user_added:
        client.add_users(group, users)
    on_users_added.assert_called_once_with(group, client, users)
    on_user_added.call_count == len(users)
    on_user_added.call_args == [mocker.call(group, client, u) for u in users]


def test_add_user(mocker, client, user, group):
    add_users = mocker.patch.object(client, 'add_users')
    client.add_user(group, user)
    add_users.assert_called_once_with(thread, client)


def test_remove_user(listener, client, user, group):
    with listener('on_user_removed') as on_user_removed:
        client.remove_user(group, user)
    on_user_removed.assert_called_once_with(group, client, user)


def test_add_admin(listener, client, user, group):
    with listener('on_admin_added') as on_admin_added:
        client.add_admin(group, user)
    on_admin_added.assert_called_once_with(group, client, user)


def test_remove_admin(listener, client, user, group):
    with listener('on_admin_removed') as on_admin_removed:
        client.remove_admin(group, user)
    on_admin_removed.assert_called_once_with(group, client, user)


def test_add_remove_thread(listener, client, users):
    with listener('on_thread_added') as on_thread_added:
        group = client.add_thread(users)
    on_thread_added.assert_called_once_with(group, client)

    with listener('on_thread_removed') as on_thread_removed:
        client.remove_thread(group)
    on_thread_removed.assert_called_once_with(group, client)


def test_leave_thread(mocker, client, group):
    remove_user = mocker.patch.object(client, 'remove_user')
    client.leave_thread(group)
    remove_user.assert_called_once_with(group)
