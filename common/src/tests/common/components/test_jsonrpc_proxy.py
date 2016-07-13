#!/usr/bin/python3

import unittest
import pytest
import json
from io import StringIO
from gosa.common.components.jsonrpc_proxy import *

class JSONRPCProxyTestCase(unittest.TestCase):
    @unittest.mock.patch("gosa.common.components.jsonrpc_proxy.urllib2")
    @unittest.mock.patch("gosa.common.components.jsonrpc_proxy.dumps", wraps=json.dumps)
    def test_JSONRPCProxy(self, jsonDumpsMock, urllib2Mock):
        # ServiceURL is a optional argument and could be None through requests
        # (which of course would cause errors).
        
        def respError(*args, **kwargs):
            return StringIO("""{"error": "data", "result": null, "id": "jsonrpc"}""")
        def respSuccess(*args, **kwargs):
            return StringIO("""{"error": null, "result": "information", "id": "jsonrpc"}""")
        http_handler = unittest.mock.MagicMock()
        https_handler = unittest.mock.MagicMock()
        opener = unittest.mock.MagicMock()
        opener.open.side_effect = respSuccess
        
        urllib2Mock.HTTPHandler.return_value = http_handler
        urllib2Mock.HTTPSHandler.return_value = https_handler
        
        urllib2Mock.build_opener.return_value = opener
        
        sp = JSONServiceProxy()
        sp("test parameter", 1)
        jsonDumpsMock.assert_called_with({"method": None, "params": ("test parameter", 1), "id": "jsonrpc"})
        opener.open.side_effect = respError
        sp = sp.getProxy() # Recreates instance (with a few parameters gone)
        with pytest.raises(JSONRPCException):
            sp(test="TEST", digit=1)
        jsonDumpsMock.assert_called_with({"method": None, "params": {"test": "TEST", "digit": 1}, "id": "jsonrpc"})
        
        with pytest.raises(JSONRPCException):
            sp("positional arg", test="TEST", digit=1)
        
        opener.open.side_effect = respSuccess
        
        # Implementation checks if mode is "POST" and uses PostData to transmit the data.
        # Using any other mode will cause the data to be sent url-form-encoded.
        # Assuming "GET"
        sp = JSONServiceProxy(serviceURL="http://user:secret@localhost:8080/rpc", mode="GET")
        jsonDumpsMock.assert_called_with({"method": "login", "params": ("user", "secret"), "id": "jsonrpc"})
        # Username and password are omitted after initial login
        sp()
        opener.open.assert_called_with("http://localhost:8080/rpc?"+quote(dumps({"method": None, "params": (), "id": "jsonrpc"})))
        
        # Trigger line 173 - Expansion of __serviceName
        sp.name1.name2

    @unittest.mock.patch("gosa.common.components.jsonrpc_proxy.cookielib")
    @unittest.mock.patch("gosa.common.components.jsonrpc_proxy.requests.utils")
    def test_XSRFCookieProcessor(self, requestsUtilsMock, cookielibMock):
        cookieJarMock = unittest.mock.MagicMock()
        cookielibMock.CookieJar.return_value = cookieJarMock
        
        request = unittest.mock.MagicMock()
        request.has_header.return_value = False
        
        response = unittest.mock.MagicMock()
        
        def extract_cookies(resp, req):
            assert resp == response
            assert req == request
        cookieJarMock.extract_cookies.side_effect = extract_cookies
        def dict_from_cookiejar(cookiejar):
            assert cookiejar == cookieJarMock
            return {"_xsrf": "TOKEN"}
        def dict_from_cookiejar_without_token(cookiejar):
            assert cookiejar == cookieJarMock
            return {}
        requestsUtilsMock.dict_from_cookiejar.side_effect = dict_from_cookiejar_without_token
        
        # Initial state
        cp = XSRFCookieProcessor()
        assert cp.has_token() == False
        assert cp.http_request(request) == request
        
        # first request
        request.has_header.assert_called_once_with("X-XSRFToken")
        cookieJarMock.add_cookie_header.assert_called_with(request)
        
        cp.http_response(request, response)
        cookieJarMock.extract_cookies.assert_called_with(response, request)
        requestsUtilsMock.dict_from_cookiejar.assert_called_with(cookieJarMock)
        
        # After the first request, there is still no token present
        assert cp.has_token() == False
        
        # first response
        requestsUtilsMock.dict_from_cookiejar.side_effect = dict_from_cookiejar
        cp.http_response(request, response)
        cookieJarMock.extract_cookies.assert_called_with(response, request)
        requestsUtilsMock.dict_from_cookiejar.assert_called_with(cookieJarMock)
        
        # after the arrival of a response with a token, there is a token present
        assert cp.has_token()
        
        # new request uses the token
        cp.http_request(request)
        request.has_header.assert_called_with("X-XSRFToken")
        request.add_unredirected_header.assert_called_with("X-XSRFToken", "TOKEN")
        cookieJarMock.add_cookie_header.assert_called_with(request)
        
        # if a token is already present in the given request, a it is not added
        # to the request, but to the cookiejar.
        countRequestAdded = request.add_unredirected_header.call_count
        request.has_header.return_value = True
        cp.http_request(request)
        assert countRequestAdded == request.add_unredirected_header.call_count

    def test_JSONObjectFactory(self):
        import uuid
        object_uuid = str(uuid.uuid4())
        
        def dispatchObjectMethod(ref, name, *args):
            # Note: No keyword arguments are forwarded.
            assert ref == object_uuid
            assert name == "testfunction"
            assert args == ("required parameter",)
            return "success"
        
        proxy = unittest.mock.MagicMock()
        proxy.dispatchObjectMethod.side_effect = dispatchObjectMethod
        
        of = JSONObjectFactory.get_instance(proxy,
                "TestType",
                object_uuid,
                "dc=test,dc=de",
                "tests.common.components.test_jsonrpc_proxy.TestType",
                ("testfunction"),
                ("attr1", "attr2"),
                {"attr1": "Data1", "attr2": "Data2"})
        assert of.uuid == object_uuid
        assert of.dn == "dc=test,dc=de"
        assert of.testfunction("required parameter") == "success"
        assert of.attr1 == "Data1"
        assert of.attr2 == "Data2"
        with pytest.raises(AttributeError):
            of.attr3
        
        of.attr2 = "Data"
        assert of.attr2 == "Data"
        with pytest.raises(AttributeError):
            of.attr3 = "TEST"
        
        assert repr(of) == object.__getattribute__(of, "ref") == object_uuid
