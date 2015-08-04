"""
Provides the Response object.
"""

import os
from . import errors
from .staticfiles import File
import json
from .lowerdict import LowerDict
import datetime

HTTP_COOKIE_PATH   = '/'
HTTP_COOKIE_SECURE = ''

# REVIEW: I was using the application version as an etag for the HTML,
# etc.  This will need to be switched to the SHA1 of each file or
# something.  (Would would mean we can't stream responses since we
# need the contents to create the etag.)
APP_VERSION = os.environ.get('APP_VERSION', None)
APP_VERSION_BYTES = APP_VERSION and APP_VERSION.encode('utf8') or None

CACHE_CONTROL_NEVER   = 'max-age=0, no-cache, no-store'
CACHE_CONTROL_HOUR    = 'private, max-age=3600'     # 1 hour
CACHE_CONTROL_FOREVER = 'private, max-age=31536000' # 1 year


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
        body = self._format_body(ctx)

        assert body is None or 'cache-control' in self.headers, 'status=%s body=%s headers=%s' % (self.status, type(self.body), ' '.join(self.headers.keys()))

        if body is not None:
            self.headers['content-length'] = len(body)

        status = self.status or (200 if body is not None else 204)

        assert body is None or 'content-length' in self.headers

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


    def _format_body(self, ctx):
        """
        Convert the response body into bytes and return it.

        This may update `self.status` and `self.headers`.
        """
        body = self.body

        if body is None:
            if self.status is None:
                self.status = 204
            return None

        if isinstance(body, dict) or isinstance(body, list):
            self.headers['content-type']  = 'application/json'
            self.headers['cache-control'] = CACHE_CONTROL_NEVER
            return json.dumps(body, default=Response._ohook).encode('utf8')

        if isinstance(body, File):
            # REVIEW: This is hardcoded.  We need an initialization
            # function or something to set things like this.
            if APP_VERSION and APP_VERSION != 'dev':
                self.headers['etag'] = APP_VERSION_BYTES

                if body.relpath.endswith('/index.html'):
                    self.headers['cache-control'] = CACHE_CONTROL_HOUR
                else:
                    self.headers['cache-control'] = CACHE_CONTROL_FOREVER

            else:
                # In development do not cache anything.
                self.headers['cache-control'] = CACHE_CONTROL_NEVER

            # (I've put this here so we get the cache-control header even on a
            # 304.  Is that right?)

            if APP_VERSION and APP_VERSION != 'dev':
                # If the browser has supplied a previous etag and it matches,
                # return a 304.
                oldetag = ctx.request.headers.get('if-none-match', None)
                if oldetag and body.etag == oldetag:
                    self.status = 304
                    return None

            self.headers['content-type'] = body.mimetype
            return body.content

        raise Exception('Unsupported data returned from handler: request={} data={} {!r}'.format(self, type(body), body))
