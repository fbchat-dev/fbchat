# -*- coding: UTF-8 -*-

from fbchat import *

c = Client("<email>", "<password>")

# This is a possible way we *could* build the library. Not saying it's a good
# idea, but I'd like your opinions

u = c.users[0]

# Updates the users nickname, also on Facebook's side
u.nickname = "New nickname"

# Should throw an error, since we can't change a persons name
u.name = "New name"


g = c.groups[0]

# Updates the title
g.title = "New title"

# Adds a user to the group. If they're already in the group, nothing would
# happen? Or should an error be thrown?
g.participants += [u]

# Makes every participant an admin
g.admins = g.participants

# Makes yourself the only admin in the group
g.admins = [c]


# Deletes the group
c.threads -= g


# Unfriends the user
c.friends -= u
