import pytest
import fbchat
import datetime
import os

pytestmark = pytest.mark.online


def test_fetch(client):
    client.fetch_users()


def test_search_for_users(client):
    list(client.search_for_users("test", 10))


def test_search_for_pages(client):
    list(client.search_for_pages("test", 100))


def test_search_for_groups(client):
    list(client.search_for_groups("test", 1000))


def test_search_for_threads(client):
    list(client.search_for_threads("test", 1000))

    with pytest.raises(fbchat.HTTPError, match="rate limited"):
        list(client.search_for_threads("test", 10000))


def test_message_search(client):
    list(client.search_messages("test", 500))


def test_fetch_thread_info(client):
    list(client.fetch_thread_info(["4"]))[0]


def test_fetch_threads(client):
    list(client.fetch_threads(20))
    list(client.fetch_threads(200))


def test_undocumented(client):
    client.fetch_unread()
    client.fetch_unseen()


@pytest.fixture
def open_resource(pytestconfig):
    def get_resource_inner(filename):
        path = os.path.join(pytestconfig.rootdir, "tests", "resources", filename)
        return open(path, "rb")

    return get_resource_inner


def test_upload_and_fetch_image_url(client, open_resource):
    with open_resource("image.png") as f:
        ((id, mimetype),) = client.upload([("image.png", f, "image/png")])
    assert mimetype == "image/png"

    assert client.fetch_image_url(id).startswith("http")


def test_upload_image(client, open_resource):
    with open_resource("image.png") as f:
        _ = client.upload([("image.png", f, "image/png")])


def test_upload_many(client, open_resource):
    with open_resource("image.png") as f_png, open_resource(
        "image.jpg"
    ) as f_jpg, open_resource("image.gif") as f_gif, open_resource(
        "file.json"
    ) as f_json, open_resource(
        "file.txt"
    ) as f_txt, open_resource(
        "audio.mp3"
    ) as f_mp3, open_resource(
        "video.mp4"
    ) as f_mp4:
        _ = client.upload(
            [
                ("image.png", f_png, "image/png"),
                ("image.jpg", f_jpg, "image/jpeg"),
                ("image.gif", f_gif, "image/gif"),
                ("file.json", f_json, "application/json"),
                ("file.txt", f_txt, "text/plain"),
                ("audio.mp3", f_mp3, "audio/mpeg"),
                ("video.mp4", f_mp4, "video/mp4"),
            ]
        )


def test_mark_as_read(client, user, group):
    client.mark_as_read([user, group], datetime.datetime.now())


def test_mark_as_unread(client, user, group):
    client.mark_as_unread([user, group], datetime.datetime.now())


def test_move_threads(client, user, group):
    client.move_threads(fbchat.ThreadLocation.PENDING, [user, group])
    client.move_threads(fbchat.ThreadLocation.INBOX, [user, group])


@pytest.mark.skip(reason="need to have threads to delete")
def test_delete_threads():
    pass


@pytest.mark.skip(reason="need to have messages to delete")
def test_delete_messages():
    pass
