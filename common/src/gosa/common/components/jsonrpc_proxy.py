# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

import urllib.request as urllib2
import http.cookiejar as cookielib
from urllib.parse import quote, urlparse
from gosa.common.gjson import dumps, loads
from gosa.common.components.json_exception import JSONRPCException


class JSONObjectFactory(object):

    def __init__(self, proxy, ref, dn, oid, methods, properties, data):
        object.__setattr__(self, "proxy", proxy)
        object.__setattr__(self, "ref", ref)
        object.__setattr__(self, "uuid", ref)
        object.__setattr__(self, "dn", dn)
        object.__setattr__(self, "oid", oid)
        object.__setattr__(self, "methods", methods)
        object.__setattr__(self, "properties", properties)

        for prop in properties:
            object.__setattr__(self, "_" + prop, None if not prop in data else data[prop])

    def _call(self, name, *args, **kwargs):
        ref = object.__getattribute__(self, "ref")
        return object.__getattribute__(self, "proxy").dispatchObjectMethod(ref,
                name, *args, **kwargs)

    def __getattribute__(self, name):

        if name in ['uuid', 'dn']:
            return object.__getattribute__(self, name)

        if name in object.__getattribute__(self, "methods"):
            return lambda *f: object.__getattribute__(self, "_call")(*[name] + list(f))

        if not name in object.__getattribute__(self, "properties"):
            raise AttributeError("'%s' object has no attribute '%s'" %
                (type(self).__name__, name))

        return object.__getattribute__(self, "_" + name)

    def __setattr__(self, name, value):
        if not name in object.__getattribute__(self, "properties"):
            raise AttributeError("'%s' object has no attribute '%s'" %
                (type(self).__name__, name))

        ref = object.__getattribute__(self, "ref")
        object.__getattribute__(self, "proxy").setObjectProperty(ref, name, value)
        object.__setattr__(self, "_" + name, value)

    def __repr__(self):
        return object.__getattribute__(self, "ref")

    @staticmethod
    def get_instance(proxy, obj_type, ref, dn, oid, methods, properties, data=None):
        return type(str(obj_type),
                (JSONObjectFactory, object),
                JSONObjectFactory.__dict__.copy())(proxy, ref, dn, oid, methods, properties, data)


class JSONServiceProxy(object):
    """
    The JSONServiceProxy provides a simple way to use GOsa RPC
    services from various clients. Using the proxy object, you
    can directly call methods without the need to know where
    it actually gets executed.

    Example::

        >>> proxy = JSONServiceProxy('https://localhost')
        >>> proxy.login("admin", "secret")
        >>> proxy.getMethods()
        ...
        >>> proxy.logout()

    This will return a dictionary describing the available methods.

    =============== ============
    Parameter       Description
    =============== ============
    serviceURL      URL used to connect to the HTTP service
    serviceName     *internal*
    opener          *internal*
    mode            Use POST or GET for communication
    =============== ============

    The URL format is::

       (http|https)://user:password@host:port/rpc

    .. note::
       The HTTP service is operated by a gosa-backend instance.
    """

    def __init__(self, serviceURL=None, serviceName=None, opener=None, mode='POST'):
        self.__serviceURL = serviceURL
        self.__serviceName = serviceName
        self.__mode = mode
        username = None
        password = None

        if not opener:
            http_handler = urllib2.HTTPHandler()
            https_handler = urllib2.HTTPSHandler()
            cookie_handler = urllib2.HTTPCookieProcessor(cookielib.CookieJar())

            # Split URL, user, password from provided URL
            tmp = urlparse(serviceURL)
            if tmp.username:
                username = tmp.username
                password = tmp.password
                self.__serviceURL = "%s://%s:%s%s" % (tmp.scheme, tmp.hostname,
                        tmp.port, tmp.path)
                passman = urllib2.HTTPPasswordMgrWithDefaultRealm()
                passman.add_password(None, self.__serviceURL, username, password)
                auth_handler = urllib2.HTTPBasicAuthHandler(passman)
                opener = urllib2.build_opener(http_handler, https_handler,
                        cookie_handler, auth_handler)

            else:
                opener = urllib2.build_opener(http_handler, https_handler, cookie_handler)

        self.__opener = opener

        # Eventually log in
        if username and password:
            self.login(username, password)

    def __getattr__(self, name):
        if self.__serviceName != None:
            name = "%s.%s" % (self.__serviceName, name)

        return JSONServiceProxy(self.__serviceURL, name, self.__opener, self.__mode)

    def getProxy(self):
        return JSONServiceProxy(self.__serviceURL, None, self.__opener, self.__mode)

    def __call__(self, *args, **kwargs):
        if len(kwargs) > 0 and len(args) > 0:
            raise JSONRPCException("JSON-RPC does not support positional and keyword arguments at the same time")

        if len(kwargs):
            postdata = dumps({"method": self.__serviceName, 'params': kwargs, 'id': 'jsonrpc'})
        else:
            postdata = dumps({"method": self.__serviceName, 'params': args, 'id': 'jsonrpc'})

        if self.__mode == 'POST':
            respdata = self.__opener.open(self.__serviceURL, postdata).read()
        else:
            respdata = self.__opener.open(self.__serviceURL + "?" + quote(postdata)).read()

        resp = loads(respdata)
        if resp['error'] != None:
            raise JSONRPCException(resp['error'])

        return resp['result']
