import fbchat
import pytest
import logging
import getpass


@pytest.fixture(scope="session")
def session(pytestconfig):
    session_cookies = pytestconfig.cache.get("session_cookies", None)
    try:
        session = fbchat.Session.from_cookies(session_cookies)
    except fbchat.FacebookError:
        logging.exception("Error while logging in with cookies!")
        session = fbchat.Session.login(input("Email: "), getpass.getpass("Password: "))

    yield session

    pytestconfig.cache.set("session_cookies", session.get_cookies())


@pytest.fixture
def client(session):
    return fbchat.Client(session=session)


@pytest.fixture
def listener(session):
    return fbchat.Listener(session=session, chat_on=False, foreground=False)
