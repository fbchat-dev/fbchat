from __future__ import unicode_literals

class Base():
    def __repr__(self):
        return self.__unicode__().encode('utf-8')

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
        #self.score = jsoin['score']
        #self.tokens = data['tokens']

        self.data = data

class Thread():
    def __init__(self, **entries): 
        self.__dict__.update(entries)
