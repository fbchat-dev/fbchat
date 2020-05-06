import attr
import random
import paho.mqtt.client
import requests
from ._common import log, kw_only
from . import _util, _exception, _session, _graphql, _events

from typing import Iterable, Optional, Mapping, List


HOST = "edge-chat.messenger.com"

TOPICS = [
    # Things that happen in chats (e.g. messages)
    "/t_ms",
    # Group typing notifications
    "/thread_typing",
    # Private chat typing notifications
    "/orca_typing_notifications",
    # Active notifications
    "/orca_presence",
    # Other notifications not related to chats (e.g. friend requests)
    "/legacy_web",
    # Facebook's continuous error reporting/logging?
    "/br_sr",
    # Response to /br_sr
    "/sr_res",
    # Data about user-to-user calls
    # TODO: Investigate the response from this! (A bunch of binary data)
    # "/t_rtc",
    # TODO: Find out what this does!
    # TODO: Investigate the response from this! (A bunch of binary data)
    # "/t_p",
    # TODO: Find out what this does!
    "/webrtc",
    # TODO: Find out what this does!
    "/onevc",
    # TODO: Find out what this does!
    "/notify_disconnect",
    # Old, no longer active topics
    # These are here just in case something interesting pops up
    "/inbox",
    "/mercury",
    "/messaging_events",
    "/orca_message_notifications",
    "/pp",
    "/webrtc_response",
]


def get_cookie_header(session: requests.Session, url: str) -> str:
    """Extract a cookie header from a requests session."""
    # The cookies are extracted this way to make sure they're escaped correctly
    return requests.cookies.get_cookie_header(
        session.cookies, requests.Request("GET", url),
    )


def generate_session_id() -> int:
    """Generate a random session ID between 1 and 9007199254740991."""
    return random.randint(1, 2 ** 53)


def mqtt_factory() -> paho.mqtt.client.Client:
    # Configure internal MQTT handler
    mqtt = paho.mqtt.client.Client(
        client_id="mqttwsclient",
        clean_session=True,
        protocol=paho.mqtt.client.MQTTv31,
        transport="websockets",
    )
    mqtt.enable_logger()
    # mqtt.max_inflight_messages_set(20)  # The rest will get queued
    # mqtt.max_queued_messages_set(0)  # Unlimited messages can be queued
    # mqtt.message_retry_set(20)  # Retry sending for at least 20 seconds
    # mqtt.reconnect_delay_set(min_delay=1, max_delay=120)
    mqtt.tls_set()
    mqtt.connect_async(HOST, 443, keepalive=10)
    return mqtt


def fetch_sequence_id(session: _session.Session) -> int:
    """Fetch sequence ID."""
    params = {
        "limit": 0,
        "tags": ["INBOX"],
        "before": None,
        "includeDeliveryReceipts": False,
        "includeSeqID": True,
    }
    log.debug("Fetching MQTT sequence ID")
    # Same doc id as in `Client.fetch_threads`
    (j,) = session._graphql_requests(_graphql.from_doc_id("1349387578499440", params))
    sequence_id = j["viewer"]["message_threads"]["sync_sequence_id"]
    if not sequence_id:
        raise _exception.NotLoggedIn("Failed fetching sequence id")
    return int(sequence_id)


