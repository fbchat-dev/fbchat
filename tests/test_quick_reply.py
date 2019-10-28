from fbchat._quick_reply import (
    QuickReplyText,
    QuickReplyLocation,
    QuickReplyPhoneNumber,
    QuickReplyEmail,
    graphql_to_quick_reply,
)


def test_parse_minimal():
    data = {
        "content_type": "text",
        "payload": None,
        "external_payload": None,
        "data": None,
        "title": "A",
        "image_url": None,
    }
    assert QuickReplyText(title="A") == graphql_to_quick_reply(data)
    data = {"content_type": "location"}
    assert QuickReplyLocation() == graphql_to_quick_reply(data)
    data = {"content_type": "user_phone_number"}
    assert QuickReplyPhoneNumber() == graphql_to_quick_reply(data)
    data = {"content_type": "user_email"}
    assert QuickReplyEmail() == graphql_to_quick_reply(data)


def test_parse_text_full():
    data = {
        "content_type": "text",
        "title": "A",
        "payload": "Some payload",
        "image_url": "https://example.com/image.jpg",
        "data": None,
    }
    assert QuickReplyText(
        payload="Some payload",
        data=None,
        is_response=False,
        title="A",
        image_url="https://example.com/image.jpg",
    ) == graphql_to_quick_reply(data)


def test_parse_with_is_response():
    data = {"content_type": "text"}
    assert QuickReplyText(is_response=True) == graphql_to_quick_reply(
        data, is_response=True
    )
