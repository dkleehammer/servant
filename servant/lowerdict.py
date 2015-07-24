
class LowerDict(dict):
    """
    A dictionary subclass that lowercases all keys.
    """
    def __setitem__(self, key, value):
        return dict.__setitem__(self, key.lower(), value)

    def __getitem__(self, key):
        return dict.__getitem__(self, key.lower())

    # REVIEW: Do we need to subclass `get` also or does __getitem__ handle that?
