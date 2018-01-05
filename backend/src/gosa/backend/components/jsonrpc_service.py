# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

"""
The JSONRPC implementation consists of a GOsa backend plugin (*JSONRPCService*)
and a WSGI application (*JsonRpcApp*). The first is implemented as a handler
plugin, so it is going to be invoked on agent startup. It takes care of
registering the WSGI application to the
:class:`gosa.backend.compoments.httpd.HTTPService`.

------
"""
import sys
import uuid
import traceback
import logging
import tornado.web
import time

from gosa.backend.objects.index import UserSession
from gosa.common.env import make_session
from gosa.common.hsts_request_handler import HSTSRequestHandler
from tornado.gen import coroutine, is_future
from gosa.common.gjson import loads, dumps
from gosa.common.utils import f_print, N_
from gosa.common.error import GosaErrorHandler as C
from gosa.common import Environment
from gosa.common.components import PluginRegistry, JSONRPCException
from gosa.common.components.auth import *
from gosa.backend import __version__ as VERSION
from gosa.backend.lock import GlobalLock
from gosa.backend.utils.ldap import check_auth
from gosa.backend.exceptions import FilterException
from gosa.common.components.command import no_login_commands
import hashlib


# Register the errors handled  by us
from tornado.concurrent import Future

C.register_codes(dict(
    INVALID_JSON=N_("Invalid JSON string '%(data)s'"),
    JSON_MISSING_PARAMETER=N_("Parameter missing in JSON body"),
    PARAMETER_LIST_OR_DICT=N_("Parameter must be list or dictionary"),
    INDEXING=N_("Index rebuild in progress - try again later"),
    REGISTRY_NOT_READY=N_("Registry is not ready")
    ), module="gosa.backend")


