# -*- coding: UTF-8 -*-

from __future__ import unicode_literals

from .core import CoreClient
from ..models import Thread, User, Group, Page, Text


__all__ = ("CacherClient",)


def add_events_to_cache(cache, events):
    min1, min2 = (0, 0)
    prepend = []
    for min1, min2, x in reversed(list(traverse(cache))):
        if x == events[0]:
            events = cache[min1][:min2] + events
            break
        if x.time < events[0].time:
            prepend = [cache[min1][: min2 + 1]]
            break

    max1, max2 = (0, 0)
    append = []
    for max1, max2, x in traverse(cache):
        if x == events[-1]:
            events = events + cache[max1][max2 + 1 :]
            break
        if x.time > events[-1].time:
            append = [cache[max1][max2:]]
            break

    return cache[:min1] + prepend + [events] + append + cache[max1 + 1 :]


class CacherClient(CoreClient):
    """Enables caching information about threads"""

    def __init__(self, *args, **kwargs):
        super(self, CacherClient).__init__(*args, **kwargs)
        self._threads = set(self)  # Unordered, `self` is a thread, too
        self._events = set()  # Unordered

    def get_thread(self, thread_id):
        """Retrieves a thread from the cache, by it's ID

        Args:
            thread_id (int): The `Thread` to retrieve, by it's ID

        Return:
            The cached thread, if found, otherwise a new `Thread` instance is created,
            added to the cache, and returned
        """
        return self._cache_thread(Thread(thread_id))

    def _cache_thread(self, thread):
        """Add a thread to the cache

        If the thread is already in the cache, the relevant data is updated

        Args:
            thread (`Thread`): The thread to add

        Return:
            If the thread was found in the cache, then the updated `Thread` is returned.
            Otherwise, the supplied thread is simply returned
        """

        if thread in self._threads:
            old_thread = self._threads[self._threads.index(thread)]
            if old_thread is thread:
                return old_thread
            for name, value in vars(thread).items():
                # if getattr(old_thread, name) != value:
                setattr(old_thread, name, value)
            if type(thread) != type(old_thread) and type(thread) != Thread:
                old_thread.__class__ = type(thread)
            return old_thread

        self._threads.add(thread)

        return thread

    def _cache_events(self, thread, events):
        [self._cache_event(e) for e in events]
        self._events.update(set(events))
        # events.sort(lambda x: x.time)
        thread._events = add_events_to_cache(thread._events, events)

    def _cache_event(self, event):
        """Add an event to the cache

        Args:
            event (`Event`): The event to add
        """

        if event in self._events:
            old_event = self._events[self._events.index(event)]
            for name, value in vars(event).items():
                # if name not in ['is_read', 'name', 'width', 'height', 'pack', 'reactions'] and getattr(old_event, name) != value:
                #    raise ValueError("A (supposedly) immutable attribue was changed in a cached event: old={} ({}), new={} ({})".format(old, vars(old), new, vars(new)))
                setattr(old_event, name, value)
            return old_event

        self._events.add(event)

        return event

    def _cache_events(self, events, before=None, after=None):
        """Add multiple events to the cache

        Args:
            events (list): The `Event`\s to add
            before (int): ID of
            after (int):
        """

        [self._cache_event(e) for e in events]

        if before:
            events.prepend(Event(before))
        if after:
            events.append(Event(after))
        self._event_sequences.append(events)

        self._merge_sequences()
