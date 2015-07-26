"""
Middleware to check page permissions against the users permissions in the session.
"""

import logging
from .middleware import Middleware
from .errors import HttpError

logger = logging.getLogger('permissions')

class PermissionsMiddleware(Middleware):
    """
    Checks the user against the current route's permissions.

    There are two hardcoded permissions (meaning they aren't in the DB so they
    don't show up in the management UI):

      - PUBLIC: public page anyone can access
      - USER: any logged in user can access
    """
    def __init__(self, allowed):
        """
        allowed
          All allowed permissions, checked using assertions in debug builds.
        """
        self.allowed = set(allowed)

    def register_route(self, route):
        required = route.route_keywords.get('permissions')
        if not required:
            raise Exception('No permissions set for route: %r' % route)

        route.permissions = set(required.split())

        if __debug__:
            unknown = route.permissions - self.allowed
            assert not unknown, "Route {!r} has invalid permissions: {}.".format(route, ','.join(unknown))


    def start(self, ctx):
        if not ctx.route:
            # This is going to be a 404
            return

        required = ctx.route.permissions
        if 'PUBLIC' in required:
            return

        # TODO: How do we know a user is logged in?  We can have a session
        # before two-factor is complete!

        if ctx.session and ctx.session.authenticated:
            if 'USER' in required:
                return

            if not ctx.session.permissions.isdisjoint(required):
                return

        logger.warning('AUTH-FAILURE: ctx=%s required=%s permissions=%s', ctx, required,
                       ctx.session and ctx.session.permissions or None)

        raise HttpError(403)

    def complete(self, ctx):
        pass
