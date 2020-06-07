import datetime
import pytest
from fbchat import ParseError
from fbchat._session import (
    parse_server_js_define,
    base36encode,
    prefix_url,
    generate_message_id,
    session_factory,
    client_id_factory,
    find_form_request,
    get_error_data,
)


def test_parse_server_js_define_old():
    html = """
    some data;require("TimeSliceImpl").guard(function(){(require("ServerJSDefine")).handleDefines([["DTSGInitialData",[],{"token":"123"},100]])

    <script>require("TimeSliceImpl").guard(function() {require("ServerJSDefine").handleDefines([["DTSGInitData",[],{"token":"123","async_get_token":"12345"},3333]])

    </script>
    other irrelevant data
    """
    define = parse_server_js_define(html)
    assert define == {
        "DTSGInitialData": {"token": "123"},
        "DTSGInitData": {"async_get_token": "12345", "token": "123"},
    }


def test_parse_server_js_define_new():
    html = """
    some data;require("TimeSliceImpl").guard(function(){new (require("ServerJS"))().handle({"define":[["DTSGInitialData",[],{"token":""},100]],"require":[...]});}, "ServerJS define", {"root":true})();
    more data
    <script><script>require("TimeSliceImpl").guard(function(){var s=new (require("ServerJS"))();s.handle({"define":[["DTSGInitData",[],{"token":"","async_get_token":""},3333]],"require":[...]});require("Run").onAfterLoad(function(){s.cleanup(require("TimeSliceImpl"))});}, "ServerJS define", {"root":true})();</script>
    other irrelevant data
    """
    define = parse_server_js_define(html)
    assert define == {
        "DTSGInitialData": {"token": ""},
        "DTSGInitData": {"async_get_token": "", "token": ""},
    }


def test_parse_server_js_define_error():
    with pytest.raises(ParseError, match="Could not find any"):
        parse_server_js_define("")

    html = 'function(){(require("ServerJSDefine")).handleDefines([{"a": function(){}}])'
    with pytest.raises(ParseError, match="Invalid"):
        parse_server_js_define(html + html)

    html = 'function(){require("ServerJSDefine").handleDefines({"a": "b"})'
    with pytest.raises(ParseError, match="Invalid"):
        parse_server_js_define(html + html)


@pytest.mark.parametrize(
    "number,expected",
    [(1, "1"), (10, "a"), (123, "3f"), (1000, "rs"), (123456789, "21i3v9")],
)
def test_base36encode(number, expected):
    assert base36encode(number) == expected


def test_prefix_url():
    static_url = "https://upload.messenger.com/"
    assert prefix_url(static_url) == static_url
    assert prefix_url("/") == "https://www.messenger.com/"
    assert prefix_url("/abc") == "https://www.messenger.com/abc"


def test_generate_message_id():
    # Returns random output, so hard to test more thoroughly
    assert generate_message_id(datetime.datetime.utcnow(), "def")


def test_session_factory():
    session = session_factory()
    assert session.headers


def test_client_id_factory():
    # Returns random output, so hard to test more thoroughly
    assert client_id_factory()


