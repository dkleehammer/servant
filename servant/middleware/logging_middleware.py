
from . import Middleware
import logging
from time import perf_counter

logger = logging.getLogger('web')

class LoggingMiddleware(Middleware):
    def start(self, ctx):
        # The start and stop time should probably be part of the context anyway.
        ctx._log_timer_start = perf_counter()

    def complete(self, ctx):
        diff = perf_counter() - ctx._log_timer_start
        logger.info('%s status=%s time=%.7s seconds', ctx.url, ctx.response.status, diff)
