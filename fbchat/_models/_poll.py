import attr
from .._common import attrs_default
from .. import _exception, _session
from typing import Iterable, Sequence


@attrs_default
class PollOption:
    """Represents a poll option."""

    #: ID of the poll option
    id = attr.ib(converter=str, type=str)
    #: Text of the poll option
    text = attr.ib(type=str)
    #: Whether vote when creating or client voted
    vote = attr.ib(type=bool)
    #: ID of the users who voted for this poll option
    voters = attr.ib(type=Sequence[str])
    #: Votes count
    votes_count = attr.ib(type=int)

    @classmethod
    def _from_graphql(cls, data):
        if data.get("viewer_has_voted") is None:
            vote = False
        elif isinstance(data["viewer_has_voted"], bool):
            vote = data["viewer_has_voted"]
        else:
            vote = data["viewer_has_voted"] == "true"
        return cls(
            id=int(data["id"]),
            text=data.get("text"),
            vote=vote,
            voters=(
                [m["node"]["id"] for m in data["voters"]["edges"]]
                if isinstance(data.get("voters"), dict)
                else data["voters"]
            ),
            votes_count=(
                data["voters"]["count"]
                if isinstance(data.get("voters"), dict)
                else data["total_count"]
            ),
        )


@attrs_default
class Poll:
    """Represents a poll."""

    #: ID of the poll
    session = attr.ib(type=_session.Session)
    #: ID of the poll
    id = attr.ib(converter=str, type=str)
    #: The poll's question
    question = attr.ib(type=str)
    #: The poll's top few options. The full list can be fetched with `fetch_options`
    options = attr.ib(type=Sequence[PollOption])
    #: Options count
    options_count = attr.ib(type=int)

    @classmethod
    def _from_graphql(cls, session, data):
        return cls(
            session=session,
            id=data["id"],
            question=data["title"] if data.get("title") else data["text"],
            options=[PollOption._from_graphql(m) for m in data["options"]],
            options_count=data["total_count"],
        )

    def fetch_options(self) -> Sequence[PollOption]:
        """Fetch all `PollOption` objects on the poll.

        The result is ordered with options with the most votes first.

        Example:
            >>> options = poll.fetch_options()
            >>> options[0].text
            "An option"
        """
        data = {"question_id": self.id}
        j = self.session._payload_post("/ajax/mercury/get_poll_options", data)
        return [PollOption._from_graphql(m) for m in j]

    def set_votes(self, option_ids: Iterable[str], new_options: Iterable[str] = None):
        """Update the user's poll vote.

        Args:
            option_ids: Option ids to vote for / keep voting for
            new_options: New options to add

        Example:
            >>> options = poll.fetch_options()
            >>> # Add option
            >>> poll.set_votes([o.id for o in options], new_options=["New option"])
            >>> # Remove vote from option
            >>> poll.set_votes([o.id for o in options if o.text != "Option 1"])
        """
        data = {"question_id": self.id}

        for i, option_id in enumerate(option_ids or ()):
            data["selected_options[{}]".format(i)] = option_id

        for i, option_text in enumerate(new_options or ()):
            data["new_options[{}]".format(i)] = option_text

        j = self.session._payload_post(
            "/messaging/group_polling/update_vote/?dpr=1", data
        )
        if j.get("status") != "success":
            raise _exception.ExternalError(
                "Failed updating poll vote: {}".format(j.get("errorTitle")),
                j.get("errorMessage"),
            )
