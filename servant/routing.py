"""
Provides the @route decorator and its implementation.

The decorator creates a Route object, defined here, and stores it in the global
list of routes (`_routes`).  There is also a lookup function to find the
appropriate route for a URL.
"""

import re, inspect
from urllib.parse import urlparse
from asyncio import coroutine

from .middleware import middleware

_routes = []
# The global list of registered routes as Route objects.

def route(pattern, **kwargs):
    """
    The @route decorator used to register URL handlers.  The first parameter of the decorated
    function should be named "ctx".

    pattern
      The pattern for the URL the decorated function will handle.

      Wrap a component of the path in braces to mark it as a variable ("/file/{filename}").
      The decorated function must take a parameter with this name.
    """
    def wrapper(func):
        # # We'll apply the @coroutine so we don't need two decorators.
        # assert not inspect.isgenerator(func) and not inspect.iscoroutine(func)
        assert not any(r.pattern == pattern for r in _routes), 'URL "{}" registered twice: first={} second={}'.format(pattern, _routes[pattern], func)

        r = Route(pattern, func, kwargs)
        for m in middleware:
            m.register_route(r)

        _routes.append(r)
    return wrapper


def get(url):
    """
    Given a URL, find the Route that handles it.

    If found, a tuple containing the Route object and the regular expression match used to
    match the pattern is returned.  If there are variables in the URL, the match will have a
    group for each in the order they are found in the URL.

    If not found, (None, None) is returned.
    """
    url = urlparse(url)

    for r in _routes:
        match = r.regexp.match(url.path)
        if match:
            return (r, match)

    return (None, None)


class Route:
    """
    A route mapping, created by the @route decorator, that maps from a URL
    pattern (e.g. "/static/js/{filename}") to a URL handler function to call.

    This object is callable like a function and will pick the arguments to the
    URL handler from the request (GET variables, JSON variables, etc.)
    """
    def __init__(self, pattern, func, kwargs):
        """
        pattern: The URL regexp.
        func: The URL handler callback.
        """
        self.pattern = pattern
        self._func = func
        self.func = coroutine(func)
        self.route_keywords = kwargs

        self.regexp = None

        self.urlvars = []
        # The names of variables to be parsed from the URL, in the order they
        # appear in the pattern.  There is a group for each in `self.regexp` so
        # all we have to do is get all of the groups.

        self.formvars = []
        # The names of variables we expect to find in vars variables or a JSON
        # object (depending on the content-type).  These are the URL handler
        # parameters that are not variables in the URL pattern.

        self.analyze_pattern()
        self.analyze_params()

    def analyze_params(self):
        """
        Analyzes the URL handlers parameters to determine which should come from URL
        variables and which are expected to be in the body.
        """
        params = inspect.getargspec(self._func).args
        assert params[0] == 'ctx', 'The first parameter is not `ctx`.  pattern={} callback={}'.format(self.pattern, self._func)

        params = set(params[1:])
        self.formvars = params - set(self.urlvars)

    def analyze_pattern(self):
        """
        Creates a regular expression from the pattern for matching URLs.
        """
        # Split the URL by slashes and examine each part.  Each could be either
        # plan text (e.g. "static") or a variables (e.g. "{filename}").

        regexps  = []
        varnames = []

        assert self.pattern.startswith('/'), 'Route patterns must start with "/": {!r}'.format(self.pattern)

        for part in self.pattern.rstrip('/').split('/'):
            if part.startswith('{') and part.endswith('}'):
                # variable
                varnames.append(part[1:-1])
                regexps.append('([^/]+)')
            else:
                # plain text
                regexps.append(re.escape(part))

        regexp = '^' + '/'.join(regexps) + '/?$'

        self.regexp = re.compile(regexp)
        self.urlvars = varnames

    @coroutine
    def __call__(self, match, ctx):
        """
        Calls the URL handler, passing any defined parameters.
        """
        args = {
            'ctx': ctx
        }

        if self.urlvars:
            args.update(zip(self.urlvars, match.groups()))

        if self.formvars:
            assert ctx.request.form, 'No variables: %r' % ctx
            args.update({ name: ctx.request.form.get(name, None) for name in self.formvars })

        result = yield from self.func(**args)
        return result

    def __repr__(self):
        return 'Route<{} {}>'.format(self.pattern, self._func)

