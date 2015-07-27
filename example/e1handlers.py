
from servant import route, staticfiles

@route('/', permissions='PUBLIC')
def index(ctx):
    return staticfiles.get('/static', 'index.html')

@route('/click', permissions='PUBLIC')
def click(ctx, counter):
    print('COUNTER:', counter, type(counter))

    return {
        'counter': counter + 2
    }