def test_find_form_request():
    html = """
    <div>
    <form action="/checkpoint/?next=https%3A%2F%2Fwww.messenger.com%2F" class="checkpoint" id="u_0_c" method="post" onsubmit="">
        <input autocomplete="off" name="jazoest" type="hidden" value="some-number" />
        <input autocomplete="off" name="fb_dtsg" type="hidden" value="some-base64" />
        <input class="hidden_elem" data-default-submit="true" name="submit[Continue]" type="submit" />
        <input autocomplete="off" name="nh" type="hidden" value="some-hex" />
        <div class="_4-u2 _5x_7 _p0k _5x_9 _4-u8">
            <div class="_2e9n" id="u_0_d">
                <strong id="u_0_e">Two factor authentication required</strong>
                <div id="u_0_f"></div>
            </div>
            <div class="_2ph_">
                <input autocomplete="off" name="no_fido" type="hidden" value="true" />
                <div class="_50f4">You've asked us to require a 6-digit login code when anyone tries to access your account from a new device or browser.</div>
                <div class="_3-8y _50f4">Enter the 6-digit code from your Code Generator or 3rd party app below.</div>
                <div class="_2pie _2pio">
                    <span>
                        <input aria-label="Login code" autocomplete="off" class="inputtext" id="approvals_code" name="approvals_code" placeholder="Login code" tabindex="1" type="text" />
                    </span>
                </div>
            </div>
            <div class="_5hzs" id="checkpointBottomBar">
                <div class="_2s5p">
                    <button class="_42ft _4jy0 _2kak _4jy4 _4jy1 selected _51sy" id="checkpointSubmitButton" name="submit[Continue]" type="submit" value="Continue">Continue</button>
                </div>
                <div class="_2s5q">
                    <div class="_25b6" id="u_0_g">
                        <a href="#" id="u_0_h" role="button">Need another way to authenticate?</a>
                    </div>
                </div>
            </div>
        </div>
    </form>
    </div>
    """
    url, data = find_form_request(html)
    assert url.startswith("https://www.facebook.com/checkpoint/")
    assert {
        "jazoest": "some-number",
        "fb_dtsg": "some-base64",
        "nh": "some-hex",
        "no_fido": "true",
        "approvals_code": "[missing]",
        "submit[Continue]": "Continue",
    } == data


def test_find_form_request_error():
    with pytest.raises(ParseError, match="Could not find form to submit"):
        assert find_form_request("")
    with pytest.raises(ParseError, match="Could not find url to submit to"):
        assert find_form_request("<form></form>")


def test_get_error_data():
    html = """<!DOCTYPE html>
    <html lang="da" id="facebook" class="no_js">

    <head>
        <meta charset="utf-8" />
        <title id="pageTitle">Messenger</title>
        <meta name="referrer" content="default" id="meta_referrer" />
    </head>

    <body class="_605a x1 Locale_da_DK" dir="ltr">
    <div class="_3v_o" id="XMessengerDotComLoginViewPlaceholder">
    <form id="login_form" action="/login/password/" method="post" onsubmit="">
        <input type="hidden" name="jazoest" value="2222" autocomplete="off" />
        <input type="hidden" name="lsd" value="xyz-abc" autocomplete="off" />
        <div class="_3403 _3404">
            <div>Type your password again</div>
            <div>The password you entered is incorrect. <a href="https://www.facebook.com/recover/initiate?ars=facebook_login_pw_error">Did you forget your password?</a></div>
        </div>
        <div id="loginform">
            <input type="hidden" autocomplete="off" id="initial_request_id" name="initial_request_id" value="xxx" />
            <input type="hidden" autocomplete="off" name="timezone" value="" id="u_0_1" />
            <input type="hidden" autocomplete="off" name="lgndim" value="" id="u_0_2" />
            <input type="hidden" name="lgnrnd" value="aaa" />
            <input type="hidden" id="lgnjs" name="lgnjs" value="n" />
            <input type="text" class="inputtext _55r1 _43di" id="email" name="email" placeholder="E-mail or phone number" value="some@email.com" tabindex="0" aria-label="E-mail or phone number" />
            <input type="password" class="inputtext _55r1 _43di" name="pass" id="pass" tabindex="0" placeholder="Password" aria-label="Password" />
            <button value="1" class="_42ft _4jy0 _2m_r _43dh _4jy4 _517h _51sy" id="loginbutton" name="login" tabindex="0" type="submit">Continue</button>
            <div class="_43dj">
                <div class="uiInputLabel clearfix">
                    <label class="uiInputLabelInput">
                        <input type="checkbox" value="1" name="persistent" tabindex="0" class="" id="u_0_0" />
                        <span class=""></span>
                    </label>
                    <label for="u_0_0" class="uiInputLabelLabel">Stay logged in</label>
                </div>
                <input type="hidden" autocomplete="off" id="default_persistent" name="default_persistent" value="0" />
            </div>
    </form>
    </div>
    </body>

    </html>
    """
    msg = "The password you entered is incorrect. Did you forget your password?"
    assert msg == get_error_data(html)
