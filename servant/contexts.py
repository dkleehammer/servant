"""
The context object stores all of the information in the request and the
response.  It provides convenience methods to "pass-through" to those objects.
"""

from .responses import Response

class Context:
    """
    A Context encapsulates the request and response objects and provides
    convenience methods.  Contexts are passed to middleware and to request
    handlers.

    A new Context is created for each request.

    Handlers normally just return the data they want sent to the browser, but
    they may also set the response status, headers, cookies, etc.
    """
    def __init__(self, route, request, ip):
        self.route = route
        # The route handling this request.

        self.request = request
        self.response = Response()

        self.ip = ip
        # The most likely address of the client.  If an X-Forwarded-For header
        # is present it is used.  Otherwise the address of the actual connection
        # is used.  Note that there is no way to ensure this is valid so be
        # careful when using it.

    def __repr__(self):
        return repr(self.request)

    @property
    def headers(self):
        """
        The dictionary of request headers.  This dictionary always lowercases keys.

        This is a convenience property that returns ctx.request.headers.
        """
        return self.request.headers

    @property
    def url(self):
        """
        The request URL.

        This is a convenience property that returns ctx.request.url.
        """
        return self.request.url

    # def create_session(self, user_id=None, auth_status=None, login=None, name=None):
    #     """
    #     Creates a new session-id and Session object and sets the 'sid' response
    #     cookie.
    #
    #     This should only be used when the user is logging in.  This cannot be
    #     used with a user that is already logged in.
    #     """
    #     assert self.session is None, 'There is already a session-id assigned to this context'
    #
    #     self.sid = genrandom(20)
    #     self.session = Session(id=self.sid, user_id=user_id, login=login, auth_status=auth_status,
    #                            name=name)
    #     self.set_cookie('sid', self.sid)

    @property
    def user_id(self):
        return self.session and self.session.user_id

    # def delete_session(self):
    #     """
    #     Marks the session for deleting and deletes the "sid" cookie.
    #
    #     The session middleware is response for actually deleting the session and
    #     the end of request processing.
    #     """
    #     if self.session:
    #         assert self._deleted_session is None, 'There is already a deleted session!'
    #         self._deleted_session = self.session
    #         self.session = None
    #
    #     self.delete_cookie('sid')
    #     self.sid = None

    def set_cookie(self, name, value, http_only=True):
        """
        Sets a response cookie.

        This is a convenience method that calls ctx.response.set_cookie.
        """
        self.response.set_cookie(name, value, http_only=http_only)

    def delete_cookie(self, name):
        """
        Deletes a cookie by settings its expiration date in the past.

        This is a convenience method that calls ctx.response.delete_cookie.
        """
        self.response.delete_cookie(name)

