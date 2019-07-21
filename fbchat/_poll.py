# -*- coding: UTF-8 -*-
from __future__ import unicode_literals

import attr


@attr.s(cmp=False)
class Poll(object):
    """Represents a poll."""

    #: Title of the poll
    title = attr.ib()
    #: List of :class:`PollOption`, can be fetched with :func:`fbchat.Client.fetchPollOptions`
    options = attr.ib()
    #: Options count
    options_count = attr.ib(None)
    #: ID of the poll
    uid = attr.ib(None)

    @classmethod
    def _from_graphql(cls, data):
        return cls(
            uid=int(data["id"]),
            title=data.get("title") if data.get("title") else data.get("text"),
            options=[PollOption._from_graphql(m) for m in data.get("options")],
            options_count=data.get("total_count"),
        )


@attr.s(cmp=False)
class PollOption(object):
    """Represents a poll option."""

    #: Text of the poll option
    text = attr.ib()
    #: Whether vote when creating or client voted
    vote = attr.ib(False)
    #: ID of the users who voted for this poll option
    voters = attr.ib(None)
    #: Votes count
    votes_count = attr.ib(None)
    #: ID of the poll option
    uid = attr.ib(None)

    @classmethod
    def _from_graphql(cls, data):
        if data.get("viewer_has_voted") is None:
            vote = None
        elif isinstance(data["viewer_has_voted"], bool):
            vote = data["viewer_has_voted"]
        else:
            vote = data["viewer_has_voted"] == "true"
        return cls(
            uid=int(data["id"]),
            text=data.get("text"),
            vote=vote,
            voters=(
                [m.get("node").get("id") for m in data.get("voters").get("edges")]
                if isinstance(data.get("voters"), dict)
                else data.get("voters")
            ),
            votes_count=(
                data.get("voters").get("count")
                if isinstance(data.get("voters"), dict)
                else data.get("total_count")
            ),
        )
