
# An HttpProtocol is created when a connection is received and is deleted when
# the connection is closed.
#
# As soon as it is created we start accepting data.  When a complete request is
# received we create a Request object and launch it on its own using
# asyncio.async.  When the request completes, it must call back into the
# protocol so it can continue parsing the next request.  If your handler never
# calls a completing method (e.g. request.complete_with_content) then a
# connection timeout (a TCP/IP timeout or our background reaper) will eventually
# clean up, but this is not ideal.
#
# I'm trying to keep the logic in Request to make it easier to make it generic
# and subclassable later.  (For now, I'm hardcoding our application Logic there
# though.)

# TODO: Reaper
# TODO: Handle connection close

import re, logging, inspect
from asyncio import Protocol, coroutine, async

from . import errors
from .errors import HttpError
from . import routing
from .contexts import Context
from .requests import Request
from .lowerdict import LowerDict
from .middleware import middleware

logger = logging.getLogger('web')

MAX_HEADERS = 1024 * 6
RE_REQUEST_LINE  = re.compile(r'(GET|POST|PUT|DELETE) [ ]+ (\S+) [ ]+ HTTP/1.1 [ ]* \r\n', re.VERBOSE)

_STATE_IDLE             = 0
_STATE_READING_HEADERS  = 1
_STATE_READING_CONTENT  = 2
_STATE_HANDLING_REQUEST = 3

_STATE_NAMES = { v: k for (k,v) in globals().items() if k.startswith('_STATE_') }

