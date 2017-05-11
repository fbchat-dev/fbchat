import inspect


class EventHook(object):
    """
    A simple implementation of the Observer-Pattern.
    The user can specify an event signature upon inizializazion,
    defined by kwargs in the form of argumentname=class (e.g. id=int).
    The arguments' types are not checked in this implementation though.
    Callables with a fitting signature can be added with += or removed with -=.
    All listeners can be notified by calling the EventHook class with fitting
    arguments.
    
    Thanks http://stackoverflow.com/a/35957226/5556222
    """

    def __init__(self, **signature):
        self._signature = signature
        self._argnames = set(signature.keys())
        self._handlers = []

    def _kwargs_str(self):
        return ", ".join(k+"="+v.__name__ for k, v in self._signature.items())

    def __iadd__(self, handler):
        params = inspect.signature(handler).parameters
        valid = True
        argnames = set(n for n in params.keys())
        if argnames != self._argnames:
            valid = False
        for p in params.values():
            if p.kind == p.VAR_KEYWORD:
                valid = True
                break
            if p.kind not in (p.POSITIONAL_OR_KEYWORD, p.KEYWORD_ONLY):
                valid = False
                break
        if not valid:
            raise ValueError("Listener must have these arguments: (%s)"
                             % self._kwargs_str())
        self._handlers.append(handler)
        return self

    def __isub__(self, handler):
        self._handlers.remove(handler)
        return self

    def __call__(self, *args, **kwargs):
        if args or set(kwargs.keys()) != self._argnames:
            raise ValueError("This EventHook must be called with these " +
                             "keyword arguments: (%s)" % self._kwargs_str() +
                             ", but was called with: (%s)" %self._signature)
        for handler in self._handlers[:]:
            handler(**kwargs)

    def __repr__(self):
        return "EventHook(%s)" % self._kwargs_str()
