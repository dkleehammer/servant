
from servant import File
from servant.middleware import Middleware

class ResponseMiddleware(Middleware):
    """
    Examines URL handler responses and converts them to bytes if necessary.
    """
    def complete(self, ctx):

        response = ctx.response

        if response.status:
            return

        body = response.body

        if body is None:
            response.status = 204
            return

        if isinstance(body, dict) or isinstance(body, list):
            response.status = 200
            response.body   = json.dumps(body, default=Response._ohook).encode('utf8')
            response.headers['content-type']   = 'application/json'
            response.headers['content-length'] = len(body.content)
            return

        if isinstance(body, File):
            if body.etag and body.etag == ctx.request.headers.get('if-none-match', None):
                response.status = 304
                response.body   = None
                return

            if body.etag:
                response.headers['etag'] = file.etag

            response.body = body.content
            response.headers['content-type']   = body.mimetype
            response.headers['content-length'] = len(body.content)

            return

        if typeof(body) is not bytes:
            raise Exception('Response is not bytes: ctx=%s resp=%s' % (ctx, body))
