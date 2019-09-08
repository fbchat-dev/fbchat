import pytest

from os import path
from fbchat import FBchatFacebookError, Message, Mention
from utils import subset, STICKER_LIST, EMOJI_LIST, TEXT_LIST

pytestmark = pytest.mark.online


@pytest.mark.parametrize("text", TEXT_LIST)
def test_send_text(client, catch_event, compare, text):
    with catch_event("on_message") as x:
        mid = client.send(Message(text=text))

    assert compare(x, mid=mid, message=text)
    assert subset(vars(x.res["message_object"]), uid=mid, author=client.uid, text=text)


@pytest.mark.parametrize("emoji, emoji_size", EMOJI_LIST)
def test_send_emoji(client, catch_event, compare, emoji, emoji_size):
    with catch_event("on_message") as x:
        mid = client.send_emoji(emoji, emoji_size)

    assert compare(x, mid=mid, message=emoji)
    assert subset(
        vars(x.res["message_object"]),
        uid=mid,
        author=client.uid,
        text=emoji,
        emoji_size=emoji_size,
    )


def test_send_mentions(client, catch_event, compare, message_with_mentions):
    with catch_event("on_message") as x:
        mid = client.send(message_with_mentions)

    assert compare(x, mid=mid, message=message_with_mentions.text)
    assert subset(
        vars(x.res["message_object"]),
        uid=mid,
        author=client.uid,
        text=message_with_mentions.text,
    )
    # The mentions are not ordered by offset
    for m in x.res["message_object"].mentions:
        assert vars(m) in [vars(x) for x in message_with_mentions.mentions]


@pytest.mark.parametrize("sticker", STICKER_LIST)
def test_send_sticker(client, catch_event, compare, sticker):
    with catch_event("on_message") as x:
        mid = client.send(Message(sticker=sticker))

    assert compare(x, mid=mid)
    assert subset(vars(x.res["message_object"]), uid=mid, author=client.uid)
    assert subset(vars(x.res["message_object"].sticker), uid=sticker.uid)


# Kept for backwards compatibility
@pytest.mark.parametrize(
    "method_name, url",
    [
        (
            "sendRemoteImage",
            "https://github.com/carpedm20/fbchat/raw/master/tests/image.png",
        ),
        ("sendLocalImage", path.join(path.dirname(__file__), "resources", "image.png")),
    ],
)
def test_send_images(client, catch_event, compare, method_name, url):
    text = "An image sent with {}".format(method_name)
    with catch_event("on_message") as x:
        mid = getattr(client, method_name)(url, Message(text))

    assert compare(x, mid=mid, message=text)
    assert subset(vars(x.res["message_object"]), uid=mid, author=client.uid, text=text)
    assert x.res["message_object"].attachments[0]


def test_send_local_files(client, catch_event, compare):
    files = [
        "image.png",
        "image.jpg",
        "image.gif",
        "file.json",
        "file.txt",
        "audio.mp3",
        "video.mp4",
    ]
    text = "Files sent locally"
    with catch_event("on_message") as x:
        mid = client.send_local_files(
            [path.join(path.dirname(__file__), "resources", f) for f in files],
            message=Message(text),
        )

    assert compare(x, mid=mid, message=text)
    assert subset(vars(x.res["message_object"]), uid=mid, author=client.uid, text=text)
    assert len(x.res["message_object"].attachments) == len(files)


# To be changed when merged into master
def test_send_remote_files(client, catch_event, compare):
    files = ["image.png", "data.json"]
    text = "Files sent from remote"
    with catch_event("on_message") as x:
        mid = client.send_remote_files(
            [
                "https://github.com/carpedm20/fbchat/raw/master/tests/{}".format(f)
                for f in files
            ],
            message=Message(text),
        )

    assert compare(x, mid=mid, message=text)
    assert subset(vars(x.res["message_object"]), uid=mid, author=client.uid, text=text)
    assert len(x.res["message_object"].attachments) == len(files)


@pytest.mark.parametrize("wave_first", [True, False])
def test_wave(client, wave_first):
    client.wave(wave_first)
