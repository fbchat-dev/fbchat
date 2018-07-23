# -*- coding: UTF-8 -*-

from __future__ import unicode_literals

import threading
import logging

from random import randint
from time import sleep
from .base import BaseClient
from .models import Event, Message, Action

log = logging.getLogger(__name__)


class StopListen(BaseException):
    pass


class ListenerClient(BaseClient):
    """Enables basic listening

    Attributes:
        is_listening (threading.Event): Whether the client is currently listening
    """

    def __init__(self, *args, **kwargs):
        super(self, ListenerClient).__init__(*args, **kwargs)

        self._should_stop_listening = threading.Event()
        self.is_listening = threading.Event()

        self._sticky, self._pool = (None, None)
        self._clientid = hex(randint(2**31))[2:]


    def listen(self):
        """Start listening for incoming messages or events

        When the client recieves an event, it will parse the event,
        and call the corresponding `on_` method
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

        Attributes:
            called_externally (bool): Set this if you're calling from another
                python-thread, or other multithreaded shenanigans
        """
        self._should_stop_listening.set()
        if called_externally:
            if not self.is_listening.wait(60):
                raise ValueError("Could not stop listening: The operation timed out")
        else:
            raise StopListen()


    def init_listener(self):
        """Prepare the event listener.

        This method is useful if you want to control the listener from an
        external event loop
        """
        if self.is_listening.is_set():
            raise ValueError("Can't start listening: The client is already listening")
        self.is_listening.set()

        j = self.s.get("https://0-edge-chat.facebook.com/pull", query={
            'msgs_recv': 0,
            'channel': 'p_' + str(self.id),
            'clientid': self._clientid,
        }).json()

        self._sticky = j['lb_info']['sticky']
        self._pool = j['lb_info']['pool']

        self.s.params['seq'] = '0'

    def step_listener(self):
        """Do one cycle of the listening loop.

        This method is useful if you want to control the listener from an
        external event loop
        """

        try:
            self.s.get("https://0-edge-chat.facebook.com/active_ping", query={
                'channel': 'p_' + str(self.id),
                'clientid': self._clientid,
                'partition': -2,
                'cap': 0,
                'uid': self.id,
                'sticky_token': self._sticky,
                'sticky_pool': self._pool,
                'viewer_uid': self.id,
                'state': 'active',
            })

            j = self.s.get("https://0-edge-chat.facebook.com/pull", query={
                'msgs_recv': 0,
                'sticky_token': self._sticky,
                'sticky_pool': self._pool,
                'clientid': self._clientid,
            }).json()
        except requests.Timeout:
            # The pull request is expected to time out if there was no new data
            pass
        except requests.ConnectionError:
            # If we lost our internet connection, keep trying every minute
            sleep(60)
        '''
        except FacebookError as e:
            # Fix 502 and 503 pull errors
            if e.request_status_code in [502, 503]:
                self.req_url.change_pull_channel()
                self.startListening()
            else:
                raise e
        '''

        self.s.params['seq'] = j.get('seq', '0')

        try:
            self._parse_raw(j)
        except Exception as e:
            self.on_error(e, j)

    def clean_listener(self):
        """Cleanup the event listener.

        This method is useful if you want to control the listener from an
        external event loop
        """
        self.is_listening.clear()
        self.sticky, self.pool = (None, None)


    def _parse_raw(self, raw_data):
        log.debug("Data from listening: %s", data)

        if 'ms' not in data:
            self.on_unknown(data)
            return

        for m in data['ms']:
            if not self.parse_data(m, data.get('type')):
                self.on_unknown(m)

    def parse_data(self, data):
        """Called when data is recieved while listening

        This method is overwritten by other classes, to parse the data they need

        Args:
            data (dict): Dictionary containing the json data recieved

        Return:
            ``True`` if the data was parsed, ``False`` or ``None`` if it was unknown
        """

        # Happens on every login
        if data.get('type') == 'qprimer':
            return True

    def on_error(self, exception, data):
        """Called when an error was encountered while listening

        Args:
            exception (Exception): The exception that was encountered
            data (dict): Dictionary containing the full json data recieved
        """
        log.exception("Caught exception while listening. Caused by %s", data)

    def on_unknown(self, data):
        """Called when some unknown data was recieved while listening

        Useful for debugging, and finding missing features / unclaimed potential

        Args:
            data (dict): Dictionary containing the unknown json data recieved
        """
        log.info("Unknown data recieved while pulling: %s", data)

    def on_event(self, event):
        """Called when an event is executed / sent in a thread

        Calls `SenderClient.on_message` and `ThreadInterracterClient.on_action`,
        based on the type of event

        Args:
            event (`Event`): The executed / sent event
        """
        pass # Implemented in other classes
