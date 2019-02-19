# -*- coding: UTF-8 -*-

from __future__ import unicode_literals
import json
import re
from .models import *
from .utils import *

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


def graphql_color_to_enum(color):
    if color is None:
        return None
    if not color:
        return ThreadColor.MESSENGER_BLUE
    color = color[2:]  # Strip the alpha value
    color_value = "#{}".format(color.lower())
    return enum_extend_if_invalid(ThreadColor, color_value)


def get_customization_info(thread):
    if thread is None or thread.get("customization_info") is None:
        return {}
    info = thread["customization_info"]

    rtn = {
        "emoji": info.get("emoji"),
        "color": graphql_color_to_enum(info.get("outgoing_bubble_color")),
    }
    if (
        thread.get("thread_type") == "GROUP"
        or thread.get("is_group_thread")
        or thread.get("thread_key", {}).get("thread_fbid")
    ):
        rtn["nicknames"] = {}
        for k in info.get("participant_customizations", []):
            rtn["nicknames"][k["participant_id"]] = k.get("nickname")
    elif info.get("participant_customizations"):
        uid = thread.get("thread_key", {}).get("other_user_id") or thread.get("id")
        pc = info["participant_customizations"]
        if len(pc) > 0:
            if pc[0].get("participant_id") == uid:
                rtn["nickname"] = pc[0].get("nickname")
            else:
                rtn["own_nickname"] = pc[0].get("nickname")
        if len(pc) > 1:
            if pc[1].get("participant_id") == uid:
                rtn["nickname"] = pc[1].get("nickname")
            else:
                rtn["own_nickname"] = pc[1].get("nickname")
    return rtn


def graphql_to_sticker(s):
    if not s:
        return None
    sticker = Sticker(uid=s["id"])
    if s.get("pack"):
        sticker.pack = s["pack"].get("id")
    if s.get("sprite_image"):
        sticker.is_animated = True
        sticker.medium_sprite_image = s["sprite_image"].get("uri")
        sticker.large_sprite_image = s["sprite_image_2x"].get("uri")
        sticker.frames_per_row = s.get("frames_per_row")
        sticker.frames_per_col = s.get("frames_per_column")
        sticker.frame_rate = s.get("frame_rate")
    sticker.url = s.get("url")
    sticker.width = s.get("width")
    sticker.height = s.get("height")
    if s.get("label"):
        sticker.label = s["label"]
    return sticker


def graphql_to_attachment(a):
    _type = a["__typename"]
    if _type in ["MessageImage", "MessageAnimatedImage"]:
        return ImageAttachment(
            original_extension=a.get("original_extension")
            or (a["filename"].split("-")[0] if a.get("filename") else None),
            width=a.get("original_dimensions", {}).get("width"),
            height=a.get("original_dimensions", {}).get("height"),
            is_animated=_type == "MessageAnimatedImage",
            thumbnail_url=a.get("thumbnail", {}).get("uri"),
            preview=a.get("preview") or a.get("preview_image"),
            large_preview=a.get("large_preview"),
            animated_preview=a.get("animated_image"),
            uid=a.get("legacy_attachment_id"),
        )
    elif _type == "MessageVideo":
        return VideoAttachment(
            width=a.get("original_dimensions", {}).get("width"),
            height=a.get("original_dimensions", {}).get("height"),
            duration=a.get("playable_duration_in_ms"),
            preview_url=a.get("playable_url"),
            small_image=a.get("chat_image"),
            medium_image=a.get("inbox_image"),
            large_image=a.get("large_image"),
            uid=a.get("legacy_attachment_id"),
        )
    elif _type == "MessageAudio":
        return AudioAttachment(
            filename=a.get("filename"),
            url=a.get("playable_url"),
            duration=a.get("playable_duration_in_ms"),
            audio_type=a.get("audio_type"),
        )
    elif _type == "MessageFile":
        return FileAttachment(
            url=a.get("url"),
            name=a.get("filename"),
            is_malicious=a.get("is_malicious"),
            uid=a.get("message_file_fbid"),
        )
    else:
        return Attachment(uid=a.get("legacy_attachment_id"))


