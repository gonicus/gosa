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
import ssl
import tornado.wsgi
import tornado.web
import pkg_resources
import socket
from tornado.ioloop import IOLoop
from tornado.httpserver import HTTPServer
from zope.interface import implementer
from gosa.common import Environment
from gosa.common.hsts_request_handler import HSTSRequestHandler, HSTSStaticFileHandler
from gosa.common.handler import IInterfaceHandler
from gosa.common.utils import N_
from gosa.common.error import GosaErrorHandler as C

C.register_codes(dict(
    HTTP_PATH_ALREADY_REGISTERED=N_("'%(path)s' has already been registered")
    ))


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

    def __init__(self):
        env = Environment.getInstance()
        self.log = logging.getLogger(__name__)
        self.log.info("initializing HTTP service provider")
        self.env = env
        self.srv = None
        self.ssl = None
        self.host = None
        self.scheme = None
        self.port = None

    def serve(self):
        """
        Start HTTP service thread.
        """
        self.host = self.env.config.get('http.host', default="localhost")
        self.port = self.env.config.get('http.port', default=8080)
        self.ssl = self.env.config.get('http.ssl', default=None)

        if self.ssl and self.ssl.lower() in ['true', 'yes', 'on']:
            self.scheme = "https"
            ssl_ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)

            cafile = self.env.config.get('http.ca-certs', default=None)
            if cafile:
                ssl_ctx.load_verify_locations(cafile=cafile)

            ssl_ctx.load_cert_chain(self.env.config.get('http.cert-file', default=None), self.env.config.get('http.key-file', default=None))
        else:
            self.scheme = "http"
            ssl_ctx = None

        apps = []

        # register routes in the HTTPService
        for entry in sorted(pkg_resources.iter_entry_points("gosa.route"), key=lambda entry: entry.name, reverse=True):
            module = entry.load()
            if issubclass(module, (HSTSStaticFileHandler, HSTSRequestHandler)):
                self.log.debug("registering route %s for %s" % (entry.name, module))
                apps.append((entry.name, module, {"hsts": self.ssl}))
            else:
                self.log.error("Registering '%s' as HTTP service denied: no subclass of HSTSRequestHandler or HSTSStaticFileHandler" % module)

        application = tornado.web.Application(apps,
                                              cookie_secret=self.env.config.get('http.cookie-secret', default="TecloigJink4"),
                                              xsrf_cookies=True)

        # Fetch server
        self.srv = HTTPServer(application, ssl_options=ssl_ctx)

        self.srv.listen(self.port, self.host)
        self.thread = Thread(target=self.start)
        self.thread.start()

        self.log.info("now serving on %s://%s:%s" % (self.scheme, self.host, self.port))

    def get_gui_uri(self):
        """ Returns the gui URI as a tuple of base URI and relative path"""
        default = "index.html"
        if self.env.config.get("gui.debug", "false") == "true":  # pragma: nocover
            default = "gosa/source/index.html"
        return "%s://%s:%s" %(self.scheme, socket.gethostname(), self.port), default

    def start(self):
        IOLoop.configure('tornado.platform.asyncio.AsyncIOLoop')
        IOLoop.instance().start()

    def stop(self):
        """
        Stop HTTP service thread.
        """
        self.log.debug("shutting down HTTP service provider")
        IOLoop.instance().stop()
