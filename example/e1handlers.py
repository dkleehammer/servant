
from datetime import datetime

from servant import route, staticfiles

@route('/', permissions='PUBLIC')
def index(ctx):
    return staticfiles.get('/static', 'index.html')

@route('/click', permissions='PUBLIC')
def click(ctx, counter, timestamp):
    print('COUNTER:', counter, type(counter))
    print('TIMESTAMP:', timestamp, type(timestamp))

    return {
        'counter': counter + 2,
        'timestamp': datetime.now()
    }
