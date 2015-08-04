#!/usr/bin/env python3

from os.path import abspath, dirname, join
root = dirname(abspath(__file__))

# Add the lib directory to the sys.path
import sys
sys.path.insert(0, dirname(root))

import asyncio
from servant import HttpProtocol, staticfiles, register_middleware

from datetime import datetime

def main():
    loop = asyncio.get_event_loop()
    loop.set_debug(True)

    from servant.security_headers import SecurityHeadersMiddlware
    from servant.logging_middleware import LoggingMiddleware
    register_middleware(SecurityHeadersMiddlware())
    register_middleware(LoggingMiddleware())

    staticfiles.serve_prefix('/static', join(root, 'static'))
    staticfiles.serve_prefix('/generated', join(root, 'generated'))

    from servant import configuration
    configuration.config(decode_hook=_json_load_object_hook, encode_hook=_json_save_hook)

    import e1handlers

    port = 8000
    coro = loop.create_server(HttpProtocol, host='127.0.0.1', port=port)
    server = loop.run_until_complete(coro)
    print('listening on port', port)

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass

    server.close()
    loop.run_until_complete(server.wait_closed())
    loop.close()


def _json_load_object_hook(d):
    n = d.get('__dt')
    if type(n) is int:
        return datetime.fromtimestamp(n / 1000)
    return d


def _json_save_hook(obj):
    if type(obj) is datetime:
        return { '__dt' : obj.timestamp() * 1000 }
    raise TypeError()

if __name__ == '__main__':
    main()
