
# pylint: disable=unidiomatic-typecheck
#
# For performance we only do some exact checks.  We don't expect subclasses of
# Python's built-in date object and we know the decoder is going to give us a
# plain dictionary.

import json
from datetime import date

class CustomEncoder(json.JSONEncoder):

    # pylint: disable=method-hidden
    #
    # I'm not sure what pylint is complaining about, but I think it has this
    # backwards.  We are overriding a method but it seems to think the original
    # is going to override us.

    def default(self, obj):
        # if isinstance(obj, pglib.Row):
        #     return dict(zip(obj.columns, obj))
        if type(obj) is date:
            return { '_date': obj.isoformat() }
        # TODO: implement `datetime`
        if isinstance(obj, set):
            return list(obj)
        return json.JSONEncoder.default(self, obj)

def dumps(obj):
    """
    Our wrapper around the standard library's json.dumps to add support for custom data types.
    """
    return json.dumps(obj, cls=CustomEncoder, separators=(',', ':'))

def loads(s):
    """
    Our wrapper around the standard library's json.loads to add support for custom data types.
    """
    return json.loads(s, object_hook=_custom_decoder)

def _custom_decoder(obj):
    if type(obj) is dict and '_date' in obj:
        s = obj['_date']
        return date(int(s[0:4]), int(s[5:7]), int(s[8:10]))
    return obj
