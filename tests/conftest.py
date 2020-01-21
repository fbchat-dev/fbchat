import pytest


@pytest.fixture(scope="session")
def session():
    class FakeSession:
        # TODO: Add a further mocked session
        user_id = "31415926536"

        def __repr__(self):
            return "<FakeSession>"

    return FakeSession()
