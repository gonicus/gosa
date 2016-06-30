# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

import re
import unittest.mock
from tornado.testing import AsyncHTTPTestCase
from tornado.web import Application
from gosa.common.gjson import dumps, loads
from gosa.backend.components.jsonrpc_service import JsonRpcHandler
from gosa.common.components import PluginRegistry

class JsonRpcHandlerTestCase(AsyncHTTPTestCase):

    def get_app(self):
        return Application([('/rpc', JsonRpcHandler)], cookie_secret='TecloigJink4', xsrf_cookies=True)

    def setUp(self):
        super(JsonRpcHandlerTestCase, self).setUp()
        self.registry = PluginRegistry()
        self.__cookies = ''
        self._xsrf = None

    def tearDown(self):
        super(JsonRpcHandlerTestCase, self).tearDown()
        self.registry.shutdown()

    def _update_cookies(self, headers):
        try:
            raw = headers['Set-Cookie']
            #remove expires + path
            raw = re.sub(r"; expires=[^;]+;", "", raw)
            raw = re.sub(r";? Path=[^,]+,", ";", raw)
            # last path
            raw = re.sub(r";? Path=[^,]$", "", raw)
            for cookie in raw.split(";"):
                (key, value) = cookie.split("=", 1)
                if key == "_xsrf":
                    self._xsrf = value
            self.__cookies = raw
        except KeyError:
            return

    def fetch(self, url, **kw):
        header = {}
        if self.__cookies != '':
            header['Cookie'] = self.__cookies
        if self._xsrf:
            header['X-XSRFToken'] = self._xsrf
            if len(header['Cookie'])>0 and '_xsrf' not in header['Cookie']:
                header['Cookie'] = "%s;%s=%s" % (header['Cookie'], '_xsrf', self._xsrf)
        if 'body' in kw:
            print("URL: {}, Body: {}, Headers: {}".format(url, kw['body'] , header))
        else:
            print("URL: {}, Headers: {}".format(url, header))
        resp = AsyncHTTPTestCase.fetch(self, url, headers=header, **kw)
        self._update_cookies(resp.headers)
        return resp

    def login(self):
        # fetch the xsrf cookie
        self.fetch('/rpc', method='GET')
        data = dumps({
            "id": 0,
            "method": "login",
            "params": ["username", "password"]
        })
        # login
        return self.fetch('/rpc',
                          method='POST',
                          body=data
                          )

    def test_login(self):
        # failed login
        with unittest.mock.patch.object(JsonRpcHandler, 'authenticate', return_value=False) as m:
            response = self.login()
            assert response.code == 401

        # successfull login
        with unittest.mock.patch.object(JsonRpcHandler, 'authenticate', return_value=True) as m:
            response = self.login()
            assert response.code == 200
            json = loads(response.body)
            assert json['result'] == True
            assert json['error'] is None
            assert json['id'] == 0

    def test_bad_method_name(self):
        # fetch the xsrf cookie
        self.fetch('/rpc', method='GET')
        data = dumps({
            "id": 1,
            "method": "_somemethod",
            "params": []
        })
        response = self.fetch('/rpc',
                              method='POST',
                              body=data
                              )
        assert response.code == 403

    def test_xsrf(self):
        data = dumps({
            "id": 3,
            "method": "login",
            "params": ["username", "passwd"]
        })
        response = self.fetch('/rpc',
                          method='POST',
                          body=data
                          )
        # without requesting the xsrf cookie we get the 403 code
        assert response.code == 403

    def test_logout(self):
        # fetch the xsrf cookie
        self.fetch('/rpc', method='GET')
        data = dumps({
            "id": 3,
            "method": "logout",
            "params": []
        })
        response = self.fetch('/rpc',
                          method='POST',
                          body=data
                          )
        # logging out before beeing logged in is not allowed
        assert response.code == 401

        self.login()
        response = self.fetch('/rpc',
                              method='POST',
                              body=data
                              )

        assert response.code == 200
        json = loads(response.body)
        assert json['result'] == True
        assert json['error'] is None
        assert json['id'] == 3

        # check if we are logged out
        data = dumps({
            "id": 3,
            "method": "getSessionUser",
            "params": []
        })
        response = self.fetch('/rpc',
                              method='POST',
                              body=data
                              )
        assert response.code == 401

    def test_unknown(self):
        self.login()
        data = dumps({
            "id": 1,
            "method": "unknownmethod",
            "params": []
        })
        response = self.fetch('/rpc',
                              method='POST',
                              body=data
                              )

        assert response.code == 500
        json = loads(response.body)
        assert json['error']['code'] == 100
        assert json['error']['name'] == "JSONRPCError"

    def test_missingparameter(self):
        # fetch the xsrf cookie
        self.fetch('/rpc', method='GET')
        data = dumps({
            "id": 1,
            "params": []
        })
        response = self.fetch('/rpc',
                              method='POST',
                              body=data
                              )
        assert response.code == 400

    def test_invalidjson(self):
        # fetch the xsrf cookie
        self.fetch('/rpc', method='GET')
        response = self.fetch('/rpc',
                              method='POST',
                              body="this is no json://"
                              )
        assert response.code == 400

    def test_wrong_parameter_format(self):
        # fetch the xsrf cookie
        self.fetch('/rpc', method='GET')
        data = dumps({
            "id": 1,
            "method": "login",
            "params": 'no list or dict'
        })
        response = self.fetch('/rpc',
                              method='POST',
                              body=data
                              )
        assert response.code == 400

    def test_getSessionUser(self):
        self.login()
        data = dumps({
            "id": 1,
            "method": "getSessionUser",
            "params": []
        })
        response = self.fetch('/rpc',
                              method='POST',
                              body=data
                              )
        assert response.code == 200
        json = loads(response.body)
        assert json['result'] == "username"


    def test_exception(self):
        self.login()
        data = dumps({
            "id": 1,
            "method": "getSessionUser",
            "params": {'test': 'test'}
        })
        response = self.fetch('/rpc',
                              method='POST',
                              body=data
                              )
        assert response.code == 500
        json = loads(response.body)
        assert json['error']['code'] == 100
        assert json['error']['name'] == "JSONRPCError"
