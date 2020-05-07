import pytest
import fbchat

pytestmark = pytest.mark.online


# TODO: Verify return values


def test_wave(any_thread):
    assert any_thread.wave(True)
    assert any_thread.wave(False)


def test_send_text(any_thread):
    assert any_thread.send_text("Test")


def test_send_text_with_mention(any_thread):
    mention = fbchat.Mention(thread_id=any_thread.id, offset=5, length=8)
    assert any_thread.send_text("Test @mention", mentions=[mention])


def test_send_emoji(any_thread):
    assert any_thread.send_emoji("😀", size=fbchat.EmojiSize.LARGE)


def test_send_sticker(any_thread):
    assert any_thread.send_sticker("1889713947839631")


def test_send_location(any_thread):
    any_thread.send_location(51.5287718, -0.2416815)


def test_send_pinned_location(any_thread):
    any_thread.send_pinned_location(39.9390731, 116.117273)


@pytest.mark.skip(reason="need a way to use the uploaded files from test_client.py")
def test_send_files(any_thread):
    pass
