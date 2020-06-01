import pytest
import fbchat


@pytest.fixture(scope="session")
def session():
    return fbchat.Session(
        user_id="31415926536", fb_dtsg=None, revision=None, session=None
    )
