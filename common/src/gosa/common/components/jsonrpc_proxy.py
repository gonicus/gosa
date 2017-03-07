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
from urllib.error import HTTPError

import requests
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


class XSRFCookieProcessor(urllib2.HTTPCookieProcessor):
    """
    Extend the HTTPCookieProcessor by handling the XSRF Cookie from tornado
    """
    def __init__(self, cookiejar=None):
        if cookiejar is None:
            cookiejar = cookielib.CookieJar()
        self.cookiejar = cookiejar
        self.xsrf_token = None

    def http_request(self, request):
        if not request.has_header('X-XSRFToken') and (self.xsrf_token):
            request.add_unredirected_header("X-XSRFToken", self.xsrf_token)
        self.cookiejar.add_cookie_header(request)
        return request

    def http_response(self, request, response):
        self.cookiejar.extract_cookies(response, request)
        cookies = requests.utils.dict_from_cookiejar(self.cookiejar)
        if '_xsrf' in cookies:
            self.xsrf_token = cookies['_xsrf']
        return response

    def has_token(self):
        return self.xsrf_token is not None

    https_request = http_request
    https_response = http_response


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

    def __init__(self, serviceURL=None, serviceName=None, opener=None, mode='POST', cookieProcessor=None):
        self.__serviceURL = serviceURL
        self.__serviceName = serviceName
        self.__mode = mode
        if cookieProcessor is None:
            self.__cookieProcessor = XSRFCookieProcessor()
        else:
            self.__cookieProcessor = cookieProcessor

        username = None
        password = None

        if not opener:
            http_handler = urllib2.HTTPHandler()
            https_handler = urllib2.HTTPSHandler()

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
                                              self.__cookieProcessor, auth_handler)

            else:
                opener = urllib2.build_opener(http_handler, https_handler, self.__cookieProcessor)

        self.__opener = opener

        # Eventually log in
        if username and password:
            self.login(username, password)

    def __getattr__(self, name):
        if self.__serviceName != None:
            name = "%s.%s" % (self.__serviceName, name)

        return JSONServiceProxy(self.__serviceURL, name, self.__opener, self.__mode, self.__cookieProcessor)

    def get_facet(self):
        return self.__serviceURL

    def getProxy(self):
        return JSONServiceProxy(self.__serviceURL, None, self.__opener, self.__mode)

    def apply_cookies(self, request):
        return self.__cookieProcessor.http_request(request)

    def __call__(self, *args, **kwargs):
        if len(kwargs) > 0 and len(args) > 0:
            raise JSONRPCException("JSON-RPC does not support positional and keyword arguments at the same time")

        if not self.__cookieProcessor.has_token():
            # get the cookie
            self.__opener.open(self.__serviceURL).read()

        if len(kwargs):
            postdata = dumps({"method": self.__serviceName, 'params': kwargs, 'id': 'jsonrpc'})
        else:
            postdata = dumps({"method": self.__serviceName, 'params': args, 'id': 'jsonrpc'})

        try:
            if self.__mode == 'POST':
                respdata = self.__opener.open(self.__serviceURL, postdata.encode('utf8')).read()
            else:
                respdata = self.__opener.open(self.__serviceURL + "?" + quote(postdata.encode('utf8'))).read()
        except HTTPError as e:
            error = loads(e.fp.readline())
            raise JSONRPCException(error['error']['message'])

        resp = loads(respdata)
        if resp['error'] != None:
            raise JSONRPCException(resp['error'])

        return resp['result']
