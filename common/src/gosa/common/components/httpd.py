# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

"""
The *HTTPService* and the *HTTPDispatcher* are responsible for exposing
registered `WSGI <http://wsgi.org>`_ components to the world. While the
*HTTPService* is just providing the raw HTTP service, the *HTTPDispatcher*
is redirecting a path to a module.

-------
"""
from threading import Thread
import logging
import tornado.wsgi
import tornado.web
import pkg_resources
from tornado.ioloop import IOLoop
from tornado.httpserver import HTTPServer
from zope.interface import implementer
from webob import exc #@UnresolvedImport
from gosa.common import Environment
from gosa.common.handler import IInterfaceHandler
from gosa.common.utils import N_
from gosa.common.error import GosaErrorHandler as C
from gosa.common.exceptions import HTTPException

C.register_codes(dict(
    HTTP_PATH_ALREADY_REGISTERED=N_("'%(path)s' has already been registered")
    ))


class HTTPDispatcher(object):
    """
    The *HTTPDispatcher* can be used to register WSGI applications
    to a given path. It will inspect the path of an incoming request
    and decides which registered application it gets.

    Analyzing the path can be configured to detect a *subtree* match
    or an *exact* match. If you need subtree matches, just add the
    class variable ``http_subtree`` to the WSGI class and set it to
    *True*.
    """

    def __init__(self):
        self.__app = {}
        self.env = Environment.getInstance()
        self.log = logging.getLogger(__name__)

    def __call__(self, environ, start_response):
        path = environ.get('PATH_INFO')
        for app_path in sorted(self.__app, key=len, reverse=True):
            app = self.__app[app_path]

            if hasattr(app, "http_subtree") and path.startswith(app_path if app_path == "/" else app_path + "/"):
                return app.__call__(environ, start_response)
            elif path == app_path:
                return app.__call__(environ, start_response)

        # Nothing found
        self.log.debug('no resource %s registered!' % path)
        resp = exc.HTTPNotFound('no resource %s registered!' % path)
        return resp(environ, start_response)

    def register(self, path, app):
        self.log.debug("registering %s on %s" % (app.__class__.__name__, path))
        self.__app[path] = app

    def unregister(self, path):
        if path in self.__app:
            self.log.debug("unregistering %s" % path)
            del(self.__app[path])

@implementer(IInterfaceHandler)
class HTTPService(object):
    """
    Class to serve HTTP fragments to the interested client. It makes
    makes use of a couple of configuration flags provided by the clacks
    configuration files ``[http]`` section:

    ============== =============
    Key            Description
    ============== =============
    url            AMQP URL to connect to the broker
    id             User name to connect with
    key            Password to connect with
    command-worker Number of worker processes
    ============== =============

    Example::

        [http]
        host = node1.intranet.gonicus.de
        port = 8080
        sslpemfile = /etc/clacks/host.pem

    If you want to create a clacks agent module that is going to export
    functionality (i.e. static content or some RPC functionality) you
    can register such a component like this::

        >>> from gosa.common.components import PluginRegistry
        >>> class SomeTest(object):
        ...    http_subtree = True
        ...    path = '/test'
        ...
        ...    def __init__(self):
        ...        # Get http service instance
        ...        self.__http = PluginRegistry.getInstance('HTTPService')
        ...
        ...        # Register ourselves
        ...        self.__http.register(self.path, self)
        ...

    When *SomeTest* is instantiated, it will register itself to the *HTTPService* -
    and will be served when the *HTTPService* starts up.
    """
    _priority_ = 10

    __register = {}
    __register_ws = {}
    __register_static = {}

    def __init__(self):
        env = Environment.getInstance()
        self.log = logging.getLogger(__name__)
        self.log.info("initializing HTTP service provider")
        self.env = env
        self.srv = None
        self.ssl = None
        self.app = None
        self.host = None
        self.scheme = None
        self.port = None

    def serve(self):
        """
        Start HTTP service thread.
        """
        self.app = HTTPDispatcher()

        self.host = self.env.config.get('http.host', default="localhost")
        self.port = self.env.config.get('http.port', default=8080)
        self.ssl = self.env.config.get('http.ssl', default=None)

        if self.ssl and self.ssl.lower() in ['true', 'yes', 'on']:
            self.scheme = "https"
            ssl_options = dict(
                certfile=self.env.config.get('http.certfile', default=None),
                keyfile=self.env.config.get('http.keyfile', default=None),
                ca_certs=self.env.config.get('http.ca-certs', default=None))
        else:
            self.scheme = "http"
            ssl_options = None

        apps = []

        # register routes in the HTTPService
        for entry in pkg_resources.iter_entry_points("gosa.route"):
            module = entry.load()
            apps.append((entry.name, module))

        # Make statics registerable
        for pth, local_pth in self.__register_static.items():
            apps.append((pth, tornado.web.StaticFileHandler, {"path": local_pth}))

        # Make websockets available if registered
        for pth, ws_app in self.__register_ws.items():
            apps.append((pth, ws_app))

        # Finally add the WSGI handler
        wsgi_app = tornado.wsgi.WSGIContainer(self.app)
        apps.append((r".*", tornado.web.FallbackHandler, dict(fallback=wsgi_app)))

        application = tornado.web.Application(apps)

        # Fetch server
        self.srv = HTTPServer(application, ssl_options=ssl_options)

        self.srv.listen(self.port, self.host)
        self.thread = Thread(target=self.start)
        self.thread.start()

        self.log.info("now serving on %s://%s:%s" % (self.scheme, self.host, self.port))

        # Register all possible instances that have shown
        # interrest to be served
        for path, obj in self.__register.items():
            self.app.register(path, obj)

    def start(self):
        IOLoop.instance().start()

    def stop(self):
        """
        Stop HTTP service thread.
        """
        self.log.debug("shutting down HTTP service provider")
        IOLoop.instance().stop()

    def register(self, path, app):
        """
        Register the application *app* on path *path*.

        ================= ==========================
        Parameter         Description
        ================= ==========================
        path              Path part of an URL - i.e. '/rpc'
        app               WSGI application
        ================= ==========================
        """
        if path in self.__register_static or path in self.__register_ws:
            raise HTTPException(C.make_error("HTTP_PATH_ALREADY_REGISTERED", path=path))

        self.__register[path] = app

    def register_static(self, path, local_path):
        """
        Register a static directory *local_path* in the web servers
        *path*.

        ================= ==========================
        Parameter         Description
        ================= ==========================
        path              Path part of an URL - i.e. '/static'
        local_path        Local path to serve from - i.e. '/var/www'
        ================= ==========================
        """
        if path in self.__register or path in self.__register_ws:
            raise HTTPException(C.make_error("HTTP_PATH_ALREADY_REGISTERED", path=path))

        self.__register_static[path] = local_path

    def register_ws(self, path, app):
        """
        Register the websocket application *app* on path *path*.

        ================= ==========================
        Parameter         Description
        ================= ==========================
        path              Path part of an URL - i.e. '/ws'
        app               WSGI application
        ================= ==========================
        """
        if path in self.__register or path in self.__register_static:
            raise HTTPException(C.make_error("HTTP_PATH_ALREADY_REGISTERED", path=path))

        self.__register_ws[path] = app
