from __future__ import unicode_literals
from .__meta__ import __version__, __version_info__  # noqa: F401
from .notify import *
from . import __version__ as vv
try:
    version = vv.version
except:
    pass
