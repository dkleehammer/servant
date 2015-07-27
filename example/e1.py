#!/usr/bin/env python3

from os.path import abspath, dirname, join
root = dirname(abspath(__file__))

# Add the lib directory to the sys.path
import sys
sys.path.insert(0, dirname(root))

import asyncio
from servant import HttpProtocol, staticfiles, register_middleware

def main():
    loop = asyncio.get_event_loop()
    loop.set_debug(True)

    from servant.permissions import PermissionsMiddleware
    from servant.security_headers import SecurityHeadersMiddlware
    from servant.logging_middleware import LoggingMiddleware

    register_middleware(PermissionsMiddleware(['USER', 'PUBLIC', 'test']))

    register_middleware(SecurityHeadersMiddlware())
    register_middleware(LoggingMiddleware())

    staticfiles.serve_prefix('/static', join(root, 'static'), permissions='PUBLIC')
    staticfiles.serve_prefix('/generated', join(root, 'generated'), permissions='PUBLIC')

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



if __name__ == '__main__':
    main()
