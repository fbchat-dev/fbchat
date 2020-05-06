# TODO: Consider adding Session.from_file and Session.to_file,
# which would make this example a lot easier!

import atexit
import json
import getpass
import fbchat


def load_cookies(filename):
    try:
        # Load cookies from file
        with open(filename) as f:
            return json.load(f)
    except FileNotFoundError:
        return  # No cookies yet


def save_cookies(filename, cookies):
    with open(filename, "w") as f:
        json.dump(cookies, f)


def load_session(cookies):
    if not cookies:
        return
    try:
        return fbchat.Session.from_cookies(cookies)
    except fbchat.FacebookError:
        return  # Failed loading from cookies


cookies = load_cookies("session.json")
session = load_session(cookies)
if not session:
    # Session could not be loaded, login instead!
    session = fbchat.Session.login("<email>", getpass.getpass())

# Save session cookies to file when the program exits
atexit.register(lambda: save_cookies("session.json", session.get_cookies()))

# Do stuff with session here
