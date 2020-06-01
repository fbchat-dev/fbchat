import pytest
import fbchat
from fbchat import EmojiSize, Mention, Message, MessageData
from fbchat._models._message import graphql_to_extensible_attachment


@pytest.mark.parametrize(
    "tags,size",
    [
        (None, None),
        (["hot_emoji_size:unknown"], None),
        (["bunch", "of:different", "tags:large", "hot_emoji_size:s"], EmojiSize.SMALL),
        (["hot_emoji_size:s"], EmojiSize.SMALL),
        (["hot_emoji_size:m"], EmojiSize.MEDIUM),
        (["hot_emoji_size:l"], EmojiSize.LARGE),
        (["hot_emoji_size:small"], EmojiSize.SMALL),
        (["hot_emoji_size:medium"], EmojiSize.MEDIUM),
        (["hot_emoji_size:large"], EmojiSize.LARGE),
    ],
)
def test_emojisize_from_tags(tags, size):
    assert size is EmojiSize._from_tags(tags)


def test_graphql_to_extensible_attachment_empty():
    assert None is graphql_to_extensible_attachment({})


@pytest.mark.parametrize(
    "obj,type_",
    [
        # UnsentMessage testing is done in test_attachment.py
        (fbchat.LocationAttachment, "MessageLocation"),
        (fbchat.LiveLocationAttachment, "MessageLiveLocation"),
        (fbchat.ShareAttachment, "ExternalUrl"),
        (fbchat.ShareAttachment, "Story"),
    ],
)
def test_graphql_to_extensible_attachment_dispatch(monkeypatch, obj, type_):
    monkeypatch.setattr(obj, "_from_graphql", lambda data: True)
    data = {"story_attachment": {"target": {"__typename": type_}}}
    assert graphql_to_extensible_attachment(data)


def test_mention_from_range():
    data = {"length": 17, "offset": 0, "entity": {"__typename": "User", "id": "1234"}}
    assert Mention(thread_id="1234", offset=0, length=17) == Mention._from_range(data)
    data = {
        "length": 2,
        "offset": 10,
        "entity": {"__typename": "MessengerViewer1To1Thread"},
    }
    assert Mention(thread_id=None, offset=10, length=2) == Mention._from_range(data)
    data = {
        "length": 5,
        "offset": 21,
        "entity": {"__typename": "MessengerViewerGroupThread"},
    }
    assert Mention(thread_id=None, offset=21, length=5) == Mention._from_range(data)


def test_mention_to_send_data():
    assert {
        "profile_xmd[0][id]": "1234",
        "profile_xmd[0][length]": 7,
        "profile_xmd[0][offset]": 4,
        "profile_xmd[0][type]": "p",
    } == Mention(thread_id="1234", offset=4, length=7)._to_send_data(0)
    assert {
        "profile_xmd[1][id]": "4321",
        "profile_xmd[1][length]": 7,
        "profile_xmd[1][offset]": 24,
        "profile_xmd[1][type]": "p",
    } == Mention(thread_id="4321", offset=24, length=7)._to_send_data(1)


def test_message_format_mentions():
    expected = (
        "Hey 'Peter'! My name is Michael",
        [
            Mention(thread_id="1234", offset=4, length=7),
            Mention(thread_id="4321", offset=24, length=7),
        ],
    )
    assert expected == Message.format_mentions(
        "Hey {!r}! My name is {}", ("1234", "Peter"), ("4321", "Michael")
    )
    assert expected == Message.format_mentions(
        "Hey {p!r}! My name is {}", ("4321", "Michael"), p=("1234", "Peter")
    )


def test_message_get_forwarded_from_tags():
    assert not MessageData._get_forwarded_from_tags(None)
    assert not MessageData._get_forwarded_from_tags(["hot_emoji_size:unknown"])
    assert MessageData._get_forwarded_from_tags(
        ["attachment:photo", "inbox", "sent", "source:chat:forward", "tq"]
    )


@pytest.mark.skip(reason="need to be added")
def test_message_to_send_data_quick_replies():
    raise NotImplementedError


@pytest.mark.skip(reason="need to gather test data")
def test_message_from_graphql():
    pass


@pytest.mark.skip(reason="need to gather test data")
def test_message_from_reply():
    pass


@pytest.mark.skip(reason="need to gather test data")
def test_message_from_pull():
    pass
