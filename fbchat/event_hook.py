# -*- coding: UTF-8 -*-

class EventHook(object):
    """
    A simple implementation of the Observer-Pattern.
    All listeners added to this will be called, regardless of parameters
    """
    
    def __init__(self, *args):
        self._handlers = list(args)

    def add(self, handler):
        return self.__iadd__(handler)

    def remove(self, handler):
        return self.__isub__(handler)

    def __iadd__(self, handler):
        self._handlers.append(handler)
        return self

    def __isub__(self, handler):
        self._handlers.remove(handler)
        return self

    def __call__(self, *args, **kwargs):
        for handler in self._handlers:
            handler(*args, **kwargs)
