import attr
import random
import paho.mqtt.client
from . import _util, _graphql


@attr.s(slots=True)
class Mqtt:
    _state = attr.ib()
    _mqtt = attr.ib()

    @classmethod
    def connect(cls, state, foreground):
        mqtt = paho.mqtt.client.Client(
            client_id="mqttwsclient",
            clean_session=True,
            protocol=paho.mqtt.client.MQTTv31,
            transport="websockets",
        )
        mqtt.enable_logger()

        # Generate a random session ID between 1 and 9007199254740991
        session_id = random.randint(1, 2 ** 53)

        username = {
            # The user ID
            "u": state.user_id,
            # Session ID
            "s": session_id,
            # Active status setting
            "chat_on": True,
            # foreground_state - Whether the window is focused
            "fg": foreground,
            # Can be any random ID
            "d": state._client_id,
            # Application ID, taken from facebook.com
            "aid": 219994525426954,
            # MQTT extension by FB, allows making a SUBSCRIBE while CONNECTing
            "st": [
                # TODO: Investigate the result from these
                # "/inbox",
                # "/mercury",
                # "/messaging_events",
                # "/orca_message_notifications",
                # "/pp",
                # "/t_p",
                # "/t_rtc",
                # "/webrtc_response",
                "/legacy_web",
                "/webrtc",
                "/onevc",
                # Things that happen in chats (e.g. messages)
                "/t_ms",
                # Group typing notifications
                "/thread_typing",
                # Private chat typing notifications
                "/orca_typing_notifications",
                "/notify_disconnect",
                # Active notifications
                "/orca_presence",
                "/br_sr",
                "/sr_res",
            ],
            # MQTT extension by FB, allows making a PUBLISH while CONNECTing
            "pm": [],
            # Unknown parameters
            "cp": 3,
            "ecp": 10,
            "ct": "websocket",
            "mqtt_sid": "",
            "dc": "",
            "no_auto_fg": True,
            "gas": None,
            "pack": [],
        }
        mqtt.username_pw_set(_util.json_minimal(username))

        headers = {
            "Cookie": _util.get_cookie_header(state._session, "edge-chat.facebook.com"),
            "User-Agent": state._session.headers["User-Agent"],
            "Origin": "https://www.facebook.com",
            "Host": "edge-chat.facebook.com",
        }

        # TODO: Is region (lla | atn | odn | others?) important?
        mqtt.ws_set_options(path="/chat?sid={}".format(session_id), headers=headers)
        mqtt.tls_set()
        response_code = mqtt.connect("edge-chat.facebook.com", 443, keepalive=10)
        # TODO: Handle response code

        return cls(state=state, mqtt=mqtt)

    def listen(self, on_message):
        def real_on_message(client, userdata, message):
            on_message(message.topic, message.payload)

        self._mqtt.on_message = real_on_message

        self._mqtt.loop_forever()  # TODO: retry_first_connection=True?

    def disconnect(self):
        self._mqtt.disconnect()

    def set_foreground(self, state):
        payload = _util.json_minimal({"foreground": state})
        info = self._mqtt.publish("/foreground_state", payload=payload, qos=1)
        # TODO: We can't wait for this, since the loop is running with .loop_forever()
        # info.wait_for_publish()
