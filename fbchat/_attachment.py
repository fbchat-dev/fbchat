# -*- coding: UTF-8 -*-
from __future__ import unicode_literals


class Attachment(object):
    #: The attachment ID
    uid = None

    def __init__(self, uid=None):
        """Represents a Facebook attachment"""
        self.uid = uid


class UnsentMessage(Attachment):
    def __init__(self, *args, **kwargs):
        """Represents an unsent message attachment"""
        super(UnsentMessage, self).__init__(*args, **kwargs)


class ShareAttachment(Attachment):
    #: ID of the author of the shared post
    author = None
    #: Target URL
    url = None
    #: Original URL if Facebook redirects the URL
    original_url = None
    #: Title of the attachment
    title = None
    #: Description of the attachment
    description = None
    #: Name of the source
    source = None
    #: URL of the attachment image
    image_url = None
    #: URL of the original image if Facebook uses `safe_image`
    original_image_url = None
    #: Width of the image
    image_width = None
    #: Height of the image
    image_height = None
    #: List of additional attachments
    attachments = None

    def __init__(
        self,
        author=None,
        url=None,
        original_url=None,
        title=None,
        description=None,
        source=None,
        image_url=None,
        original_image_url=None,
        image_width=None,
        image_height=None,
        attachments=None,
        **kwargs
    ):
        """Represents a shared item (eg. URL) that has been sent as a Facebook attachment"""
        super(ShareAttachment, self).__init__(**kwargs)
        self.author = author
        self.url = url
        self.original_url = original_url
        self.title = title
        self.description = description
        self.source = source
        self.image_url = image_url
        self.original_image_url = original_image_url
        self.image_width = image_width
        self.image_height = image_height
        if attachments is None:
            attachments = []
        self.attachments = attachments
