# config/settings/__init__.py

try:
    from .local import *  # noqa
except ImportError:
    pass

from .base import *  # noqa