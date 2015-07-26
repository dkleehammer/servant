
# Import the most common items to simplify URL handlers code.

from .connection import HttpProtocol
from .staticfiles import File
from .routing import route
from .middleware import middleware
from .middleware import register as register_middleware
