
middleware = []
# All middlware registered, in the order it was registered.

def register(m):
    middleware.append(m)


class Middleware:
    """
    A base class for middleware, primarily for documentation.  You do
    not need to call the base class methods from your subclass.
    """
    def register_route(self, route):
        pass

    def start(self, ctx):
        """
        Called at the beginning of request handling.

        This can be a normal function or a coroutine.
        """
        pass

    def complete(self, ctx):
        """
        Called at the end of request handling.

        This can be a normal function or a coroutine.
        """
        pass
