#!/usr/bin/env python3

from os.path import abspath, dirname, join
root = dirname(abspath(__file__))

# Add the lib directory to the sys.path
import sys
sys.path.insert(0, dirname(root))

import asyncio
from servant import route, HttpProtocol, staticfiles

def main():
    loop = asyncio.get_event_loop()
    loop.set_debug(True)

    staticfiles.register_key('static', join(root, 'static'))
    staticfiles.register_key('generated', join(root, 'generated'))

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


@route('/', permissions='PUBLIC')
def index(ctx):
    return staticfiles.get('static', 'index.html')

@route('/static/{dir}/{filename}', permissions='PUBLIC')
def staticfile(ctx, dir, filename):
    return staticfiles.get('static', dir + '/' + filename)

@route('/generated/{filename}', permissions='PUBLIC')
def generatedfile(ctx, filename):
    return staticfiles.get('generated', filename)

@route('/click', permissions='PUBLIC')
def click(ctx, counter):
    print('COUNTER:', counter, type(counter))

    return {
        'counter': counter + 2
    }


if __name__ == '__main__':
    main()
