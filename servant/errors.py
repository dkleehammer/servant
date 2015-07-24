
# Remember, do not try to send user data back to the user in a message.  If they
# manage to sneak a '\r\n' into the data we'll have a header injection attack on
# our hands.

class HttpError(Exception):
    def __init__(self, code, url=None, message=None):
        assert isinstance(code, int)
        assert code in STATUSES, 'Invalid status {}'.format(code)
        assert code != 404 or url, 'Please provide the URL for 404s'
        Exception.__init__(self, message or str(STATUSES[code], 'utf8'))
        self.code = code
        self.url  = url


STATUSES = {
    100: b"Continue",
    101: b"Switching Protocols",
    102: b"Processing",
    103: b"199",
    200: b"OK",
    201: b"Created",
    202: b"Accepted",
    203: b"Non-Authoritative Information",
    204: b"No Content",
    205: b"Reset Content",
    206: b"Partial Content",
    207: b"Multi-Status",
    208: b"Already Reported",
    226: b"IM Used",
    300: b"Multiple Choices",
    301: b"Moved Permanently",
    302: b"Found",
    303: b"See Other",
    304: b"Not Modified",
    305: b"Use Proxy",
    307: b"Temporary Redirect",
    308: b"Permanent Redirect",
    400: b"Bad Request",
    401: b"Unauthorized",
    402: b"Payment Required",
    403: b"Forbidden",
    404: b"Not Found",
    405: b"Method Not Allowed",
    406: b"Not Acceptable",
    407: b"Proxy Authentication Required",
    408: b"Request Timeout",
    409: b"Conflict",
    410: b"Gone",
    411: b"Length Required",
    412: b"Precondition Failed",
    413: b"Payload Too Large",
    414: b"URI Too Long",
    415: b"Unsupported Media Type",
    416: b"Range Not Satisfiable",
    417: b"Expectation Failed",
    418: b"I'm A Teapot",        # ;)
    420: b"Enhance Your Calm",
    421: b"Misdirected Request",
    422: b"Unprocessable Entity",
    423: b"Locked",
    424: b"Failed Dependency",
    426: b"Upgrade Required",
    428: b"Precondition Required",
    429: b"Too Many Requests",
    431: b"Request Header Fields Too Large",
    500: b"Internal Server Error",
    501: b"Not Implemented",
    502: b"Bad Gateway",
    503: b"Service Unavailable",
    504: b"Gateway Timeout",
    505: b"HTTP Version Not Supported",
    506: b"Variant Also Negotiates",
    507: b"Insufficient Storage",
    508: b"Loop Detected",
    510: b"Not Extended",
    511: b"Network Authentication Required",
}
