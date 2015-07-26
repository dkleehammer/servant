"""
Session middleware that loads the session data if the ctx has a
session-id.  Saves the session afterwards.
"""

import pickle, logging, os
from foundation import db

logger = logging.getLogger("session")

_CHECK_IP = (os.environ.get('CHECK_IP', 'true').lower() == 'false')
# Normally we ensure that the IP address from the context (from X-Forwarded-For)
# matches that in the sessions table.  This is here so we can disable the check
# (in the config file set "CHECK_IP=false") if something goes wrong with the proxies.


AUTH_STATUS_NOT_LOGGED_IN = 0
AUTH_STATUS_OTP_REQUIRED  = 1
AUTH_STATUS_COMPLETE      = 2

_AUTH_STATUS = ['none', 'otp', 'complete']

class SessionData:
    """
    Holds arbitrary data that will be pickled and stored in the sessions table.
    This is basically a dictionary that allows us to use a "." to access
    variables.
    """
    def __setattr__(self, name, value):
        self.__dict__[name] = value


class Session:
    """
    The session-object available on the ctx.  At the end of each ctx all
    attributes are serialized to the sessions table.

    Note that requesting an allowed value always returns None - it never raises
    an exception.
    """

    def __init__(self, id=None, user_id=None, login=None, name=None, auth_status=None, data=None):
        self.id          = id
        self.user_id     = user_id
        self.login       = login
        self.name        = name
        self.auth_status = auth_status

        self.data = SessionData()
        if data:
            self.data.__dict__.update(data)

        self.isnew = (data is None)

        assert (user_id and login and name and auth_status), repr(self)

    @property
    def authenticated(self):
        return self.auth_status == AUTH_STATUS_COMPLETE

    def __repr__(self):
        return 'Session: id={} user={} login={} auth={} data={!r}'.format(
            self.id, self.user_id, self.login, _AUTH_STATUS[self.auth_status], self.data)


class SessionMiddleware:

    # Do not accept a session-id if we don't have a matching session in the
    # database.  It is a way for attackers to pin a cookie in someone's
    # browser.  The attacker already knows the session-id value and can later
    # hijack the session after the user logs in.  If we see a session-id we
    # don't know, ignore the cookie and do not create a session.
    #
    # Similarly, once a user logs in, always generate a new session-id.

    def start(self, ctx):
        sid = ctx.sid
        if not sid:
            logger.debug('%s: no session-id', ctx)
            return

        row = yield from db.row(
            """
            select s.session_data, s.user_id, s.ip_address, s.auth_status,
                   u.login, u.name
              from sessions s
              join users u on u.user_id = s.user_id
             where s.sid=%s
            """, sid)

        if not row:
            logger.error('%s: session-id %r not in the database', ctx, sid)
            ctx.delete_cookie('sid')
            return

        if _CHECK_IP and ctx.ip != row.ip_address:
            # We're comparing the IP address from the request with the one
            # logged in with in an attempt to tie the session to the user's
            # computer.  Obviously this isn't foolproof since we rely on the
            # X-Forwarded-For header which can easily be faked, but it is a
            # start.
            logger.error('SECURITY: sid %s (%s) logged in from IP %s but this request is from %s',
                         sid, row.user_id, row_ipaddress, ctx.ip)
            return

        try:
            # PERFORMANCE: pickle.loads() might be inefficient.  There is a
            # Pickler class.  See what loads() actually does.  If this is fine,
            # delete this comment.
            data = pickle.loads(row.session_data)
            ctx.session = Session(id=ctx.sid, user_id=row.user_id, login=row.login,
                                  name=row.name, auth_status=row.auth_status, data=data)
            logger.debug('%s: loaded session', ctx)
        except:
            logger.error('%s: Unable to restore prev_pickled session data', ctx, exc_info=True)
            row = yield from db.execute("delete from sessions where sid=%s", sid)
            raise Exception("Unable to restore previous session data")

    def complete(self, ctx):
        if ctx._deleted_session:
            logger.debug('%s: deleting session', ctx)
            yield from db.execute("delete from sessions where sid=%s", ctx.sid)

        session = ctx.session

        if session:
            data = pickle.dumps(session.data.__dict__, -1)
            if session.isnew:
                logger.debug('%s: saving new session', ctx)
                yield from db.execute(
                    """
                    insert into sessions(sid, auth_status, user_id, ip_address,
                                         session_data, login_time, last_activity_time)
                    values (%s, %s, %s, %s, %s, localtimestamp, localtimestamp)
                    """,
                    ctx.session.id, ctx.session.auth_status, ctx.session.user_id,
                    ctx.ip, data)
            else:
                logger.debug('%s: updating session', ctx)
                count = (yield from db.execute(
                    """
                    update sessions set
                           auth_status=%s,
                           session_data=%s,
                           last_activity_time = localtimestamp
                     where sid = %s
                       and user_id = %s
                    """, ctx.session.auth_status, data, ctx.sid, ctx.session.user_id))
                assert count == 1, 'Session was not updated: sid=%s uid=%s' % (ctx.sid, ctx.session.user_id)
