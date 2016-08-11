#!/usr/bin/python3
# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.
from threading import Timer
import pytest
from tornado.testing import gen_test, AsyncTestCase
from unittest import mock
from gosa.common.components.mqtt_proxy import *


class MqttProxyTestCase(AsyncTestCase):

    @gen_test
    def test_call(self):
        with mock.patch("gosa.common.components.mqtt_proxy.MQTTHandler", spec=MQTTHandler) as m_handler:
            proxy = MQTTServiceProxy(mqttHandler=m_handler, serviceAddress="test/client", methods=['testCall'])

            with pytest.raises(JSONRPCException):
                yield proxy.testCall("arg", test="kwarg")

            with pytest.raises(NameError):
                yield proxy.unknownCall("arg")

            response = Future()
            m_handler.send_sync_message.return_value = response

            def send():
                response.set_result('{"result": "test"}')

            timer = Timer(0.1, send)
            timer.start()
            res = yield proxy.testCall("arg")
            args, kwargs = m_handler.send_sync_message.call_args

            content = loads(args[0])
            assert content['method'] == "testCall"
            assert content['params'] == ["arg"]
            assert content['id'] == "jsonrpc"
            assert args[1].startswith("test/client/")
            assert res == '{"result": "test"}'

            response = Future()
            m_handler.send_sync_message.return_value = response

            def send():
                response.set_result('{"error": "test error"}')

            with pytest.raises(JSONRPCException):
                timer = Timer(0.1, send)
                timer.start()
                yield proxy.testCall(test="arg")

    def test_getProxy(self):
        with mock.patch("gosa.common.components.mqtt_proxy.MQTTHandler", spec=MQTTHandler) as m_handler:
            proxy = MQTTServiceProxy(mqttHandler=m_handler, serviceAddress="test/client", methods=['testCall'])

            with mock.patch("gosa.common.components.mqtt_proxy.MQTTServiceProxy") as m_proxy:
                proxy.getProxy()
                m_proxy.assert_called_with(m_handler, "test/client", None, methods=['testCall'])

    @gen_test
    def test_get_methods(self):
        with mock.patch("gosa.common.components.mqtt_proxy.MQTTHandler", spec=MQTTHandler) as m_handler:
            response = Future()
            m_handler.send_sync_message.return_value = response

            def send():
                response.set_result('{"testCall": "test"}')

            timer = Timer(0.1, send)
            timer.start()

            proxy = MQTTServiceProxy(mqttHandler=m_handler, serviceAddress="test/client")

            res = yield proxy.testCall(test="arg")
            args, kwargs = m_handler.send_sync_message.call_args

            content = loads(args[0])
            assert content['method'] == "testCall"
            assert content['params'] == {'test': 'arg'}
            assert content['id'] == "jsonrpc"
            assert args[1].startswith("test/client/")
            assert res == '{"testCall": "test"}'

    def test_get_attr(self):
        with mock.patch("gosa.common.components.mqtt_proxy.MQTTHandler", spec=MQTTHandler) as m_handler:
            proxy = MQTTServiceProxy(mqttHandler=m_handler, serviceAddress="test/client", serviceName="test", methods=['testCall'])
            with mock.patch("gosa.common.components.mqtt_proxy.MQTTServiceProxy") as m_proxy:
                proxy.attribute
                m_proxy.assert_called_with(m_handler, "test/client", "test/attribute", methods=['testCall'])