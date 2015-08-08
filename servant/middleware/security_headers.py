
from . import Middleware

class SecurityHeadersMiddlware(Middleware):
    def complete(self, ctx):
        # ctx.response.headers['Content-Security-Policy']   = "script-src 'self' 'unsafe-eval' ; style-src 'self' 'unsafe-inline'"
        ctx.response.headers['Strict-Transport-Security'] = 'max-age=8640000; includeSubDomains'
        ctx.response.headers['X-Frame-Options']           = 'DENY'
        ctx.response.headers['X-XSS-Protection']          = '1; mode=block'
