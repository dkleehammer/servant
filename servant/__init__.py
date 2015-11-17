
# Import the most common items to simplify URL handlers code.

from .connection import HttpProtocol
from .staticfiles import File
from .routing import route
from .middleware import middleware
from .middleware import register as register_middleware
from .errors import HttpError

from ._version import get_versions
__version__ = get_versions()['version']
del get_versions