def graphql_to_extensible_attachment(a):
    story = a.get("story_attachment")
    if story:
        target = story.get("target")
        if target:
            _type = target["__typename"]
            if _type == "MessageLocation":
                url = story.get("url")
                address = get_url_parameter(get_url_parameter(url, "u"), "where1")
                try:
                    latitude, longitude = [float(x) for x in address.split(", ")]
                    address = None
                except ValueError:
                    latitude, longitude = None, None
                rtn = LocationAttachment(
                    uid=int(story["deduplication_key"]),
                    latitude=latitude,
                    longitude=longitude,
                    address=address,
                )
                media = story.get("media")
                if media and media.get("image"):
                    image = media["image"]
                    rtn.image_url = image.get("uri")
                    rtn.image_width = image.get("width")
                    rtn.image_height = image.get("height")
                rtn.url = url
                return rtn
            elif _type == "MessageLiveLocation":
                rtn = LiveLocationAttachment(
                    uid=int(story["target"]["live_location_id"]),
                    latitude=story["target"]["coordinate"]["latitude"]
                    if story["target"].get("coordinate")
                    else None,
                    longitude=story["target"]["coordinate"]["longitude"]
                    if story["target"].get("coordinate")
                    else None,
                    name=story["title_with_entities"]["text"],
                    expiration_time=story["target"].get("expiration_time"),
                    is_expired=story["target"].get("is_expired"),
                )
                media = story.get("media")
                if media and media.get("image"):
                    image = media["image"]
                    rtn.image_url = image.get("uri")
                    rtn.image_width = image.get("width")
                    rtn.image_height = image.get("height")
                rtn.url = story.get("url")
                return rtn
            elif _type in ["ExternalUrl", "Story"]:
                url = story.get("url")
                rtn = ShareAttachment(
                    uid=a.get("legacy_attachment_id"),
                    author=story["target"]["actors"][0]["id"]
                    if story["target"].get("actors")
                    else None,
                    url=url,
                    original_url=get_url_parameter(url, "u")
                    if "/l.php?u=" in url
                    else url,
                    title=story["title_with_entities"].get("text"),
                    description=story["description"].get("text")
                    if story.get("description")
                    else None,
                    source=story["source"].get("text"),
                    attachments=[
                        graphql_to_subattachment(attachment)
                        for attachment in story.get("subattachments")
                    ],
                )
                media = story.get("media")
                if media and media.get("image"):
                    image = media["image"]
                    rtn.image_url = image.get("uri")
                    rtn.original_image_url = (
                        get_url_parameter(rtn.image_url, "url")
                        if "/safe_image.php" in rtn.image_url
                        else rtn.image_url
                    )
                    rtn.image_width = image.get("width")
                    rtn.image_height = image.get("height")
                return rtn
        else:
            return UnsentMessage(uid=a.get("legacy_attachment_id"))


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


def graphql_to_live_location(a):
    return LiveLocationAttachment(
        uid=a["id"],
        latitude=a["coordinate"]["latitude"] / (10 ** 8)
        if not a.get("stopReason")
        else None,
        longitude=a["coordinate"]["longitude"] / (10 ** 8)
        if not a.get("stopReason")
        else None,
        name=a.get("locationTitle"),
        expiration_time=a["expirationTime"],
        is_expired=bool(a.get("stopReason")),
    )


def graphql_to_poll(a):
    rtn = Poll(
        title=a.get("title") if a.get("title") else a.get("text"),
        options=[graphql_to_poll_option(m) for m in a.get("options")],
    )
    rtn.uid = int(a["id"])
    rtn.options_count = a.get("total_count")
    return rtn


def graphql_to_poll_option(a):
    if a.get("viewer_has_voted") is None:
        vote = None
    elif isinstance(a["viewer_has_voted"], bool):
        vote = a["viewer_has_voted"]
    else:
        vote = a["viewer_has_voted"] == "true"
    rtn = PollOption(text=a.get("text"), vote=vote)
    rtn.uid = int(a["id"])
    rtn.voters = (
        [m.get("node").get("id") for m in a.get("voters").get("edges")]
        if isinstance(a.get("voters"), dict)
        else a.get("voters")
    )
    rtn.votes_count = (
        a.get("voters").get("count")
        if isinstance(a.get("voters"), dict)
        else a.get("total_count")
    )
    return rtn


