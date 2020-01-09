import pytest

from fbchat import Message
from utils import subset

pytestmark = pytest.mark.online


def test_delete_messages(client):
    text1 = "This message will stay"
    text2 = "This message will be removed"
    mid1 = client.send(Message(text=text1))
    mid2 = client.send(Message(text=text2))
    client.delete_messages(mid2)
    (message,) = client.fetch_thread_messages(limit=1)
    assert subset(vars(message), id=mid1, author=client.id, text=text1)
