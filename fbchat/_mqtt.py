import attr
import random
import paho.mqtt.client
from ._core import log
from . import _util, _exception, _graphql


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
    _sequence_id = attr.ib()
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
        mqtt.enable_logger()
        # mqtt.max_inflight_messages_set(20)
        # mqtt.max_queued_messages_set(0)  # unlimited
        # mqtt.message_retry_set(5)
        # mqtt.reconnect_delay_set(min_delay=1, max_delay=120)
        # TODO: Is region (lla | atn | odn | others?) important?
        mqtt.tls_set()

        self = cls(
            state=state,
            mqtt=mqtt,
            on_message=on_message,
            chat_on=chat_on,
            foreground=foreground,
            sequence_id=cls._fetch_sequence_id(state),
        )

        # Configure callbacks
        mqtt.on_message = self._on_message_handler
        mqtt.on_connect = self._on_connect_handler

        self._configure_connect_options()

        # Attempt to connect
        try:
            rc = mqtt.connect(self._HOST, 443, keepalive=10)
        except (
            # Taken from .loop_forever
            paho.mqtt.client.socket.error,
            OSError,
            paho.mqtt.client.WebsocketConnectionError,
        ) as e:
            raise _exception.FBchatException("MQTT connection failed") from e

        # Raise error if connecting failed
        if rc != paho.mqtt.client.MQTT_ERR_SUCCESS:
            err = paho.mqtt.client.error_string(rc)
            raise _exception.FBchatException("MQTT connection failed: {}".format(err))

        return self

    def _on_message_handler(self, client, userdata, message):
        # Parse payload JSON
        try:
            j = _util.parse_json(message.payload)
        except _exception.FBchatFacebookError:
            log.exception("Failed parsing MQTT data as JSON: %r", message.payload)
            return

        if message.topic == "/t_ms":
            # Update sync_token when received
            # This is received in the first message after we've created a messenger
            # sync queue.
            if "syncToken" in j and "firstDeltaSeqId" in j:
                self._sync_token = j["syncToken"]
                self._sequence_id = j["firstDeltaSeqId"]

            # Update last sequence id when received
            if "lastIssuedSeqId" in j:
                self._sequence_id = j["lastIssuedSeqId"]

            if "errorCode" in j:
                # Known types: ERROR_QUEUE_OVERFLOW | ERROR_QUEUE_NOT_FOUND
                # 'F\xfa\x84\x8c\x85\xf8\xbc-\x88 FB_PAGES_INSUFFICIENT_PERMISSION\x00'
                log.error("MQTT error code %s received", j["errorCode"])
                # TODO: Consider resetting the sync_token and sequence ID here?

        log.debug("MQTT payload: %s", j)

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

    def _on_connect_handler(self, client, userdata, flags, rc):
        # configure receiving messages.
        payload = {
            "sync_api_version": 10,
            "max_deltas_able_to_process": 1000,
            "delta_batch_size": 500,
            "encoding": "JSON",
            "entity_fbid": self._state.user_id,
        }

        # If we don't have a sync_token, create a new messenger queue
        # This is done so that across reconnects, if we've received a sync token, we
        # SHOULD receive a piece of data in /t_ms exactly once!
        if self._sync_token is None:
            topic = "/messenger_sync_create_queue"
            payload["initial_titan_sequence_id"] = str(self._sequence_id)
            payload["device_params"] = None
        else:
            topic = "/messenger_sync_get_diffs"
            payload["last_seq_id"] = str(self._sequence_id)
            payload["sync_token"] = self._sync_token

        self._mqtt.publish(topic, _util.json_minimal(payload), qos=1)

    def _configure_connect_options(self):
        # Generate a new session ID on each reconnect
        session_id = generate_session_id()

        username = {
            # The user ID
            "u": self._state.user_id,
            # Session ID
            "s": session_id,
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
            # Using this is more efficient, but the same can be acheived with:
            #     def on_connect(*args):
            #         mqtt.publish(topic, payload, qos=1)
            #     mqtt.on_connect = on_connect
            # TODO: For some reason this doesn't work!
            "pm": [
                # {
                #     "topic": topic,
                #     "payload": payload,
                #     "qos": 1,
                #     "messageId": 65536,
                # }
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

        headers = {
            # TODO: Make this access thread safe
            "Cookie": _util.get_cookie_header(self._state._session, self._HOST),
            "User-Agent": self._state._session.headers["User-Agent"],
            "Origin": "https://www.facebook.com",
            "Host": self._HOST,
        }

        self._mqtt.ws_set_options(
            path="/chat?sid={}".format(session_id), headers=headers
        )

    def loop_once(self, on_error=None):
        """Run the listening loop once.

        Returns whether to keep listening or not.
        """
        rc = self._mqtt.loop(timeout=1.0)

        # If disconnect() has been called
        if self._mqtt._state == paho.mqtt.client.mqtt_cs_disconnecting:
            return False  # Stop listening

        if rc != paho.mqtt.client.MQTT_ERR_SUCCESS:
            err = paho.mqtt.client.error_string(rc)
            log.warning("MQTT Error: %s", err)
            if on_error:
                # Temporary to support on_error param
                try:
                    raise _exception.FBchatException("MQTT Error: {}".format(err))
                except _exception.FBchatException as e:
                    on_error(exception=e)

            # Wait before reconnecting
            self._mqtt._reconnect_wait()

            # Try reconnecting
            self._configure_connect_options()
            try:
                self._mqtt.reconnect()
            except (
                # Taken from .loop_forever
                paho.mqtt.client.socket.error,
                OSError,
                paho.mqtt.client.WebsocketConnectionError,
            ):
                log.debug("MQTT connection failed")

        return True  # Keep listening

    def disconnect(self):
        self._mqtt.disconnect()

    def set_foreground(self, value):
        payload = _util.json_minimal({"foreground": value})
        info = self._mqtt.publish("/foreground_state", payload=payload, qos=1)
        self._foreground = value
        # TODO: We can't wait for this, since the loop is running with .loop_forever()
        # info.wait_for_publish()

    def set_chat_on(self, value):
        # TODO: Is this the right request to make?
        data = {"make_user_available_when_in_foreground": value}
        payload = _util.json_minimal(data)
        info = self._mqtt.publish("/set_client_settings", payload=payload, qos=1)
        self._chat_on = value
        # TODO: We can't wait for this, since the loop is running with .loop_forever()
        # info.wait_for_publish()

    # def send_additional_contacts(self, additional_contacts):
    #     payload = _util.json_minimal({"additional_contacts": additional_contacts})
    #     info = self._mqtt.publish("/send_additional_contacts", payload=payload, qos=1)