def graphql_to_plan(a):
    if a.get("event_members"):
        rtn = Plan(
            time=a.get("event_time"),
            title=a.get("title"),
            location=a.get("location_name"),
        )
        if a.get("location_id") != 0:
            rtn.location_id = str(a.get("location_id"))
        rtn.uid = a.get("oid")
        rtn.author_id = a.get("creator_id")
        guests = a.get("event_members")
        rtn.going = [uid for uid in guests if guests[uid] == "GOING"]
        rtn.declined = [uid for uid in guests if guests[uid] == "DECLINED"]
        rtn.invited = [uid for uid in guests if guests[uid] == "INVITED"]
        return rtn
    elif a.get("id") is None:
        rtn = Plan(
            time=a.get("event_time"),
            title=a.get("event_title"),
            location=a.get("event_location_name"),
            location_id=a.get("event_location_id"),
        )
        rtn.uid = a.get("event_id")
        rtn.author_id = a.get("event_creator_id")
        guests = json.loads(a.get("guest_state_list"))
    else:
        rtn = Plan(
            time=a.get("time"),
            title=a.get("event_title"),
            location=a.get("location_name"),
        )
        rtn.uid = a.get("id")
        rtn.author_id = a.get("lightweight_event_creator").get("id")
        guests = a.get("event_reminder_members").get("edges")
    rtn.going = [
        m.get("node").get("id") for m in guests if m.get("guest_list_state") == "GOING"
    ]
    rtn.declined = [
        m.get("node").get("id")
        for m in guests
        if m.get("guest_list_state") == "DECLINED"
    ]
    rtn.invited = [
        m.get("node").get("id")
        for m in guests
        if m.get("guest_list_state") == "INVITED"
    ]
    return rtn


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
        emoji_size=get_emojisize_from_tags(message.get("tags_list")),
        sticker=graphql_to_sticker(message.get("sticker")),
    )
    rtn.uid = str(message.get("message_id"))
    rtn.author = str(message.get("message_sender").get("id"))
    rtn.timestamp = message.get("timestamp_precise")
    rtn.unsent = False
    if message.get("unread") is not None:
        rtn.is_read = not message["unread"]
    rtn.reactions = {
        str(r["user"]["id"]): enum_extend_if_invalid(MessageReaction, r["reaction"])
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


def graphql_to_user(user):
    if user.get("profile_picture") is None:
        user["profile_picture"] = {}
    c_info = get_customization_info(user)
    plan = None
    if user.get("event_reminders"):
        plan = (
            graphql_to_plan(user["event_reminders"]["nodes"][0])
            if user["event_reminders"].get("nodes")
            else None
        )
    return User(
        user["id"],
        url=user.get("url"),
        first_name=user.get("first_name"),
        last_name=user.get("last_name"),
        is_friend=user.get("is_viewer_friend"),
        gender=GENDERS.get(user.get("gender")),
        affinity=user.get("affinity"),
        nickname=c_info.get("nickname"),
        color=c_info.get("color"),
        emoji=c_info.get("emoji"),
        own_nickname=c_info.get("own_nickname"),
        photo=user["profile_picture"].get("uri"),
        name=user.get("name"),
        message_count=user.get("messages_count"),
        plan=plan,
    )


def graphql_to_thread(thread):
    if thread["thread_type"] == "GROUP":
        return graphql_to_group(thread)
    elif thread["thread_type"] == "ONE_TO_ONE":
        if thread.get("big_image_src") is None:
            thread["big_image_src"] = {}
        c_info = get_customization_info(thread)
        participants = [
            node["messaging_actor"] for node in thread["all_participants"]["nodes"]
        ]
        user = next(
            p for p in participants if p["id"] == thread["thread_key"]["other_user_id"]
        )
        last_message_timestamp = None
        if "last_message" in thread:
            last_message_timestamp = thread["last_message"]["nodes"][0][
                "timestamp_precise"
            ]

        first_name = user.get("short_name")
        if first_name is None:
            last_name = None
        else:
            last_name = user.get("name").split(first_name, 1).pop().strip()

        plan = None
        if thread.get("event_reminders"):
            plan = (
                graphql_to_plan(thread["event_reminders"]["nodes"][0])
                if thread["event_reminders"].get("nodes")
                else None
            )

        return User(
            user["id"],
            url=user.get("url"),
            name=user.get("name"),
            first_name=first_name,
            last_name=last_name,
            is_friend=user.get("is_viewer_friend"),
            gender=GENDERS.get(user.get("gender")),
            affinity=user.get("affinity"),
            nickname=c_info.get("nickname"),
            color=c_info.get("color"),
            emoji=c_info.get("emoji"),
            own_nickname=c_info.get("own_nickname"),
            photo=user["big_image_src"].get("uri"),
            message_count=thread.get("messages_count"),
            last_message_timestamp=last_message_timestamp,
            plan=plan,
        )
    else:
        raise FBchatException(
            "Unknown thread type: {}, with data: {}".format(
                thread.get("thread_type"), thread
            )
        )


def graphql_to_group(group):
    if group.get("image") is None:
        group["image"] = {}
    c_info = get_customization_info(group)
    last_message_timestamp = None
    if "last_message" in group:
        last_message_timestamp = group["last_message"]["nodes"][0]["timestamp_precise"]
    plan = None
    if group.get("event_reminders"):
        plan = (
            graphql_to_plan(group["event_reminders"]["nodes"][0])
            if group["event_reminders"].get("nodes")
            else None
        )
    return Group(
        group["thread_key"]["thread_fbid"],
        participants=set(
            [
                node["messaging_actor"]["id"]
                for node in group["all_participants"]["nodes"]
            ]
        ),
        nicknames=c_info.get("nicknames"),
        color=c_info.get("color"),
        emoji=c_info.get("emoji"),
        admins=set([node.get("id") for node in group.get("thread_admins")]),
        approval_mode=bool(group.get("approval_mode"))
        if group.get("approval_mode") is not None
        else None,
        approval_requests=set(
            node["requester"]["id"] for node in group["group_approval_queue"]["nodes"]
        )
        if group.get("group_approval_queue")
        else None,
        join_link=group["joinable_mode"].get("link"),
        photo=group["image"].get("uri"),
        name=group.get("name"),
        message_count=group.get("messages_count"),
        last_message_timestamp=last_message_timestamp,
        plan=plan,
    )


def graphql_to_page(page):
    if page.get("profile_picture") is None:
        page["profile_picture"] = {}
    if page.get("city") is None:
        page["city"] = {}
    plan = None
    if page.get("event_reminders"):
        plan = (
            graphql_to_plan(page["event_reminders"]["nodes"][0])
            if page["event_reminders"].get("nodes")
            else None
        )
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
