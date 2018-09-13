# -*- coding: UTF-8 -*-

from __future__ import unicode_literals

import threading
import logging
import attr
import requests

from random import randint

from .base import BaseClient
from .models import Event, Message, Action

log = logging.getLogger(__name__)


class StopListen(BaseException):
    pass


@attr.s(slots=True)
class ListenerClient(BaseClient):
    """Enables basic listening"""

    _clientid = attr.ib(type=int, factory=lambda: "{:x}".format(randint(0, 2 ** 31)))
    _sticky = attr.ib(None, type=str)
    _pool = attr.ib(None, type=str)
    _should_stop_listening = attr.ib(type=threading.Event, factory=threading.Event)

    #: Whether the client is currently *not* listening
    is_not_listening = attr.ib(type=threading.Event, factory=threading.Event)

    def __attrs_post_init__(self):
        super(ListenerClient, self).__attrs_post_init__()
        self.is_not_listening.set()

    def listen(self):
        """Start listening for incoming messages or events

        When the client recieves an event, it will parse the event,
        and call the corresponding `on_` methods
        """
        try:
            self.init_listener()

            self._should_stop_listening.clear()

            while not self._should_stop_listening.is_set():
                try:
                    self.step_listener()
                except StopListen:
                    break
                except KeyboardInterrupt:
                    break
        finally:
            self.clean_listener()

    def stop_listen(self, called_externally=False):
        """Stop the event listener

        Args:
            called_externally (bool): Set this if you're calling from another
                python-thread, or other multithreaded shenanigans
        """
        self._should_stop_listening.set()

        if not called_externally:
            raise StopListen()

        if not self.is_not_listening.wait(60):
            raise ValueError("Could not stop listening: The operation timed out")

    def init_listener(self):
        """Prepare the event listener.

        This method is useful if you want to control the listener from an
        external event loop
        """
        self.is_not_listening.clear()

        j = self.session.get(
            "https://0-edge-chat.facebook.com/pull",
            params={
                "msgs_recv": 0,
                "channel": "p_{}".format(self.user.id),
                "clientid": self._clientid,
            },
        ).json()

        self._sticky = j["lb_info"]["sticky"]
        self._pool = j["lb_info"]["pool"]

        self.session.params["seq"] = "0"

    def step_listener(self, mark_alive=False):
        """Do one cycle of the listening loop.

        This method is useful if you want to control the listener from an
        external event loop
        """

        try:
            if mark_alive:
                self.session.get(
                    "https://0-edge-chat.facebook.com/active_ping",
                    params={
                        "channel": "p_{}".format(self.user.id),
                        "clientid": self._clientid,
                        "partition": -2,
                        "cap": 0,
                        "uid": self.user.id,
                        "sticky_token": self._sticky,
                        "sticky_pool": self._pool,
                        "viewer_uid": self.user.id,
                        "state": "active",
                    },
                )

            j = self.session.get(
                "https://0-edge-chat.facebook.com/pull",
                params={
                    "msgs_recv": 0,
                    "sticky_token": self._sticky,
                    "sticky_pool": self._pool,
                    "clientid": self._clientid,
                    "state": "active" if mark_alive else "offline",
                },
            ).json()
        except requests.Timeout:
            # The pull request is expected to time out if there was no new data
            return
        except requests.ConnectionError:
            # If we lost our internet connection, keep trying every minute
            self.is_not_listening.wait(60)
            return
        """
        except FacebookError as e:
            # Fix 502 and 503 pull errors
            if e.request_status_code in [502, 503]:
                self.req_url.change_pull_channel()
                self.startListening()
            else:
                raise e
        """

        self.session.params["seq"] = j.get("seq", "0")

        try:
            self._parse_raw(j)
        except Exception as e:
            self.on_error(e, j)

    def clean_listener(self):
        """Cleanup the event listener.

        This method is useful if you want to control the listener from an
        external event loop
        """
        self.is_not_listening.set()
        self._sticky, self._pool = (None, None)

    def _parse_raw(self, raw_data):
        log.debug("Data from listening: %s", raw_data)

        if "ms" not in raw_data:
            if raw_data.get("t") == "heartbeat":
                # Pull heartbeat, no need to do anything
                return
            self.on_unknown(raw_data)
            return

        for data in raw_data["ms"]:
            event = self.parse_data(data, data.get("type"))
            if not event:
                self.on_unknown(data)
            elif isinstance(event, Event):
                self.on_event(event)

    def parse_data(self, data, data_type):
        """Called when data is recieved while listening

        This method is overwritten by other classes, to parse the data they need

        Args:
            data (dict): Dictionary containing the json data recieved
            data_type (str): A special Facebook type of the recieved data

        Return:
            ``True`` if the data was parsed, ``False`` or ``None`` if it was unknown
        """

        # Happens on every login
        if data_type == "qprimer":
            return True

        if data_type == "delta":
            delta = data["delta"]
            return self.parse_delta_data(delta, delta.get("type"), delta.get("class"))

    def parse_delta_data(self, data, data_type, data_class):
        pass

    def on_error(self, exception, data):
        """Called when an error was encountered while listening

        Args:
            exception (Exception): The exception that was encountered
            data (dict): Dictionary containing the full json data recieved
        """
        raise exception

    def on_unknown(self, data):
        """Called when some unknown data was recieved while listening

        Useful for finding missing features / unclaimed potential

        Args:
            data (dict): Dictionary containing the unknown json data recieved
        """
        log.info("Unknown data recieved while listening: %s", data)

    def on_event(self, event):
        """Called when an event is executed / sent in a thread

        Calls `SenderClient.on_message` and `ThreadInterracterClient.on_action`,
        based on the type of event

        Args:
            event (`Event`): The executed / sent event
        """
        log.info("Event recieved: %s", event)
        pass  # Implemented in other classes
