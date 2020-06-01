import fbchat
from fbchat import PageData


def test_page_from_graphql(session):
    data = {
        "id": "123456",
        "name": "Some school",
        "profile_picture": {"uri": "https://scontent-arn2-1.xx.fbcdn.net/v/..."},
        "url": "https://www.facebook.com/some-school/",
        "category_type": "SCHOOL",
        "city": None,
    }
    assert PageData(
        session=session,
        id="123456",
        photo=fbchat.Image(url="https://scontent-arn2-1.xx.fbcdn.net/v/..."),
        name="Some school",
        url="https://www.facebook.com/some-school/",
        city=None,
        category="SCHOOL",
    ) == PageData._from_graphql(session, data)
