# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

import unittest.mock
from tornado.web import Application
from gosa.common.gjson import dumps, loads
from gosa.backend.components.jsonrpc_service import JsonRpcHandler, AUTH_SUCCESS, AUTH_FAILED, AUTH_LOCKED
from gosa.common.components import PluginRegistry
from tests.GosaTestCase import slow
from tests.RemoteTestCase import RemoteTestCase


@slow
class JsonRpcHandlerTestCase(RemoteTestCase):

    def get_app(self):
        return Application([('/rpc', JsonRpcHandler)], cookie_secret='TecloigJink4', xsrf_cookies=True)

    def setUp(self):
        super(JsonRpcHandlerTestCase, self).setUp()

        self.mocked_resolver = unittest.mock.MagicMock()
        self.mocked_resolver.return_value.check.return_value = True
        self.patcher = unittest.mock.patch.dict(PluginRegistry.modules, {'ACLResolver': self.mocked_resolver})
        self.patcher.start()

    def tearDown(self):
        super(JsonRpcHandlerTestCase, self).tearDown()
        self.patcher.stop()

    def test_login(self):
        # successful login
        with unittest.mock.patch.object(JsonRpcHandler, 'authenticate', return_value='cn=System Administrator,ou=people,dc=example,'
                                                                                     'dc=net') as m:
            response = self.login()
            assert response.code == 200
            json = loads(response.body)
            assert json['result']['state'] == AUTH_SUCCESS
            assert json['error'] is None
            assert json['id'] == 0

        # failed login
        with unittest.mock.patch.object(JsonRpcHandler, 'authenticate', return_value=False) as m:
            response = self.login()
            json = loads(response.body)
            assert json['result']['state'] == AUTH_LOCKED

            # reset lock
            JsonRpcHandler._JsonRpcHandler__dos_manager = {}

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
            "params": ["admin", "tester"]
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
        assert json['result'] is True
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
        assert json['result'] == "admin"

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
