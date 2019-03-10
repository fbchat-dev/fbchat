# -*- coding: UTF-8 -*-
from __future__ import unicode_literals

import json
import re
from . import _util
from ._exception import FBchatException, FBchatUserError

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


def graphql_queries_to_json(*queries):
    """
    Queries should be a list of GraphQL objects
    """
    rtn = {}
    for i, query in enumerate(queries):
        rtn["q{}".format(i)] = query.value
    return json.dumps(rtn)


def graphql_response_to_json(content):
    content = _util.strip_to_json(content)  # Usually only needed in some error cases
    try:
        j = json.loads(content, cls=ConcatJSONDecoder)
    except Exception:
        raise FBchatException("Error while parsing JSON: {}".format(repr(content)))

    rtn = [None] * (len(j))
    for x in j:
        if "error_results" in x:
            del rtn[-1]
            continue
        _util.check_json(x)
        [(key, value)] = x.items()
        _util.check_json(value)
        if "response" in value:
            rtn[int(key[1:])] = value["response"]
        else:
            rtn[int(key[1:])] = value["data"]

    _util.log.debug(rtn)

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
