import re
from tornado.testing import AsyncHTTPTestCase
from tornado.web import Application
from gosa.common.gjson import dumps, loads
from gosa.backend.components.jsonrpc_service import JsonRpcHandler
from gosa.common.components import PluginRegistry

class JsonRpcHandlerTestCase(AsyncHTTPTestCase):

    def get_app(self):
        return Application([('/rpc', JsonRpcHandler)], cookie_secret='TecloigJink4')

    def setUp(self):
        super(JsonRpcHandlerTestCase, self).setUp()
        self.registry = PluginRegistry()
        self.__cookies = ''

    def tearDown(self):
        super(JsonRpcHandlerTestCase, self).tearDown()
        self.registry.shutdown()

    def _update_cookies(self, headers):
        try:
            raw = headers['Set-Cookie']
            #remove expires + path
            raw = re.sub(r"; expires=[^;]+;", "", raw)
            raw = re.sub(r" Path=[^,]+,", ";", raw)
            # last path
            raw = re.sub(r" Path=[^,]$", "", raw)
            self.__cookies = raw
        except KeyError:
            return

    def fetch(self, url, **kw):
        header = {}
        if self.__cookies != '':
            header['Cookie'] = self.__cookies
        # print("URL: {}, Body: {}, Headers: {}".format(url, kw['body'], header))
        resp = AsyncHTTPTestCase.fetch(self, url, headers=header, **kw)
        self._update_cookies(resp.headers)
        return resp

    def login(self):
        data = dumps({
            "id": 0,
            "method": "login",
            "params": ["username", "password"]
        })
        return self.fetch('/rpc',
                          method='POST',
                          body=data
                          )

    def test_login(self):
        response = self.login()
        assert response.code == 200
        json = loads(response.body)
        assert json['result'] == True
        assert json['error'] is None
        assert json['id'] == 0

    def test_bad_method_name(self):
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

    def test_logout(self):
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
