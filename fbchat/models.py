from __future__ import unicode_literals
import sys

class Base():
    def __repr__(self):
        uni = self.__unicode__()
        return uni.encode('utf-8') if sys.version_info < (3, 0) else uni

    def __unicode__(self):
        return u'<%s %s (%s)>' % (self.type.upper(), self.name, self.url)

class User(Base):
    def __init__(self, data):
        if data['type'] != 'user':
            raise Exception("[!] %s <%s> is not a user" % (data['text'], data['path']))
        self.uid = data['uid']
        self.type = data['type']
        self.photo = data['photo']
        self.url = data['path']
        self.name = data['text']
        self.score = data['score']

        self.data = data

class Thread():
    def __init__(self, **entries): 
        self.__dict__.update(entries)

class Message():
    def __init__(self, **entries):
        self.__dict__.update(entries)
