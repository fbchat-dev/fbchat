import pytest

from fbchat import Message, MessageReaction
from utils import subset

pytestmark = pytest.mark.online


def test_set_reaction(client):
    mid = client.send(Message(text="This message will be reacted to"))
    client.react_to_message(mid, MessageReaction.LOVE)


def test_delete_messages(client):
    text1 = "This message will stay"
    text2 = "This message will be removed"
    mid1 = client.send(Message(text=text1))
    mid2 = client.send(Message(text=text2))
    client.delete_messages(mid2)
    message, = client.fetch_thread_messages(limit=1)
    assert subset(vars(message), uid=mid1, author=client.uid, text=text1)
