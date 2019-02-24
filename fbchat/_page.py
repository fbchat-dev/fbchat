# -*- coding: UTF-8 -*-
from __future__ import unicode_literals

from ._thread import ThreadType, Thread


class Page(Thread):
    """Represents a Facebook page. Inherits `Thread`"""

    #: The page's custom url
    url = None
    #: The name of the page's location city
    city = None
    #: Amount of likes the page has
    likes = None
    #: Some extra information about the page
    sub_title = None
    #: The page's category
    category = None

    def __init__(
        self,
        uid,
        url=None,
        city=None,
        likes=None,
        sub_title=None,
        category=None,
        **kwargs
    ):
        super(Page, self).__init__(ThreadType.PAGE, uid, **kwargs)
        self.url = url
        self.city = city
        self.likes = likes
        self.sub_title = sub_title
        self.category = category
