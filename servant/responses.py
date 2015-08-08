"""
Provides the Response object.
"""

import os, logging, gzip
from . import errors
from .staticfiles import File
from .lowerdict import LowerDict

# TODO:: Need to enable way to make this secure.
HTTP_COOKIE_PATH   = '/'
HTTP_COOKIE_SECURE = ''

logger = logging.getLogger('servant')

def itob(n):
    """
    Int to bytes
    """
    return bytes(str(n), 'ascii')


class Response:
    """
    Encapsulates the response to send to the client.

    A URL handler does not have to interact with this object - it can simply
    return the value to send.  However, it may set the status, headers, cookies,
    or the body.
    """

    _ohook = None
    # The JSON encoding hook (json.dumps(default=xx)).  Set this using
    # configuration.config(encode_hook).

    def __init__(self):
        self.status  = None
        self.headers = LowerDict()
        self.cookies = {}
        self.body    = None

    def set_cookie(self, name, value, http_only=True):
        """
        Sets a response cookie
        """
        assert isinstance(name, str)
        assert isinstance(value, str)
        self.cookies[name] = '{}{}'.format(value, http_only and '; HttpOnly' or '')

    def delete_cookie(self, name):
        """
        Deletes a cookie by setting the expiration date to a time in the past.
        """
        assert isinstance(name, str)
        self.cookies[name] = 'deleted; Expires=Thu, 01-Jan-1970 00:00:01 GMT; HttpOnly'

    def _send(self, ctx, transport):
        """
        Called at the end of processing to send response to the browser.  Do not
        call this from a URL handler.
        """
        status = self.status
        body   = self.body

        if type(body) not in (type(None), bytes):
            # (In development, assert which will raise an exception.  If it gets out of
            # development, log it and return an error to the browser.)
            logger.error('Response is not bytes: {} {!r}'.format(type(body), body))
            raise AssertionError('Response is not bytes: {} {!r}'.format(type(body), body))
            status = 500
            body   = None

        if not status:
            if body is None:
                status = 204
            else:
                status = 200

        if body is not None:
            self.headers['content-length'] = str(len(body))

        if __debug__:
            for key, val in self.headers.items():
                assert type(val) is str, 'Header %s value is not a string: val=%r type=%s' % (key, val, type(val))

        headers = '\r\n'.join('{}: {}'.format(k,v) for k,v in self.headers.items())

        parts = [
            b'HTTP/1.1 ', itob(status), b' ', errors.STATUSES[status], b'\r\n',
            headers.encode('utf8'),
        ]

        if self.cookies:
            cs = [ 'Set-Cookie: {}={}; path={}{}'.format(key, val, HTTP_COOKIE_PATH, HTTP_COOKIE_SECURE)
                   for (key, val) in self.cookies.items() ]
            parts.append(b'\r\n')
            parts.append('\r\n'.join(cs).encode('utf8'))

        parts.append(b'\r\n\r\n')

        if body:
            parts.append(body)

        transport.writelines(parts)
