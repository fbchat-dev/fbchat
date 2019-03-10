# -*- coding: UTF-8 -*-

from __future__ import unicode_literals
import json
import re
from .models import *
from ._util import *

# Shameless copy from https://stackoverflow.com/a/8730674
FLAGS = re.VERBOSE | re.MULTILINE | re.DOTALL
WHITESPACE = re.compile(r"[ \t\n\r]*", FLAGS)


class ConcatJSONDecoder(json.JSONDecoder):
    def decode(self, s, _w=WHITESPACE.match):
        s_len = len(s)

        objs = []
        end = 0
        while end != s_len:
            obj, end = self.raw_decode(s, idx=_w(s, end).end())
            end = _w(s, end).end()
            objs.append(obj)
        return objs


# End shameless copy


def graphql_to_attachment(a):
    _type = a["__typename"]
    if _type in ["MessageImage", "MessageAnimatedImage"]:
        return ImageAttachment._from_graphql(a)
    elif _type == "MessageVideo":
        return VideoAttachment._from_graphql(a)
    elif _type == "MessageAudio":
        return AudioAttachment._from_graphql(a)
    elif _type == "MessageFile":
        return FileAttachment._from_graphql(a)
    else:
        return Attachment(uid=a.get("legacy_attachment_id"))


def graphql_to_extensible_attachment(a):
    story = a.get("story_attachment")
    if not story:
        return None

    target = story.get("target")
    if not target:
        return UnsentMessage(uid=a.get("legacy_attachment_id"))

    _type = target["__typename"]
    if _type == "MessageLocation":
        return LocationAttachment._from_graphql(story)
    elif _type == "MessageLiveLocation":
        return LiveLocationAttachment._from_graphql(story)
    elif _type in ["ExternalUrl", "Story"]:
        return ShareAttachment._from_graphql(story)

    return None


def graphql_to_subattachment(a):
    _type = a["target"]["__typename"]
    if _type == "Video":
        media = a["media"]
        return VideoAttachment(
            duration=media.get("playable_duration_in_ms"),
            preview_url=media.get("playable_url"),
            medium_image=media.get("image"),
            uid=a["target"].get("video_id"),
        )


def graphql_to_quick_reply(q, is_response=False):
    data = dict()
    _type = q.get("content_type").lower()
    if q.get("payload"):
        data["payload"] = q["payload"]
    if q.get("data"):
        data["data"] = q["data"]
    if q.get("image_url") and _type is not QuickReplyLocation._type:
        data["image_url"] = q["image_url"]
    data["is_response"] = is_response
    if _type == QuickReplyText._type:
        if q.get("title") is not None:
            data["title"] = q["title"]
        rtn = QuickReplyText(**data)
    elif _type == QuickReplyLocation._type:
        rtn = QuickReplyLocation(**data)
    elif _type == QuickReplyPhoneNumber._type:
        rtn = QuickReplyPhoneNumber(**data)
    elif _type == QuickReplyEmail._type:
        rtn = QuickReplyEmail(**data)
    return rtn


def graphql_to_message(message):
    if message.get("message_sender") is None:
        message["message_sender"] = {}
    if message.get("message") is None:
        message["message"] = {}
    rtn = Message(
        text=message.get("message").get("text"),
        mentions=[
            Mention(
                m.get("entity", {}).get("id"),
                offset=m.get("offset"),
                length=m.get("length"),
            )
            for m in message.get("message").get("ranges", [])
        ],
        emoji_size=EmojiSize._from_tags(message.get("tags_list")),
        sticker=Sticker._from_graphql(message.get("sticker")),
    )
    rtn.uid = str(message.get("message_id"))
    rtn.author = str(message.get("message_sender").get("id"))
    rtn.timestamp = message.get("timestamp_precise")
    rtn.unsent = False
    if message.get("unread") is not None:
        rtn.is_read = not message["unread"]
    rtn.reactions = {
        str(r["user"]["id"]): MessageReaction._extend_if_invalid(r["reaction"])
        for r in message.get("message_reactions")
    }
    if message.get("blob_attachments") is not None:
        rtn.attachments = [
            graphql_to_attachment(attachment)
            for attachment in message["blob_attachments"]
        ]
    if message.get("platform_xmd_encoded"):
        quick_replies = json.loads(message["platform_xmd_encoded"]).get("quick_replies")
        if isinstance(quick_replies, list):
            rtn.quick_replies = [graphql_to_quick_reply(q) for q in quick_replies]
        elif isinstance(quick_replies, dict):
            rtn.quick_replies = [
                graphql_to_quick_reply(quick_replies, is_response=True)
            ]
    if message.get("extensible_attachment") is not None:
        attachment = graphql_to_extensible_attachment(message["extensible_attachment"])
        if isinstance(attachment, UnsentMessage):
            rtn.unsent = True
        elif attachment:
            rtn.attachments.append(attachment)
    return rtn


