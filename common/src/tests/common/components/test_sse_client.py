#!/usr/bin/python3

import unittest, pytest
from unittest import mock
from gosa.common.components.sse_client import *

class SSEClientTestCase(unittest.TestCase):
    def test_Event(self):
        e = Event()
        e.id = "TESTID"
        e.name = "TESTNAME"
        e.data = { "test": "value" }
        assert repr(e) == "Event\n  id: TESTID\n  name: TESTNAME\n  data:\n\t{'test': 'value'}"

    @mock.patch("gosa.common.components.sse_client.logging")
    @mock.patch("gosa.common.components.sse_client.httpclient")
    def test_BaseSseClient(self, httpclientMock, loggingMock):
        httpClient = unittest.mock.MagicMock()
        httpclientMock.AsyncHTTPClient.return_value = httpClient
        
        logger = unittest.mock.MagicMock()
        loggingMock.getLogger.return_value = logger
        
        client = BaseSseClient()
        
        httpclientMock.AsyncHTTPClient.configure.assert_called_once_with("tornado.curl_httpclient.CurlAsyncHTTPClient")
        httpclientMock.AsyncHTTPClient.assert_called_once_with()
        
        assert client.log == logger
        assert client.connect_timeout == DEFAULT_CONNECT_TIMEOUT
        assert client.client == httpClient
        
        return client

    @mock.patch("gosa.common.components.sse_client.GosaHTTPRequest")
    @mock.patch("gosa.common.components.sse_client.Thread")
    def test_connect(self, threadMock, httpRequestMock):
        sseClient = self.test_BaseSseClient()
        
        connect_url = "http://localhost/test"
        
        thread = unittest.mock.MagicMock()
        threadMock.return_value = thread
        request = object()
        httpRequestMock.return_value = request
        connection = object()
        sseClient.client.fetch.return_value = connection
        
        assert sseClient.connect(connect_url) == connection
        assert getattr(sseClient, "connection", None) == connection
        
        threadMock.assert_called_once_with(target=sseClient.start)
        thread.start.assert_called_once_with()
        sseClient.client.fetch.assert_called_once_with(request, sseClient.handle_request)
        httpRequestMock.assert_called_once_with(url=connect_url,
                method='GET',
                request_timeout=0,
                connect_timeout=sseClient.connect_timeout,
                streaming_callback=sseClient.parse_event)
        
        # Removes the old connection
        newConnection = object()
        sseClient.client.fetch.return_value = newConnection
        
        old_connection = getattr(sseClient, "connection")
        sseClient.connect(connect_url)
        assert getattr(sseClient, "connection") != old_connection
        
        return sseClient
        
    @mock.patch("gosa.common.components.sse_client.IOLoop")
    def test_start(self, ioloopMock):
        instance = unittest.mock.MagicMock()
        ioloopMock.instance.return_value = instance
        
        sseClient = self.test_BaseSseClient()
        sseClient.start()
        
        instance.start.assert_called_once_with()
        ioloopMock.instance.assert_called_once_with()
    
    @mock.patch("gosa.common.components.sse_client.IOLoop")
    def test_handle_request(self, ioloopMock):
        instance = unittest.mock.MagicMock()
        ioloopMock.instance.return_value = instance
        
        sseClient = self.test_BaseSseClient()
        
        response = unittest.mock.MagicMock()
        response.body = "Some data"
        response.error = ""
        
        sseClient.handle_request(response)
        sseClient.log.debug.assert_called_once_with(response.body)
        instance.stop.assert_called_once_with()
        ioloopMock.instance.assert_called_once_with()
        
        response.error = "description of failure"
        sseClient.handle_request(response)
        sseClient.log.error.assert_called_once_with("Error: %s" % response.error)
        instance.stop.assert_called_with()
        ioloopMock.instance.assert_called_with()
    
    def test_close(self):
        sseClient = self.test_BaseSseClient()
        with pytest.raises(RuntimeError):
            sseClient.close()
        sseClient = self.test_connect()
        assert getattr(sseClient, "connection", None)
        sseClient.close()
        assert getattr(sseClient, "connection", None) == None
    
    def test_parse_event(self):
        import uuid
        id = str(uuid.uuid4())
        with unittest.mock.patch("gosa.common.components.sse_client.BaseSseClient.on_event") as onEventMock:
            sseClient = self.test_BaseSseClient()
            sseClient.parse_event(("id: %s\nevent: Event name\ndata: somedata" % id).encode())
            
            def validate(e):
                assert e.id == id
                assert e.name == "Event name"
                assert e.data == "somedata\nmore data"
            onEventMock.side_effect = validate
            sseClient.parse_event(("id: %s\nevent: Event name\ndata: somedata\ndata: more data" % id).encode())
            assert onEventMock.call_count == 2
            
            def validate(e):
                assert e.id == id
                assert e.name == None
                assert e.data == "somedata"
            onEventMock.side_effect = validate
            sseClient.parse_event(("id: %s\ndata: somedata" % id).encode())
            assert onEventMock.call_count == 3
            
            def validate(e):
                assert e.id == id
                assert e.name == "Event name"
                assert e.data == {"some": "json", "data": [1, 2, 3]}
            onEventMock.side_effect = validate
            sseClient.parse_event(("""id: %s\nevent: Event name\ndata: {"some": "json", "data": [1, 2, 3]}""" % id).encode())
            assert onEventMock.call_count == 4
    def test_on_event(self):
        sseClient = self.test_BaseSseClient()
        e = Event()
        with pytest.raises(NotImplementedError):
            sseClient.on_event(e)
        
