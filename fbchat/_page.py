import attr
from . import _plan
from ._thread import ThreadType, Thread


@attr.s
class Page(Thread):
    """Represents a Facebook page. Inherits `Thread`."""

    type = ThreadType.PAGE

    #: The page's custom URL
    url = attr.ib(None)
    #: The name of the page's location city
    city = attr.ib(None)
    #: Amount of likes the page has
    likes = attr.ib(None)
    #: Some extra information about the page
    sub_title = attr.ib(None)
    #: The page's category
    category = attr.ib(None)

    @classmethod
    def _from_graphql(cls, data):
        if data.get("profile_picture") is None:
            data["profile_picture"] = {}
        if data.get("city") is None:
            data["city"] = {}
        plan = None
        if data.get("event_reminders") and data["event_reminders"].get("nodes"):
            plan = _plan.Plan._from_graphql(data["event_reminders"]["nodes"][0])

        return cls(
            data["id"],
            url=data.get("url"),
            city=data.get("city").get("name"),
            category=data.get("category_type"),
            photo=data["profile_picture"].get("uri"),
            name=data.get("name"),
            message_count=data.get("messages_count"),
            plan=plan,
        )
