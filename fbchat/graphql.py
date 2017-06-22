# -*- coding: UTF-8 -*-

from __future__ import unicode_literals
import json
import re
from .models import *
from .utils import *

# Shameless copy from https://stackoverflow.com/a/8730674
FLAGS = re.VERBOSE | re.MULTILINE | re.DOTALL
WHITESPACE = re.compile(r'[ \t\n\r]*', FLAGS)

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

def graphql_to_message(message):
    if message.get('message_sender') is None:
        message['message_sender'] = {}
    if message.get('message') is None:
        message['message'] = {}
    is_read = None
    if message.get('unread') is not None:
        is_read = not message['unread']
    return Message(
        message.get('message_id'),
        author=message.get('message_sender').get('id'),
        timestamp=message.get('timestamp_precise'),
        is_read=is_read,
        reactions=message.get('message_reactions'),
        text=message.get('message').get('text'),
        mentions=[Mention(m.get('entity', {}).get('id'), offset=m.get('offset'), length=m.get('length')) for m in message.get('message').get('ranges', [])],
        sticker=message.get('sticker'),
        attachments=message.get('blob_attachments')
    )

def graphql_to_user(user):
    if user.get('profile_picture') is None:
        user['profile_picture'] = {}
    return User(
        user['id'],
        url=user.get('url'),
        first_name=user.get('first_name'),
        last_name=user.get('last_name'),
        is_friend=user.get('is_viewer_friend'),
        gender=GENDERS[user.get('gender')],
        affinity=user.get('affinity'),
        photo=user['profile_picture'].get('uri'),
        name=user.get('name')
    )

def graphql_to_group(group):
    if group.get('image') is None:
        group['image'] = {}
    return Group(
        group['thread_key']['thread_fbid'],
        participants=[node['messaging_actor']['id'] for node in group['all_participants']['nodes']],
        photo=group['image'].get('uri'),
        name=group.get('name')
    )

def graphql_to_page(page):
    if page.get('profile_picture') is None:
        page['profile_picture'] = {}
    if page.get('city') is None:
        page['city'] = {}
    return Page(
        page['id'],
        url=page.get('url'),
        city=page.get('city').get('name'),
        category=page.get('category_type'),
        photo=page['profile_picture'].get('uri'),
        name=page.get('name')
    )

def graphql_queries_to_json(*queries):
    """
    Queries should be a list of GraphQL objects
    """
    rtn = {}
    for i, query in enumerate(queries):
        rtn['q{}'.format(i)] = query.value
    return json.dumps(rtn)

def graphql_response_to_json(content):
    j = json.loads(content, cls=ConcatJSONDecoder)

    rtn = [None]*(len(j))
    for x in j:
        if 'error_results' in x:
            del rtn[-1]
            continue
        check_json(x)
        [(key, value)] = x.items()
        check_json(value)
        if 'response' in value:
            rtn[int(key[1:])] = value['response']
        else:
            rtn[int(key[1:])] = value['data']

    log.debug(rtn)

    return rtn

class GraphQL(object):
    def __init__(self, query=None, doc_id=None, params={}):
        if query is not None:
            self.value = {
                'priority': 0,
                'q': query,
                'query_params': params
            }
        elif doc_id is not None:
            self.value = {
                'doc_id': doc_id,
                'query_params': params
            }
        else:
            raise Exception('A query or doc_id must be specified')


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

    SEARCH_USER = """
    Query SearchUser(<search> = '', <limit> = 1) {
        entities_named(<search>) {
            search_results.of_type(user).first(<limit>) as users {
                nodes {
                    @User
                }
            }
        }
    }
    """ + FRAGMENT_USER

    SEARCH_GROUP = """
    Query SearchGroup(<search> = '', <limit> = 1, <pic_size> = 32) {
        viewer() {
            message_threads.with_thread_name(<search>).last(<limit>) as groups {
                nodes {
                    @Group
                }
            }
        }
    }
    """ + FRAGMENT_GROUP

    SEARCH_PAGE = """
    Query SearchPage(<search> = '', <limit> = 1) {
        entities_named(<search>) {
            search_results.of_type(page).first(<limit>) as pages {
                nodes {
                    @Page
                }
            }
        }
    }
    """ + FRAGMENT_PAGE

    SEARCH_THREAD = """
    Query SearchThread(<search> = '', <limit> = 1) {
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
    """ + FRAGMENT_USER + FRAGMENT_GROUP + FRAGMENT_PAGE
