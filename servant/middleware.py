
middleware = []
# All middlware registered, in the order it was registered.

def register(m):
    middleware.append(m)
