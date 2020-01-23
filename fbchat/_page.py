import attr
import datetime
from ._core import attrs_default, Image
from . import _session, _plan, _thread


@attrs_default
class Page(_thread.ThreadABC):
    """Represents a Facebook page. Implements `ThreadABC`.

    Example:
        >>> page = fbchat.Page(session=session, id="1234")
    """

    # TODO: Implement pages properly, the implementation is lacking in a lot of places!

    #: The session to use when making requests.
    session = attr.ib(type=_session.Session)
    #: The unique identifier of the page.
    id = attr.ib(converter=str, type=str)

    def _to_send_data(self):
        return {"other_user_fbid": self.id}


@attrs_default
class PageData(Page):
    """Represents data about a Facebook page.

    Inherits `Page`, and implements `ThreadABC`.
    """

    #: The page's picture
    photo = attr.ib(type=Image)
    #: The name of the page
    name = attr.ib(type=str)
    #: When the thread was last active / when the last message was sent
    last_active = attr.ib(None, type=datetime.datetime)
    #: Number of messages in the thread
    message_count = attr.ib(None, type=int)
    #: Set `Plan`
    plan = attr.ib(None, type=_plan.PlanData)
    #: The page's custom URL
    url = attr.ib(None, type=str)
    #: The name of the page's location city
    city = attr.ib(None, type=str)
    #: Amount of likes the page has
    likes = attr.ib(None, type=int)
    #: Some extra information about the page
    sub_title = attr.ib(None, type=str)
    #: The page's category
    category = attr.ib(None, type=str)

    @classmethod
    def _from_graphql(cls, session, data):
        if data.get("profile_picture") is None:
            data["profile_picture"] = {}
        if data.get("city") is None:
            data["city"] = {}
        plan = None
        if data.get("event_reminders") and data["event_reminders"].get("nodes"):
            plan = _plan.PlanData._from_graphql(
                session, data["event_reminders"]["nodes"][0]
            )

        return cls(
            session=session,
            id=data["id"],
            url=data.get("url"),
            city=data.get("city").get("name"),
            category=data.get("category_type"),
            photo=Image._from_uri(data["profile_picture"]),
            name=data["name"],
            message_count=data.get("messages_count"),
            plan=plan,
        )
