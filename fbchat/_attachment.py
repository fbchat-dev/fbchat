# -*- coding: UTF-8 -*-
from __future__ import unicode_literals

import attr


@attr.s(cmp=False)
class Attachment(object):
    """Represents a Facebook attachment"""

    #: The attachment ID
    uid = attr.ib(None)


@attr.s(cmp=False)
class UnsentMessage(Attachment):
    """Represents an unsent message attachment"""


@attr.s(cmp=False)
class ShareAttachment(Attachment):
    """Represents a shared item (eg. URL) that has been sent as a Facebook attachment"""

    #: ID of the author of the shared post
    author = attr.ib(None)
    #: Target URL
    url = attr.ib(None)
    #: Original URL if Facebook redirects the URL
    original_url = attr.ib(None)
    #: Title of the attachment
    title = attr.ib(None)
    #: Description of the attachment
    description = attr.ib(None)
    #: Name of the source
    source = attr.ib(None)
    #: URL of the attachment image
    image_url = attr.ib(None)
    #: URL of the original image if Facebook uses `safe_image`
    original_image_url = attr.ib(None)
    #: Width of the image
    image_width = attr.ib(None)
    #: Height of the image
    image_height = attr.ib(None)
    #: List of additional attachments
    attachments = attr.ib(factory=list, converter=lambda x: [] if x is None else x)

    # Put here for backwards compatibility, so that the init argument order is preserved
    uid = attr.ib(None)
