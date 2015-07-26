
from servant import route, staticfiles

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