@attr.s(slots=True, kw_only=kw_only, eq=False)
class Listener:
    """Listen to incoming Facebook events.

    Initialize a connection to the Facebook MQTT service.

    Args:
        session: The session to use when making requests.
        chat_on: Whether ...
        foreground: Whether ...

    Example:
        >>> listener = fbchat.Listener(session, chat_on=True, foreground=True)
    """

    session = attr.ib(type=_session.Session)
    _chat_on = attr.ib(type=bool)
    _foreground = attr.ib(type=bool)
    _mqtt = attr.ib(factory=mqtt_factory, type=paho.mqtt.client.Client)
    _sync_token = attr.ib(None, type=Optional[str])
    _sequence_id = attr.ib(None, type=Optional[int])
    _tmp_events = attr.ib(factory=list, type=List[_events.Event])

    def __attrs_post_init__(self):
        # Configure callbacks
        self._mqtt.on_message = self._on_message_handler
        self._mqtt.on_connect = self._on_connect_handler

    def _handle_ms(self, j):
        """Handle /t_ms special logic.

        Returns whether to continue parsing the message.
        """
        # TODO: Merge this with the parsing in _events

        # Update sync_token when received
        # This is received in the first message after we've created a messenger
        # sync queue.
        if "syncToken" in j and "firstDeltaSeqId" in j:
            self._sync_token = j["syncToken"]
            self._sequence_id = j["firstDeltaSeqId"]
            return False

        if "errorCode" in j:
            error = j["errorCode"]
            # TODO: 'F\xfa\x84\x8c\x85\xf8\xbc-\x88 FB_PAGES_INSUFFICIENT_PERMISSION\x00'
            if error in ("ERROR_QUEUE_NOT_FOUND", "ERROR_QUEUE_OVERFLOW"):
                # ERROR_QUEUE_NOT_FOUND means that the queue was deleted, since too
                # much time passed, or that it was simply missing
                # ERROR_QUEUE_OVERFLOW means that the sequence id was too small, so
                # the desired events could not be retrieved
                log.error(
                    "The MQTT listener was disconnected for too long,"
                    " events may have been lost"
                )
                # TODO: Find a way to tell the user that they may now be missing events
                self._sync_token = None
                self._sequence_id = None
                return False
            log.error("MQTT error code %s received", error)
            return False

        # Update last sequence id
        # Except for the two cases above, this is always received
        self._sequence_id = j["lastIssuedSeqId"]
        return True

    def _on_message_handler(self, client, userdata, message):
        # Parse payload JSON
        try:
            j = _util.parse_json(message.payload.decode("utf-8"))
        except (_exception.FacebookError, UnicodeDecodeError):
            log.debug(message.payload)
            log.exception("Failed parsing MQTT data on %s as JSON", message.topic)
            return

        log.debug("MQTT payload: %s, %s", message.topic, j)

        if message.topic == "/t_ms":
            if not self._handle_ms(j):
                return

        try:
            # TODO: Don't handle this in a callback
            self._tmp_events = list(
                _events.parse_events(self.session, message.topic, j)
            )
        except _exception.ParseError:
            log.exception("Failed parsing MQTT data")

    def _on_connect_handler(self, client, userdata, flags, rc):
        if rc == 21:
            raise _exception.FacebookError(
                "Failed connecting. Maybe your cookies are wrong?"
            )
        if rc != 0:
            err = paho.mqtt.client.connack_string(rc)
            log.error("MQTT Connection Error: %s", err)
            return  # Don't try to send publish if the connection failed

        self._messenger_queue_publish()

    def _messenger_queue_publish(self):
        # configure receiving messages.
        payload = {
            "sync_api_version": 10,
            "max_deltas_able_to_process": 1000,
            "delta_batch_size": 500,
            "encoding": "JSON",
            "entity_fbid": self.session.user.id,
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
            "u": self.session.user.id,
            # Session ID
            "s": session_id,
            # Active status setting
            "chat_on": self._chat_on,
            # foreground_state - Whether the window is focused
            "fg": self._foreground,
            # Can be any random ID
            "d": self.session._client_id,
            # Application ID, taken from facebook.com
            "aid": 219994525426954,
            # MQTT extension by FB, allows making a SUBSCRIBE while CONNECTing
            "st": TOPICS,
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

        self._mqtt.username_pw_set(_util.json_minimal(username))

        headers = {
            "Cookie": get_cookie_header(
                self.session._session, "https://edge-chat.messenger.com/chat"
            ),
            "User-Agent": self.session._session.headers["User-Agent"],
            "Origin": "https://www.messenger.com",
            "Host": HOST,
        }

        # TODO: Is region (lla | atn | odn | others?) important?
        self._mqtt.ws_set_options(
            path="/chat?sid={}".format(session_id), headers=headers
        )

    def _reconnect(self) -> bool:
        # Try reconnecting
        self._configure_connect_options()
        try:
            self._mqtt.reconnect()
            return True
        except (
            # Taken from .loop_forever
            paho.mqtt.client.socket.error,
            OSError,
            paho.mqtt.client.WebsocketConnectionError,
        ) as e:
            log.debug("MQTT reconnection failed: %s", e)
            # Wait before reconnecting
            self._mqtt._reconnect_wait()
            return False

    def listen(self) -> Iterable[_events.Event]:
        """Run the listening loop continually.

        This is a blocking call, that will yield events as they arrive.

        This will automatically reconnect on errors, except if the errors are one of
        `PleaseRefresh` or `NotLoggedIn`.

        Example:
            Print events continually.

            >>> for event in listener.listen():
            ...     print(event)
        """
        if self._sequence_id is None:
            self._sequence_id = fetch_sequence_id(self.session)

        # Make sure we're connected
        while not self._reconnect():
            pass

        yield _events.Connect()

        while True:
            rc = self._mqtt.loop(timeout=1.0)

            # The sequence ID was reset in _handle_ms
            # TODO: Signal to the user that they should reload their data!
            if self._sequence_id is None:
                self._sequence_id = fetch_sequence_id(self.session)
                self._messenger_queue_publish()

            # If disconnect() has been called
            # Beware, internal API, may have to change this to something more stable!
            if self._mqtt._state == paho.mqtt.client.mqtt_cs_disconnecting:
                break  # Stop listening

            if rc != paho.mqtt.client.MQTT_ERR_SUCCESS:
                # If known/expected error
                if rc == paho.mqtt.client.MQTT_ERR_CONN_LOST:
                    yield _events.Disconnect(reason="Connection lost, retrying")
                elif rc == paho.mqtt.client.MQTT_ERR_NOMEM:
                    # This error is wrongly classified
                    # See https://github.com/eclipse/paho.mqtt.python/issues/340
                    yield _events.Disconnect(reason="Connection error, retrying")
                elif rc == paho.mqtt.client.MQTT_ERR_CONN_REFUSED:
                    raise _exception.NotLoggedIn("MQTT connection refused")
                else:
                    err = paho.mqtt.client.error_string(rc)
                    log.error("MQTT Error: %s", err)
                    reason = "MQTT Error: {}, retrying".format(err)
                    yield _events.Disconnect(reason=reason)

                while not self._reconnect():
                    pass

                yield _events.Connect()

            if self._tmp_events:
                yield from self._tmp_events
                self._tmp_events = []

    def disconnect(self) -> None:
        """Disconnect the MQTT listener.

        Can be called while listening, which will stop the listening loop.

        The `Listener` object should not be used after this is called!

        Example:
            Stop the listener when receiving a message with the text "/stop"

            >>> for event in listener.listen():
            ...     if isinstance(event, fbchat.MessageEvent):
            ...         if event.message.text == "/stop":
            ...             listener.disconnect()  # Almost the same "break"
        """
        self._mqtt.disconnect()

    def set_foreground(self, value: bool) -> None:
        """Set the ``foreground`` value while listening."""
        # TODO: Document what this actually does!
        payload = _util.json_minimal({"foreground": value})
        info = self._mqtt.publish("/foreground_state", payload=payload, qos=1)
        self._foreground = value
        # TODO: We can't wait for this, since the loop is running within the same thread
        # info.wait_for_publish()

    def set_chat_on(self, value: bool) -> None:
        """Set the ``chat_on`` value while listening."""
        # TODO: Document what this actually does!
        # TODO: Is this the right request to make?
        data = {"make_user_available_when_in_foreground": value}
        payload = _util.json_minimal(data)
        info = self._mqtt.publish("/set_client_settings", payload=payload, qos=1)
        self._chat_on = value
        # TODO: We can't wait for this, since the loop is running within the same thread
        # info.wait_for_publish()

    # def send_additional_contacts(self, additional_contacts):
    #     payload = _util.json_minimal({"additional_contacts": additional_contacts})
    #     info = self._mqtt.publish("/send_additional_contacts", payload=payload, qos=1)
    #
    # def browser_close(self):
    #     info = self._mqtt.publish("/browser_close", payload=b"{}", qos=1)
