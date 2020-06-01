import fbchat


def test_module_renaming():
    assert fbchat.Message.__module__ == "fbchat"
    assert fbchat.Group.__module__ == "fbchat"
    assert fbchat.Event.__module__ == "fbchat"
    assert fbchat.User.block.__module__ == "fbchat"
    assert fbchat.Session.login.__func__.__module__ == "fbchat"
    assert fbchat.Session._from_session.__func__.__module__ == "fbchat"
    assert fbchat.Message.session.fget.__module__ == "fbchat"
    assert fbchat.Session.__repr__.__module__ == "fbchat"


def test_did_not_rename():
    assert fbchat._graphql.queries_to_json.__module__ != "fbchat"