class JsonRpcHandler(HSTSRequestHandler):
    """
    This is the tornado request handler which is responsible for serving the
    :class:`gosa.backend.command.CommandRegistry` via HTTP/JSONRPC.
    """

    # denial service for some time after login fails to often
    __dos_manager = {}

    def initialize(self):
        self.dispatcher = PluginRegistry.getInstance('CommandRegistry')
        self.env = Environment.getInstance()
        self.log = logging.getLogger(__name__)
        self.ident = "GOsa JSON-RPC service (%s)" % VERSION

    def get(self):
        """Allow the clients to get the XSRF cookie"""
        # trigger the token generation
        self.xsrf_token
        self.write("")

    @coroutine
    def post(self):
        try:
            resp = self.process(self.request.body)
        except ValueError as e:
            self.clear()
            self.set_status(400)
            self.finish(str(e))
        except tornado.web.HTTPError as e:
            self.clear()
            self.set_status(e.status_code) 
            self.finish(e.log_message)
            raise e
        except FilterException as e:
            self.clear()
            self.set_status(500)
            error = dict(
                name='JSONRPCError',
                code=100,
                message=str(e),
                error=str(e)
            )
            self.finish(dumps(dict(result=None, error=error, id=None)))
            raise e
        else:
            if is_future(resp['result']):
                resp['result'] = yield resp['result']

            self.write(dumps(resp))
            self.set_header("Content-Type", "application/json")

    def get_lock_result(self, user):
        cls = self.__class__
        if user in cls.__dos_manager:
            # time to wait until login is allowed again
            login_stats = cls.__dos_manager[user]
            ttw = pow(4, login_stats['count'])
            ttw += login_stats['timestamp']
            print("%s > %s == %s" % (ttw, time.time(), ttw > time.time()))
            if ttw > time.time():
                self.log.info("login for user '%s' is locked. Login from host %s" % (user, self.request.remote_ip))
                return {
                    'state': AUTH_LOCKED,
                    'seconds': int(ttw)
                }
        return None

    def process(self, data):
        """
        Process an incoming JSONRPC request and dispatch it thru the
        *CommandRegistry*.

        ================= ==========================
        Parameter         Description
        ================= ==========================
        data              Incoming body data
        ================= ==========================

        ``Return``: varries
        """
        try:
            json = loads(data)
        except ValueError as e:
            raise ValueError(C.make_error("INVALID_JSON", data=str(e)))

        try:
            method = json['method']
            params = json['params']
            jid = json['id']
        except KeyError as e:
            raise ValueError(C.make_error("JSON_MISSING_PARAMETER"))

        if method.startswith('_'):
            raise tornado.web.HTTPError(403, "Bad method name %s: must not start with _" % method)
        if not isinstance(params, list) and not isinstance(params, dict):
            raise ValueError(C.make_error("PARAMETER_LIST_OR_DICT"))

        # execute command if it is allowed without login
        if method in no_login_commands:
            return self.dispatch(method, params, jid)

        # Check if we're globally locked currently
        if GlobalLock.exists("scan_index"):
            raise FilterException(C.make_error('INDEXING', "base"))

        cls = self.__class__

        twofa_manager = PluginRegistry.getInstance("TwoFactorAuthManager")

        # Create an authentication cookie on login
        if method == 'login':
            (user, password) = params

            # Check password and create session id on success
            sid = str(uuid.uuid1())
            result = {
                'state': AUTH_FAILED
            }

            lock_result = self.get_lock_result(user)
            if lock_result is not None:
                return dict(result=lock_result, error=None, id=jid)

            dn = self.authenticate(user, password)
            if dn is not False:
                # user and password matches so delete the user from observer list
                if user in cls.__dos_manager:
                    del cls.__dos_manager[user]

                with make_session() as session:
                    us = UserSession(
                        sid=sid,
                        user=user,
                        dn=dn
                    )

                    self.set_secure_cookie('REMOTE_USER', user)
                    self.set_secure_cookie('REMOTE_SESSION', sid)
                    factor_method = twofa_manager.get_method_from_user(dn)
                    if factor_method is None:
                        result['state'] = AUTH_SUCCESS
                        self.log.info("login succeeded for user '%s'" % user)
                    elif factor_method == "otp":
                        result['state'] = AUTH_OTP_REQUIRED
                        self.log.info("login succeeded for user '%s', proceeding with OTP two-factor authentication" % user)
                    elif factor_method == "u2f":
                        self.log.info("login succeeded for user '%s', proceeding with U2F two-factor authentication" % user)
                        result['state'] = AUTH_U2F_REQUIRED
                        result['u2f_data'] = twofa_manager.sign(user, dn)

                    us.auth_state = result['state']
                    session.add(us)
            else:
                # Remove current sid if present
                with make_session() as session:
                    db_session = session.query(UserSession).filter(UserSession.sid == sid).one_or_none()
                    if not self.get_secure_cookie('REMOTE_SESSION') and db_session is not None:
                        session.delete(db_session)

                self.log.error("login failed for user '%s'" % user)
                result['state'] = AUTH_FAILED

                # log login tries
                if user in cls.__dos_manager:
                    login_stats = cls.__dos_manager[user]
                    # stop counting after 6 tries to avoid "infinity" lock, the user is locked for more than an hour
                    if login_stats['count'] < 6:
                        login_stats['count'] += 1
                    login_stats['timestamp'] = time.time()
                    cls.__dos_manager[user] = login_stats
                else:
                    cls.__dos_manager[user] = {
                        'count': 1,
                        'timestamp': time.time(),
                        'ip': self.request.remote_ip
                    }
                lock_result = self.get_lock_result(user)
                if lock_result is not None:
                    return dict(result=lock_result, error=None, id=jid)

            return dict(result=result, error=None, id=jid)

        # Don't let calls pass beyond this point if we've no valid session ID
        with make_session() as session:
            cookie = self.get_secure_cookie('REMOTE_SESSION')
            if cookie is None:
                self.log.error("blocked unauthenticated call of method '%s'" % method)
                raise tornado.web.HTTPError(401, "Please use the login method to authorize yourself.")

            db_session = session.query(UserSession).filter(UserSession.sid == cookie.decode('ascii')).one_or_none()
            if db_session is None:
                self.log.error("blocked unauthenticated call of method '%s'" % method)
                raise tornado.web.HTTPError(401, "Please use the login method to authorize yourself.")

            # Remove remote session on logout
            if method == 'logout':

                # Remove current sid if present
                if self.get_secure_cookie('REMOTE_SESSION'):
                    if db_session is not None:
                        session.delete(db_session)

                # Show logout message
                if self.get_secure_cookie('REMOTE_USER'):
                    self.log.info("logout for user '%s' succeeded" % self.get_secure_cookie('REMOTE_USER'))

                self.clear_cookie("REMOTE_USER")
                self.clear_cookie("REMOTE_SESSION")
                return dict(result=True, error=None, id=jid)

            # check two-factor authentication
            if method == 'verify':
                (key,) = params

                if db_session.auth_state == AUTH_OTP_REQUIRED or db_session.auth_state == AUTH_U2F_REQUIRED:

                    if twofa_manager.verify(db_session.user, db_session.dn, key):
                        db_session.auth_state = AUTH_SUCCESS
                        return dict(result={'state': AUTH_SUCCESS}, error=None, id=jid)
                    else:
                        return dict(result={'state': AUTH_FAILED}, error=None, id=jid)

            if db_session.auth_state != AUTH_SUCCESS:
                raise tornado.web.HTTPError(401, "Please use the login method to authorize yourself.")

        return self.dispatch(method, params, jid)

    def dispatch(self, method, params, jid):
        cached_method = method[0:2] == "**"
        hash_value = None
        if cached_method:
            method = method[2:]
            hash_value = params.pop(0)
        # Try to call method with dispatcher
        if not self.dispatcher.hasMethod(method):
            text = "No such method '%s'" % method
            error_value = dict(
                name='JSONRPCError',
                code=100,
                message=text,
                error=text)
            self.log.warning(text)

            self.set_status(500)
            return dict(result=None, error=error_value, id=jid)

        try:
            self.log.debug("calling method %s(%s)" % (method, params))
            user = self.get_secure_cookie('REMOTE_USER').decode('ascii') if self.get_secure_cookie('REMOTE_USER') else None
            sid = self.get_secure_cookie('REMOTE_SESSION').decode('ascii') if self.get_secure_cookie('REMOTE_SESSION') else None
            self.log.debug("received call [%s] for %s (SID=%s): %s(%s)" % (jid, user, sid, method, params))

            if user is None and method in no_login_commands:
                # allow execution without user
                user = self.dispatcher

            if isinstance(params, dict):
                result = self.dispatcher.dispatch(user, sid, method, **params)
            else:
                result = self.dispatcher.dispatch(user, sid, method, *params)

        except JSONRPCException as e:
            exc_value = sys.exc_info()[1]
            error_value = dict(
                name='JSONRPCError',
                code=100,
                message=str(exc_value),
                error=e.error)
            self.log.error(e.error)

            self.set_status(500)
            return dict(result=None, error=error_value, id=jid)

        except Exception as e:
            text = traceback.format_exc()
            exc_value = sys.exc_info()[1]
            status_code = 500

            #TODO: enroll information if it's an extended exception
            err = str(e)
            err_id = C.get_error_id(err)
            if err_id is not None:
                # get error
                err = C.getError(None, None, err_id, keep=True)
                if err and 'status_code' in err and err['status_code'] is not None:
                    status_code = err['status_code']

            error_value = dict(
                name='JSONRPCError',
                code=100,
                message=str(exc_value),
                error=err)

            self.log.error("returning call [%s]: %s / %s" % (jid, None, f_print(err)))
            self.log.error(text)

            self.set_status(status_code)
            return dict(result=None, error=error_value, id=jid)

        self.log.debug("returning call [%s]: %s / %s" % (jid, result, None))
        if cached_method:
            response_hash = hashlib.md5(repr(result).encode('utf-8')).hexdigest()
            if hash_value == response_hash:
                # cache hit
                result = dict(hash=response_hash)
            else:
                # cache miss
                result = dict(hash=response_hash, response=result)
        return dict(result=result, error=None, id=jid)

    def authenticate(self, user=None, password=None):
        """
        Use the LDAP connection to authenticate the incoming HTTP request.

        ================= ==========================
        Parameter         Description
        ================= ==========================
        user              User name to authenticate with
        password          Password
        ================= ==========================

        ``Return``: user dn on success else False
        """

        return check_auth(user, password, get_dn=True)

    @classmethod
    def check_session(cls, sid, user):
        with make_session() as session:
            return session.query(UserSession).filter(UserSession.sid == sid, UserSession.user == user).count() > 0

    @classmethod
    def user_sessions_available(cls, user):
        with make_session() as session:
            if user is not None:
                return session.query(UserSession).filter(UserSession.user == user).count() > 0
            else:
                return session.query(UserSession).count() > 0
