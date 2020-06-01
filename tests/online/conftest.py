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

    # TODO: Allow the main session object to be closed - and perhaps used in `with`?
    session._session.close()


@pytest.fixture
def client(session):
    return fbchat.Client(session=session)


@pytest.fixture(scope="session")
def user(pytestconfig, session):
    user_id = pytestconfig.cache.get("user_id", None)
    if not user_id:
        user_id = input("A user you're chatting with's id: ")
        pytestconfig.cache.set("user_id", user_id)
    return fbchat.User(session=session, id=user_id)


@pytest.fixture(scope="session")
def group(pytestconfig, session):
    group_id = pytestconfig.cache.get("group_id", None)
    if not group_id:
        group_id = input("A group you're chatting with's id: ")
        pytestconfig.cache.set("group_id", group_id)
    return fbchat.Group(session=session, id=group_id)


@pytest.fixture(
    scope="session",
    params=[
        "user",
        "group",
        "self",
        pytest.param("invalid", marks=[pytest.mark.xfail()]),
    ],
)
def any_thread(request, session, user, group):
    return {
        "user": user,
        "group": group,
        "self": session.user,
        "invalid": fbchat.Thread(session=session, id="0"),
    }[request.param]


@pytest.fixture
def listener(session):
    return fbchat.Listener(session=session, chat_on=False, foreground=False)
