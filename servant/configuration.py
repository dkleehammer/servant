
def config(encode_hook=None, decode_hook=None):
    """
    Provides high-level configuration for the entire package.  It is not required; it is
    designed to allow customization.

    encode_hook
      A function that accepts a URL handler response as either a list or dictionary and JSON
      encodes it to a UTF-8 encoded string.  If not provided, json.dumps is used.

    decode_hook
      A JSON object hook (for json.loads(object_hook)) that is called for every object

      A function that accepts a Unicode JSON string and decodes it into a Python dictionary.
      If not provided, json.loads is used.

      A dictionary is required since it is used to populate URL handler arguments and we need
      to know the name of the argument each element should be assigned to.

    annotation_converter
      A function that post processes request variables (after the decode_hook, etc.) and
      optionally converts values based on Python argument annotations.

      This function is only called if the Route has annotations.  If so, the variables are
      passed as a mapping from argument name to value.

        func(route, map_arg_to_value) -> None

      If a value is to be converted, the new value should overwrite the old one in the map.
    """
    # Note: Push even if the value is None in case we're *restoring* the original value.  (I
    # don't see that being useful, but it would be expected if someone passed None on a second
    # call.)

    from .requests import Request
    Request._ohook = decode_hook

    from .responses import Response
    Response._ohook = encode_hook
