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
from gosa.common.event import EventMaker
from tornado.concurrent import Future
from tornado.testing import gen_test, AsyncTestCase
from unittest import mock, TestCase
from gosa.common.components.mqtt_handler import *


class MqttHandlerTestCase(AsyncTestCase):

    def setUp(self):
        super(MqttHandlerTestCase, self).setUp()
        with mock.patch("gosa.common.components.mqtt_handler.MQTTClient"):
            self.mqtt = MQTTHandler()

    def tearDown(self):
        super(MqttHandlerTestCase, self).tearDown()
        if hasattr(self, "mqtt"):
            self.mqtt.get_client().reset_mock()

    def test_set_subscription_callback(self):
        self.mqtt.set_subscription_callback("test")
        self.mqtt.get_client().set_subscription_callback.assert_called_with("test")

    def test_send_message(self):
        self.mqtt.send_message("message", "test/topic")
        self.mqtt.get_client().publish.assert_called_with("test/topic", "message", qos=0, proxied=False)

    def test_send_event(self):
        e = EventMaker()
        event = e.Event(e.ClientPoll())
        self.mqtt.send_event(event, "test/topic")
        self.mqtt.get_client().publish.assert_called_with("test/topic", etree.tostring(event, pretty_print=True).decode(), qos=0, proxied=False)

    @gen_test
    def test_send_sync_message(self):
        response = Future()
        self.mqtt.get_client().get_sync_response.return_value = response

        def send():
            response.set_result("result")

        timer = Timer(0.1, send)
        timer.start()
        res = yield self.mqtt.send_sync_message("message", "test/topic")
        assert res == "result"

    def test_close(self):
        self.mqtt.close()
        assert self.mqtt.get_client().disconnect.called

    def test_del(self):
        client = self.mqtt.get_client()
        del self.mqtt
        assert client.disconnect.called


class MqttHandlerInitTestCase(TestCase):

    @mock.patch("gosa.common.components.mqtt_handler.MQTTClient")
    def test_init(self, m_client):
        with mock.patch("gosa.common.components.mqtt_handler.Environment.getInstance") as m_env, \
                mock.patch("gosa.common.components.mqtt_handler.find_bus_service", return_value=[('discovered_host', 1000)]) as m_find:
            m_env.return_value.config.get.return_value = None
            mqtt = MQTTHandler()
            assert mqtt.host == "discovered_host"
            assert mqtt.port == 1000

            m_find.return_value = None
            with pytest.raises(Exception):
                MQTTHandler()

        env = Environment.getInstance()

        def get_conf(key, default=None):
            if key == "jsonrpc.key":
                return None
            elif key == "mqtt.host":
                return "localhost"
            elif key == "mqtt.port":
                return 1883
            elif key == "mqtt.keepalive":
                return 60
            else:
                env.get.config(key, default=default)

        m_env = mock.MagicMock()
        del m_env.core_key
        m_env.config.get.side_effect = get_conf

        with mock.patch("gosa.common.components.mqtt_handler.Environment.getInstance", return_value=m_env),\
                pytest.raises(Exception):
            MQTTHandler()
