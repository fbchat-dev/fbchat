# -*- coding: UTF-8 -*-
from __future__ import unicode_literals


class Poll(object):
    #: ID of the poll
    uid = None
    #: Title of the poll
    title = None
    #: List of :class:`PollOption`, can be fetched with :func:`fbchat.Client.fetchPollOptions`
    options = None
    #: Options count
    options_count = None

    def __init__(self, title, options):
        """Represents a poll"""
        self.title = title
        self.options = options

    def __repr__(self):
        return self.__unicode__()

    def __unicode__(self):
        return "<Poll ({}): {} options={}>".format(
            self.uid, repr(self.title), self.options
        )


class PollOption(object):
    #: ID of the poll option
    uid = None
    #: Text of the poll option
    text = None
    #: Whether vote when creating or client voted
    vote = None
    #: ID of the users who voted for this poll option
    voters = None
    #: Votes count
    votes_count = None

    def __init__(self, text, vote=False):
        """Represents a poll option"""
        self.text = text
        self.vote = vote

    def __repr__(self):
        return self.__unicode__()

    def __unicode__(self):
        return "<PollOption ({}): {} voters={}>".format(
            self.uid, repr(self.text), self.voters
        )
