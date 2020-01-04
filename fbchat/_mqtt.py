import attr
import random
import paho.mqtt.client
from ._core import log
from . import _util, _graphql


def generate_session_id():
    """Generate a random session ID between 1 and 9007199254740991."""
    return random.randint(1, 2 ** 53)


@attr.s(slots=True)
class Mqtt:
    _state = attr.ib()
    _mqtt = attr.ib()
    _on_message = attr.ib()
    _chat_on = attr.ib()
    _foreground = attr.ib()
    _session_id = attr.ib(factory=generate_session_id)
    _sync_token = attr.ib(None)

    _HOST = "edge-chat.facebook.com"

    @classmethod
    def connect(cls, state, on_message, chat_on, foreground):
        mqtt = paho.mqtt.client.Client(
            client_id="mqttwsclient",
            clean_session=True,
            protocol=paho.mqtt.client.MQTTv31,
            transport="websockets",
        )

        self = cls(
            state=state,
            mqtt=mqtt,
            on_message=on_message,
            chat_on=chat_on,
            foreground=foreground,
        )

        mqtt.enable_logger()
        # mqtt.max_inflight_messages_set(20)
        # mqtt.max_queued_messages_set(0)  # unlimited
        # mqtt.message_retry_set(5)
        # mqtt.reconnect_delay_set(min_delay=1, max_delay=120)
        # TODO: Is region (lla | atn | odn | others?) important?
        mqtt.tls_set()
        mqtt.ws_set_options(
            path="/chat?sid={}".format(session_id), headers=self._create_headers
        )
        mqtt.on_message = self._on_message_handler

        sequence_id = self._fetch_sequence_id(self._state)
        # Set connect/reconnect data with an empty sync token and an newly fetched
        # sequence id initially
        self._set_reconnect_data(self._sync_token, sequence_id)

        # TODO: Handle response code
        response_code = mqtt.connect(self._HOST, 443, keepalive=10)

    def _create_headers(self, headers):
        log.debug("Fetching MQTT headers")
        # TODO: Make this access thread safe
        headers["Cookie"] = _util.get_cookie_header(self._state._session, self._HOST)
        headers["User-Agent"] = self._state._session.headers["User-Agent"]
        headers["Origin"] = "https://www.facebook.com"
        headers["Host"] = self._HOST
        return headers

    def _on_message_handler(self, client, userdata, message):
        j = _util.parse_json(message.payload)
        if message.topic == "/t_ms":
            sequence_id = None

            # Update sync_token when received
            # This is received in the first message after we've created a messenger
            # sync queue.
            if "syncToken" in j and "firstDeltaSeqId" in j:
                self._sync_token = j["syncToken"]
                sequence_id = j["firstDeltaSeqId"]

            # Update last sequence id when received
            if "lastIssuedSeqId" in j:
                sequence_id = j["lastIssuedSeqId"]

            if sequence_id is not None:
                self._set_reconnect_data(self._sync_token, sequence_id)

        # Call the external callback
        self._on_message(message.topic, j)

    @staticmethod
    def _fetch_sequence_id(state):
        """Fetch sequence ID."""
        params = {
            "limit": 1,
            "tags": ["INBOX"],
            "before": None,
            "includeDeliveryReceipts": False,
            "includeSeqID": True,
        }
        log.debug("Fetching MQTT sequence ID")
        # Same request as in `Client.fetchThreadList`
        (j,) = state._graphql_requests(_graphql.from_doc_id("1349387578499440", params))
        try:
            return int(j["viewer"]["message_threads"]["sync_sequence_id"])
        except (KeyError, ValueError):
            # TODO: Proper exceptions
            raise

    @staticmethod
    def _get_messenger_sync(state, sync_token, sequence_id):
        """Get the data to configure receiving messages."""
        payload = {
            "sync_api_version": 10,
            "max_deltas_able_to_process": 1000,
            "delta_batch_size": 500,
            "encoding": "JSON",
            "entity_fbid": state.user_id,
        }

        # If we don't have a sync_token, create a new messenger queue
        # This is done so that across reconnects, if we've received a sync token, we
        # SHOULD receive a piece of data in /t_ms exactly once!
        if sync_token is None:
            topic = "/messenger_sync_create_queue"
            payload["initial_titan_sequence_id"] = str(sequence_id)
            payload["device_params"] = None
        else:
            topic = "/messenger_sync_get_diffs"
            payload["last_seq_id"] = str(sequence_id)
            payload["sync_token"] = sync_token

        return topic, payload

    def _set_reconnect_data(self, sync_token, sequence_id):
        log.debug("Setting MQTT reconnect data: %s/%s", sync_token, sequence_id)
        topic, payload = self._get_messenger_sync(self._state, sync_token, sequence_id)

        username = {
            # The user ID
            "u": self._state.user_id,
            # Session ID
            "s": self._session_id,
            # Active status setting
            "chat_on": self._chat_on,
            # foreground_state - Whether the window is focused
            "fg": self._foreground,
            # Can be any random ID
            "d": self._state._client_id,
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
            "pm": [
                {
                    "topic": topic,
                    "payload": _util.json_minimal(payload),
                    "qos": 1,
                    "messageId": 65536,
                }
                # The above is more efficient, but the same effect could have been
                # acheived with:
                #     def on_connect(*args):
                #         mqtt.publish(topic, payload=..., qos=1)
                #     mqtt.on_connect = on_connect
            ],
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

        # TODO: Make this thread safe
        self._mqtt.username_pw_set(_util.json_minimal(username))

    def listen(self):
        self._mqtt.loop_forever()  # TODO: retry_first_connection=True?

    def disconnect(self):
        self._mqtt.disconnect()

    def set_foreground(self, value):
        payload = _util.json_minimal({"foreground": value})
        info = self._mqtt.publish("/foreground_state", payload=payload, qos=1)
        self._foreground = value
        # TODO: We can't wait for this, since the loop is running with .loop_forever()
        # info.wait_for_publish()

    # def set_client_settings(self, available_when_in_foreground: bool):
    #     data = {"make_user_available_when_in_foreground": available_when_in_foreground}
    #     payload = _util.json_minimal(data)
    #     info = self._mqtt.publish("/set_client_settings", payload=payload, qos=1)
    #
    # def send_additional_contacts(self, additional_contacts):
    #     payload = _util.json_minimal({"additional_contacts": additional_contacts})
    #     info = self._mqtt.publish("/send_additional_contacts", payload=payload, qos=1)
