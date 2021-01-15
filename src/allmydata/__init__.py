"""
Decentralized storage grid.

community web site: U{https://tahoe-lafs.org/}
"""

__all__ = [
    "__version__",
    "full_version",
    "branch",
    "__appname__",
    "__full_version__",
]


def _get_version_with_fallback():
    try:
        from allmydata._version import __version__, full_version, branch
        return __version__, full_version, branch
    except ImportError:
        # We're running in a tree that hasn't run update_version, and didn't
        # come with a _version.py, so we don't know what our version is.  This
        # should not happen very often.
        return "unknown", "unknown", "unknown"

__version__, full_version, branch = _get_version_with_fallback()
__appname__ = "tahoe-lafs"

# __full_version__ is the one that you ought to use when identifying yourself
# in the "application" part of the Tahoe versioning scheme:
# https://tahoe-lafs.org/trac/tahoe-lafs/wiki/Versioning
__full_version__ = __appname__ + '/' + str(__version__)


# Install Python 3 module locations in Python 2:
from future import standard_library
standard_library.install_aliases()


# Monkey-patch 3rd party libraries:
from ._monkeypatch import patch
patch()
del patch