class HttpProtocol(Protocol):

    _next_id = 1

    def __init__(self):
        Protocol.__init__(self)

        self._id = HttpProtocol._next_id
        HttpProtocol._next_id += 1

        self.ip = None
        # The IP4 address we are directly connected to.

        self.buffer = b''

        self.state = _STATE_READING_HEADERS

        self.transport = None
        # Set to the transport while we are connected.  Once we close the
        # connection or it is closed on us, we set this back to None.

        self.headers = None
        # Contains the method line and all headers (everything up to the first
        # blank line).

        self.request_length = None
        # The content length of the request.

        self.method  = None
        self.url     = None
        self.match   = None
        self.route   = None
        self.ctx = None # The current request we are handling

    def connection_made(self, transport):
        assert self.ip is None

        self.transport = transport

        peername = transport.get_extra_info('peername')
        self.debug('Connection from %s', peername)

        if isinstance(peername, tuple) and len(peername) == 2:
            # An IP4 address.
            self.ip = peername[0]

        self.state = _STATE_READING_HEADERS

    def debug(self, msg, *args, exc_info=None):
        logger.debug(msg, *args, exc_info=exc_info)

    def error(self, msg, *args, exc_info=None):
        logger.error(msg, *args, exc_info=exc_info)

    def connection_lost(self, exc):
        self.debug('connection_lost')
        self.transport = None

    def data_received(self, data):
        # data: Bytes
        self.buffer += data
        self.debug('data_received')
        self._process_buffer()

    def _process_buffer(self):
        self.debug('_process_buffer')
        if self.state == _STATE_READING_HEADERS:
            parts = self.buffer.split(b'\r\n\r\n', 1)

            if len(parts[0]) > MAX_HEADERS:
                # (By putting the check here we check the length when the
                # end-of-headers has been found and when it hasn't.)
                self.error('Headers too large: length=%s', len(parts[0]))
                raise HttpError(431)

            if len(parts) == 1:
                # Haven't seen the end-of-headers yet.
                return

            self.buffer = parts[1]

            self.method, self.url, headers = self.parse_start_line(parts[0])
            self.headers = self.parse_headers(headers)

            self.request_length = int(self.headers.get('content-length', 0))

            self.state = _STATE_READING_CONTENT

        if self.state == _STATE_READING_CONTENT and len(self.buffer) >= self.request_length:
            # Remember, if multiple requests are pipelined there can be *more*
            # data in the buffer than the content length.

            body = self.buffer[:self.request_length]
            self.buffer = self.buffer[self.request_length:]

            self.state = _STATE_HANDLING_REQUEST
            self.handle_request(body)


    def parse_start_line(self, buffer):
        line, headers = buffer.split(b'\r\n', 1)

        tokens = line.split(None)
        # method url HTTP/1.1
        if len(tokens) != 3 or tokens[0] not in (b'GET', b"POST", b'PUT', b'DELETE'):
            self.error('Invalid start line: "%s"', line)
            raise HttpError(400)

        # TODO: Decode the URL

        method = str(tokens[0], encoding='ascii')
        url    = str(tokens[1], encoding='ascii')

        return method, url, headers


    def parse_headers(self, raw):
        raw = str(raw, encoding='ascii')

        headers = LowerDict()

        for line in raw.split('\r\n'):
            parts = line.split(':', 1)
            if len(parts) != 2 or not len(parts[0]) or ' ' in parts[0]:
                # The specification says we must reject the request if there is
                # space before the colon.  I don't know of any header namesthat
                # contain spaces, so we'll simply reject if there are any spaces
                # in the name at all.
                #
                # Note that we also do not accept continuation lines.  Either
                # there won't be a ':' or there will be a leading space, either
                # of which cause us to reject.  The HTTP 1.1 specification
                # recommends we reject continuation lines.
                self.error('Invalid header "%r".  headers="%r"', line, raw)
                raise HttpError(400)

            headers[parts[0].lower()] = parts[1].strip()

        return headers


    def handle_request(self, body):

        # It doesn't seem possible to use async (ensure_future) and pass
        # parameters.  I guess we have to first launch a function with no
        # parameters that then yields to the one we want.  I've put the handler
        # into the request.

        self.route, self.match = routing.get(self.url)

        ip = self.headers.get('X-Forwarded-For', self.ip)

        request = Request(self, self.method, self.url, self.headers, body)
        self.ctx = Context(self.route, request, ip)

        async(self._handle_request_coroutine())


    @coroutine
    def _handle_request_coroutine(self):
        ctx = self.ctx

        # TODO: Errors are not going through the context and middleware.

        try:
            for m in middleware:
                result = m.start(ctx)
                if result and inspect.isgenerator(result):
                    # The middleware function is a generator.
                    yield from result

            if not self.route:
                raise HttpError(404, ctx.url)

            ctx.response.body = yield from self.route(self.match, ctx)

        except HttpError as ex:
            ctx.response.status = ex.code
            self.error('HTTP error %s %s url=%s', ex.code, str(ex), ctx.url)
            self._complete_with_error(ex.code)

        except:
            ctx.response.status = 500
            self.error('Unhandled error in %s', self.route, exc_info=True)
            self._complete_with_error(500)

        for m in reversed(middleware):
            result = m.complete(ctx)
            if result and inspect.isgenerator(result):
                # The middleware function is a generator.
                yield from result

        try:
            ctx.response._send(ctx, self.transport)
        except:
            # An error happened while we were sending.  (Try to do as little as
            # possible in _send so there is less chance of getting an exception
            # there.)  At this point our best bet is to abort.
            logger.error('An error occurred while trying to send: %r', ctx, exc_info=True)

        # Reset everything
        self.state = _STATE_READING_HEADERS

        self.request_length = None
        self.method  = None
        self.url     = None
        self.headers = None
        self.route   = None
        self.match   = None # Can we put this into the route or request?
        self.ctx     = None

        if self.buffer:
            self._process_buffer()

    def eof_received(self):
        pass

    def complete(self, code, headers=None, body=None):
        if not self.transport:
            # Already disconnected.
            return

        assert isinstance(code, int)
        assert code != 204 or body is None, '204 cannot have body'

        response = [
            b'HTTP/1.1 ' + bytes(str(code), 'ascii') + b' ' + errors.STATUSES[code],
            b'Content-Length: ' + (b'0' if not body else bytes(str(len(body)), 'ascii')),
        ]

        if headers:
            assert all(isinstance(h, bytes) for h in headers), repr(headers)
            # We provide content-length
            assert all(b'content-length:' not in h.lower() for h in headers)
            response.extend(headers)

        response.append(b'')

        if body:
            assert isinstance(body, bytes), 'Forgot to convert body to bytes: {!r}'.format(body)
            response.append(body)

        response = b'\r\n'.join(response)

        self.transport.write(response)

        # Don't reset flags yet.  Wait until the handler returns in
        # _handle_request_coroutine

    def _complete_with_error(self, code):
        # You should have already logged the error.
        self.complete(code)
