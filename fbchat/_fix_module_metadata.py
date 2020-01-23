"""Everything in this module is taken from the excellent trio project.

Having the public path in .__module__ attributes is important for:
- exception names in printed tracebacks
- ~sphinx :show-inheritance:~
- deprecation warnings
- pickle
- probably other stuff
"""

import os


def fixup_module_metadata(namespace):
    def fix_one(qualname, name, obj):
        # Custom extension, to handle classmethods, staticmethods and properties
        if isinstance(obj, (classmethod, staticmethod)):
            obj = obj.__func__
        if isinstance(obj, property):
            obj = obj.fget

        mod = getattr(obj, "__module__", None)
        if mod is not None and mod.startswith("fbchat."):
            obj.__module__ = "fbchat"
            # Modules, unlike everything else in Python, put fully-qualitied
            # names into their __name__ attribute. We check for "." to avoid
            # rewriting these.
            if hasattr(obj, "__name__") and "." not in obj.__name__:
                obj.__name__ = name
                obj.__qualname__ = qualname
            if isinstance(obj, type):
                # Fix methods
                for attr_name, attr_value in obj.__dict__.items():
                    fix_one(objname + "." + attr_name, attr_name, attr_value)

    for objname, obj in namespace.items():
        if not objname.startswith("_"):  # ignore private attributes
            fix_one(objname, objname, obj)


# Allow disabling this when running Sphinx
# This is done so that Sphinx autodoc can detect the file's source
# TODO: Find a better way to detect when we're running Sphinx!
if os.environ.get("_FBCHAT_DISABLE_FIX_MODULE_METADATA") == "1":
    fixup_module_metadata = lambda namespace: None
