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
from gosa.common.components.mqtt_client import *


class MqttClientTestCase(AsyncTestCase):

    def setUp(self):
        super(MqttClientTestCase, self).setUp()
        with mock.patch("gosa.common.components.mqtt_client.BaseClient"):
            self.mqtt = MQTTClient('localhost')

    def tearDown(self):
        super(MqttClientTestCase, self).tearDown()
        self.mqtt.client.reset_mock()

    def test_loop_forever(self):
        with mock.patch("gosa.common.components.mqtt_client.BaseClient"):
            mqtt = MQTTClient('localhost', loop_forever=True)
            mqtt.connect()
            assert mqtt.client.loop_forever.called

    def test_authenticate(self):
        self.mqtt.authenticate("uuid", "secret")
        self.mqtt.client.username_pw_set.assert_called_with("uuid", "secret")

    def test_connect(self):
        self.mqtt.connect()
        assert not self.mqtt.client.username_pw_set.called
        self.mqtt.client.connect.assert_called_with("localhost", port=1883, keepalive=60)
        self.mqtt.client.reset_mock()

        self.mqtt.connect(uuid="uuid", secret="secret")
        self.mqtt.client.username_pw_set.assert_called_with("uuid", "secret")
        self.mqtt.client.connect.assert_called_with("localhost", port=1883, keepalive=60)

    def test_disconnect(self):
        self.mqtt.disconnect()
        assert self.mqtt.client.disconnect.called
        assert self.mqtt.client.loop_stop.called

    def test_add_subscription(self):
        self.mqtt.add_subscription("test/topic")
        assert "test/topic" in self.mqtt.subscriptions
        assert not self.mqtt.client.subscribe.called

        self.mqtt.connected = True
        self.mqtt.client.subscribe.return_value = 0, 0
        self.mqtt.add_subscription("test/topic2")
        assert "test/topic2" in self.mqtt.subscriptions
        self.mqtt.client.subscribe.assert_called_with("test/topic2")
        assert self.mqtt.subscriptions['test/topic2']['subscribed'] is False
        self.mqtt.client.on_subscribe(None, None, 0, 1)
        assert self.mqtt.subscriptions['test/topic2']['subscribed'] is True
        assert self.mqtt.subscriptions['test/topic2']['granted_qos'] == 1

    def test_set_subscription_callback(self):
        self.mqtt.add_subscription("test/topic")
        self.mqtt.add_subscription("test/topic2")

        assert self.mqtt.subscriptions['test/topic']['callback'] is None
        assert self.mqtt.subscriptions['test/topic2']['callback'] is None

        self.mqtt.set_subscription_callback("test")
        assert self.mqtt.subscriptions['test/topic']['callback'] == "test"
        assert self.mqtt.subscriptions['test/topic2']['callback'] == "test"

    def test_remove_subscription(self):
        self.mqtt.add_subscription("test/topic")
        self.mqtt.add_subscription("test/topic2")

        assert "test/topic" in self.mqtt.subscriptions
        assert "test/topic2" in self.mqtt.subscriptions
        self.mqtt.remove_subscription("test/topic2")
        assert "test/topic2" not in self.mqtt.subscriptions
        assert not self.mqtt.client.unsubscribe.called

        self.mqtt.connected = True
        self.mqtt.remove_subscription("test/topic")
        self.mqtt.client.unsubscribe.assert_called_with("test/topic")

    def test_clear_subscriptions(self):
        self.mqtt.add_subscription("test/topic")
        self.mqtt.add_subscription("test/topic2")

        assert len(self.mqtt.subscriptions) == 2
        self.mqtt.clear_subscriptions()

        self.mqtt.client.unsubscribe.assert_called_with({"test/topic": 0, "test/topic2": 0}.keys())

    def test_publish(self):
        self.mqtt.client.publish.return_value = (mqtt.MQTT_ERR_NO_CONN, 0)
        with mock.patch.object(self.mqtt.log, "error") as m:
            self.mqtt.publish("test/topic", "message")
            assert m.called

        self.mqtt.client.publish.return_value = (mqtt.MQTT_ERR_SUCCESS, 0)
        self.mqtt.publish("test/topic", "message")
        args, kwargs = self.mqtt.client.publish.call_args
        assert args[0] == "test/topic"
        payload = loads(kwargs['payload'])
        assert payload['sender_id'] is None
        assert payload['content'] == "message"
        assert kwargs['qos'] == 0
        assert kwargs['retain'] is False
        assert 0 in self.mqtt._MQTTClient__published_messages

        self.mqtt.client.on_publish(None, None, 0)
        assert 0 not in self.mqtt._MQTTClient__published_messages

    def test_on_unsubscribe(self):
        self.mqtt.connected = True
        self.mqtt.client.subscribe.return_value = 0, 0
        self.mqtt.add_subscription("test/topic")
        self.mqtt.client.on_unsubscribe(None, None, 0)
        assert len(self.mqtt.subscriptions) == 0

    def test_on_connect(self):
        self.mqtt.add_subscription("test/topic")
        self.mqtt.client.subscribe.return_value = 0, 0
        self.mqtt.client.on_connect(None, None, None, mqtt.CONNACK_ACCEPTED)
        assert self.mqtt.connected
        self.mqtt.client.subscribe.assert_called_with("test/topic")

        self.mqtt.client.reset_mock()
        self.mqtt.connected = False
        self.mqtt.client.on_connect(None, None, None, mqtt.CONNACK_REFUSED_NOT_AUTHORIZED)
        assert not self.mqtt.connected
        assert not self.mqtt.client.subscribe.called

    def test_on_message(self):
        # set sender id
        self.mqtt.authenticate("admin", "secret")

        self.mqtt.add_subscription("test/+")

        # add message callback
        m_cb = mock.MagicMock()
        self.mqtt.set_subscription_callback(m_cb.callback)

        class MessageMock:
            payload = '{"sender_id": "admin", "content": "message content"}'
            topic = "test/topic"

        m_message = MessageMock()

        # message from myself
        self.mqtt.client.on_message(None, None, m_message)
        assert not m_cb.callback.called

        # message for unsubscribed topic
        m_message.payload = '{"sender_id": "backend", "content": "message content"}'
        m_message.topic = "unknown/topic"
        self.mqtt.client.on_message(None, None, m_message)
        assert not m_cb.callback.called

        # subscribed message, callback must be called
        m_message.topic = "test/topic"
        self.mqtt.client.on_message(None, None, m_message)
        m_cb.callback.assert_called_with("test/topic", "message content")

    def test_on_log(self):
        with mock.patch.object(self.mqtt.log, "debug") as m:
            self.mqtt.client.on_log(None, None, None, "log message")
            assert m.called

    @gen_test
    def test_get_sync_response(self):
        class MessageMock:
            payload = '{"sender_id": "backend", "content": "message content"}'
            topic = "test/topic/to-backend"

        self.mqtt.client.connected = True
        self.mqtt.client.subscribe.return_value = 0, 0
        self.mqtt.client.publish.return_value = (mqtt.MQTT_ERR_SUCCESS, 0)
        m_message = MessageMock()

        # test timeout
        with pytest.raises(JSONRPCException), \
                mock.patch("gosa.common.components.mqtt_client.Queue") as m_queue:
            m_queue.return_value.get.side_effect = QueueEmpty()
            res = yield self.mqtt.get_sync_response("test/topic", "message")

        def send():
            self.mqtt.client.on_message(None, None, m_message)

        timer = Timer(0.1, send)
        timer.start()
        res = yield self.mqtt.get_sync_response("test/topic", "message")

        assert res == "message content"


