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
from zope.interface import implementer
from gosa.common.gjson import loads, dumps
from gosa.common.utils import f_print, N_
from gosa.common.error import GosaErrorHandler as C
from gosa.common.handler import IInterfaceHandler
from gosa.common import Environment
from gosa.common.components import PluginRegistry, JSONRPCException
from gosa.backend import __version__ as VERSION


# Register the errors handled  by us
C.register_codes(dict(
    INVALID_JSON=N_("Invalid JSON string '%(data)s'"),
    JSON_MISSING_PARAMETER=N_("Parameter missing in JSON body"),
    PARAMETER_LIST_OR_DICT=N_("Parameter must be list or dictionary"),
    REGISTRY_NOT_READY=N_("Registry is not ready")
    ))

class JsonRpcHandler(tornado.web.RequestHandler):
    """
    This is the tornado request handler wich is responsible for serving the
    :class:`gosa.backend.command.CommandRegistry` via HTTP/JSONRPC.
    """

    # Simple authentication saver
    __session = {}

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
        else:
            self.write(resp)

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

        # Create an authentication cookie on login
        if method == 'login':
            (user, password) = params

            # Check password and create session id on success
            sid = str(uuid.uuid1())

            if self.authenticate(user, password):
                self.__session[sid] = user
                self.set_secure_cookie('REMOTE_USER', user)
                self.set_secure_cookie('REMOTE_SESSION', sid)
                result = True
                self.log.info("login succeeded for user '%s'" % user)
            else:
                # Remove current sid if present
                if not self.get_secure_cookie('REMOTE_SESSION') and sid in self.__session:
                    del self.__session[sid]

                result = False
                self.log.error("login failed for user '%s'" % user)
                raise tornado.web.HTTPError(401, "Login failed")

            return dict(result=result, error=None, id=jid)

        # Don't let calls pass beyond this point if we've no valid session ID
        if self.get_secure_cookie('REMOTE_SESSION') is None or not self.get_secure_cookie('REMOTE_SESSION').decode('ascii') in self.__session:
            self.log.error("blocked unauthenticated call of method '%s'" % method)
            raise tornado.web.HTTPError(401, "Please use the login method to authorize yourself.")

        # Remove remote session on logout
        if method == 'logout':

            # Remove current sid if present
            if self.get_secure_cookie('REMOTE_SESSION') and self.get_secure_cookie('REMOTE_SESSION').decode('ascii') in self.__session:
                del self.__session[self.get_secure_cookie('REMOTE_SESSION').decode('ascii')]

            # Show logout message
            if self.get_secure_cookie('REMOTE_USER'):
                self.log.info("logout for user '%s' succeeded" % self.get_secure_cookie('REMOTE_USER'))

            self.clear_cookie("REMOTE_USER")
            self.clear_cookie("REMOTE_SESSION")
            return dict(result=True, error=None, id=jid)

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
            user = self.get_secure_cookie('REMOTE_USER').decode('ascii')
            self.log.debug("received call [%s] for %s: %s(%s)" % (jid, user, method, params))

            if isinstance(params, dict):
                result = self.dispatcher.dispatch(user, method, **params)
            else:
                result = self.dispatcher.dispatch(user, method, *params)

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

            #TODO: enroll information if it's an extended exception
            err = str(e)

            error_value = dict(
                name='JSONRPCError',
                code=100,
                message=str(exc_value),
                error=err)

            self.log.error("returning call [%s]: %s / %s" % (jid, None, f_print(err)))
            self.log.error(text)

            self.set_status(500)
            return dict(result=None, error=error_value, id=jid)

        self.log.debug("returning call [%s]: %s / %s" % (jid, result, None))

        return dict(result=result, error=None, id=jid)

    def authenticate(self, user=None, password=None):
        """
        Use the AMQP connection to authenticate the incoming HTTP request.

        ================= ==========================
        Parameter         Description
        ================= ==========================
        user              User name to authenticate with
        password          Password
        ================= ==========================

        ``Return``: True on success
        """
        #TODO: use LDAP here when the integration is done
        return True

    def check_session(self, sid, user):
        if not sid in self.__session:
            return False

        return self.__session[sid] == user

    def user_sessions_available(self, user):
        if user:
            return user in self.__session.values()
        else:
            return len(self.__session) > 0
