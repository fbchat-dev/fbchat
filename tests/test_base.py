import pytest
import py_compile

from glob import glob
from os import path, environ
from fbchat import FBchatException, Message, Client


def test_examples():
    # Compiles the examples, to check for syntax errors
    for name in glob(path.join(path.dirname(__file__), "../examples", "*.py")):
        py_compile.compile(name)


@pytest.mark.trylast
@pytest.mark.online
def test_login(client1):
    assert client1.is_logged_in()
    email = client1.email
    password = client1.password

    client1.logout()

    assert not client1.is_logged_in()

    with pytest.raises(FBchatException):
        client1.login("<invalid email>", "<invalid password>", max_tries=1)

    client1.login(email, password)

    assert client1.is_logged_in()


@pytest.mark.trylast
@pytest.mark.online
def test_sessions(client1):
    session = client1.get_session()
    Client("no email needed", "no password needed", session_cookies=session)
    client1.set_session(session)
    assert client1.is_logged_in()
