import pytest
from fbchat import ThreadType

pytestmark = pytest.mark.online


def test_search_for(client1):
    users = client1.search_for_users("Mark Zuckerberg")
    assert len(users) > 0

    u = users[0]

    assert u.uid == "4"
    assert u.type == ThreadType.USER
    assert u.photo[:4] == "http"
    assert u.url[:4] == "http"
    assert u.name == "Mark Zuckerberg"