def graphql_to_thread(thread):
    if thread["thread_type"] == "GROUP":
        return Group._from_graphql(thread)
    elif thread["thread_type"] == "ONE_TO_ONE":
        return User._from_thread_fetch(thread)
    else:
        raise FBchatException(
            "Unknown thread type: {}, with data: {}".format(
                thread.get("thread_type"), thread
            )
        )


def graphql_to_page(page):
    if page.get("profile_picture") is None:
        page["profile_picture"] = {}
    if page.get("city") is None:
        page["city"] = {}
    plan = None
    if page.get("event_reminders") and page["event_reminders"].get("nodes"):
        plan = Plan._from_graphql(page["event_reminders"]["nodes"][0])

    return Page(
        page["id"],
        url=page.get("url"),
        city=page.get("city").get("name"),
        category=page.get("category_type"),
        photo=page["profile_picture"].get("uri"),
        name=page.get("name"),
        message_count=page.get("messages_count"),
        plan=plan,
    )


def graphql_queries_to_json(*queries):
    """
    Queries should be a list of GraphQL objects
    """
    rtn = {}
    for i, query in enumerate(queries):
        rtn["q{}".format(i)] = query.value
    return json.dumps(rtn)


def graphql_response_to_json(content):
    content = strip_to_json(content)  # Usually only needed in some error cases
    try:
        j = json.loads(content, cls=ConcatJSONDecoder)
    except Exception:
        raise FBchatException("Error while parsing JSON: {}".format(repr(content)))

    rtn = [None] * (len(j))
    for x in j:
        if "error_results" in x:
            del rtn[-1]
            continue
        check_json(x)
        [(key, value)] = x.items()
        check_json(value)
        if "response" in value:
            rtn[int(key[1:])] = value["response"]
        else:
            rtn[int(key[1:])] = value["data"]

    log.debug(rtn)

    return rtn


class GraphQL(object):
    def __init__(self, query=None, doc_id=None, params=None):
        if params is None:
            params = {}
        if query is not None:
            self.value = {"priority": 0, "q": query, "query_params": params}
        elif doc_id is not None:
            self.value = {"doc_id": doc_id, "query_params": params}
        else:
            raise FBchatUserError("A query or doc_id must be specified")

    FRAGMENT_USER = """
    QueryFragment User: User {
        id,
        name,
        first_name,
        last_name,
        profile_picture.width(<pic_size>).height(<pic_size>) {
            uri
        },
        is_viewer_friend,
        url,
        gender,
        viewer_affinity
    }
    """

    FRAGMENT_GROUP = """
    QueryFragment Group: MessageThread {
        name,
        thread_key {
            thread_fbid
        },
        image {
            uri
        },
        is_group_thread,
        all_participants {
            nodes {
                messaging_actor {
                    id
                }
            }
        },
        customization_info {
            participant_customizations {
                participant_id,
                nickname
            },
            outgoing_bubble_color,
            emoji
        },
        thread_admins {
            id
        },
        group_approval_queue {
            nodes {
                requester {
                    id
                }
            }
        },
        approval_mode,
        joinable_mode {
            mode,
            link
        },
        event_reminders {
            nodes {
                id,
                lightweight_event_creator {
                    id
                },
                time,
                location_name,
                event_title,
                event_reminder_members {
                    edges {
                        node {
                            id
                        },
                        guest_list_state
                    }
                }
            }
        }
    }
    """

    FRAGMENT_PAGE = """
    QueryFragment Page: Page {
        id,
        name,
        profile_picture.width(32).height(32) {
            uri
        },
        url,
        category_type,
        city {
            name
        }
    }
    """

    SEARCH_USER = (
        """
    Query SearchUser(<search> = '', <limit> = 10) {
        entities_named(<search>) {
            search_results.of_type(user).first(<limit>) as users {
                nodes {
                    @User
                }
            }
        }
    }
    """
        + FRAGMENT_USER
    )

    SEARCH_GROUP = (
        """
    Query SearchGroup(<search> = '', <limit> = 10, <pic_size> = 32) {
        viewer() {
            message_threads.with_thread_name(<search>).last(<limit>) as groups {
                nodes {
                    @Group
                }
            }
        }
    }
    """
        + FRAGMENT_GROUP
    )

    SEARCH_PAGE = (
        """
    Query SearchPage(<search> = '', <limit> = 10) {
        entities_named(<search>) {
            search_results.of_type(page).first(<limit>) as pages {
                nodes {
                    @Page
                }
            }
        }
    }
    """
        + FRAGMENT_PAGE
    )

    SEARCH_THREAD = (
        """
    Query SearchThread(<search> = '', <limit> = 10) {
        entities_named(<search>) {
            search_results.first(<limit>) as threads {
                nodes {
                    __typename,
                    @User,
                    @Group,
                    @Page
                }
            }
        }
    }
    """
        + FRAGMENT_USER
        + FRAGMENT_GROUP
        + FRAGMENT_PAGE
    )
