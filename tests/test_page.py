from fbchat._page import Page


def test_page_from_graphql():
    data = {
        "id": "123456",
        "name": "Some school",
        "profile_picture": {"uri": "https://scontent-arn2-1.xx.fbcdn.net/v/..."},
        "url": "https://www.facebook.com/some-school/",
        "category_type": "SCHOOL",
        "city": None,
    }
    assert Page(
        uid="123456",
        photo="https://scontent-arn2-1.xx.fbcdn.net/v/...",
        name="Some school",
        url="https://www.facebook.com/some-school/",
        city=None,
        category="SCHOOL",
    ) == Page._from_graphql(data)
