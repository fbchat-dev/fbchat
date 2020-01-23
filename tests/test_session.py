import datetime
import pytest
from fbchat._session import (
    base36encode,
    prefix_url,
    generate_message_id,
    client_id_factory,
    is_home,
    get_error_data,
)


@pytest.mark.parametrize(
    "number,expected",
    [(1, "1"), (10, "a"), (123, "3f"), (1000, "rs"), (123456789, "21i3v9")],
)
def test_base36encode(number, expected):
    assert base36encode(number) == expected


def test_prefix_url():
    assert prefix_url("/") == "https://www.facebook.com/"
    assert prefix_url("/abc") == "https://www.facebook.com/abc"


def test_generate_message_id():
    # Returns random output, so hard to test more thoroughly
    assert generate_message_id(datetime.datetime.utcnow(), "def")


def test_client_id_factory():
    # Returns random output, so hard to test more thoroughly
    assert client_id_factory()


def test_is_home():
    assert not is_home("https://m.facebook.com/login/?...")
    assert is_home("https://m.facebook.com/home.php?refsrc=...")


@pytest.mark.skip
def test_get_error_data():
    html = """<?xml version="1.0" encoding="utf-8"?>
    <!DOCTYPE html PUBLIC "-//WAPFORUM//DTD XHTML Mobile 1.0//EN" "http://www.wapforum.org/DTD/xhtml-mobile10.dtd">
    <html xmlns="http://www.w3.org/1999/xhtml">

    <head>
        <title>Log in to Facebook | Facebook</title>
        <meta name="referrer" content="origin-when-crossorigin" id="meta_referrer" />
        <style type="text/css">...</style>
        <meta name="description" content="..." />
        <link rel="canonical" href="https://www.facebook.com/login/" />
    </head>

    <body tabindex="0" class="b c d e f g">
    <div class="h"><div id="viewport">...<div id="objects_container"><div class="g" id="root" role="main">
    <table class="x" role="presentation"><tbody><tr><td class="y">
    <div class="z ba bb" style="" id="login_error">
        <div class="bc">
            <span>The password you entered is incorrect. <a href="/recover/initiate/?ars=facebook_login_pw_error&amp;email=abc@mail.com&amp;__ccr=XXX" class="bd" aria-label="Have you forgotten your password?">Did you forget your password?</a></span>
        </div>
    </div>
    ...
    </td></tr></tbody></table>
    <div style="display:none"></div><span><img src="https://facebook.com/security/hsts-pixel.gif" width="0" height="0" style="display:none" /></span>
    </div></div><div></div></div></div>
    </body>

    </html>
    """
    url = "https://m.facebook.com/login/?email=abc@mail.com&li=XXX&e=1348092"
    msg = "The password you entered is incorrect. Did you forget your password?"
    assert (1348092, msg) == get_error_data(html)
