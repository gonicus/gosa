# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.
from uuid import uuid4
from unittest import TestCase, mock
from gosa.client.mqtt_service import *
from gosa.common import Environment
from gosa.common.utils import stripNs


class MQTTHandlerMock(mock.MagicMock):
    callback = None

    def set_subscription_callback(self, cb):
        self.callback = cb

    def simulate_message(self, topic, message):
        self.callback(topic, message)

mocked_handler = MQTTHandlerMock()


@mock.patch.dict("gosa.client.mqtt_service.PluginRegistry.modules", {'MQTTClientHandler': mocked_handler})
class ClientMqttServiceTestCase(TestCase):

    def setUp(self):
        self.mqtt = MQTTClientService()
        self.mqtt.time_int = 0
        with mock.patch.dict("gosa.client.mqtt_service.PluginRegistry.modules", {'MQTTClientHandler': mocked_handler}):
            self.mqtt.serve()
        self.env = Environment.getInstance()

    def test_handle_message(self):
        topic = "%s/client/%s" % (self.env.domain, self.env.uuid)
        with mock.patch.object(self.mqtt, "commandReceived") as m:
            mocked_handler.simulate_message(topic, "{test}")
            m.assert_called_with(topic, "{test}")

        e = EventMaker()
        msg = e.Event(e.Unknown)
        with mock.patch.object(self.mqtt.log, "debug") as m:
            # unhandled message
            mocked_handler.simulate_message(topic, etree.tostring(msg))
            assert m.called

        with mock.patch.object(self.mqtt.log, "error") as m:
            mocked_handler.simulate_message(topic, "<askkl><kmnkl&A&>")
            assert m.called

        msg = e.Event(e.ClientPoll())

        with mock.patch("gosa.client.mqtt_service.zope.event.notify") as m,\
                mock.patch("gosa.client.mqtt_service.random.randint", return_value=0):
            mocked_handler.simulate_message(topic, etree.tostring(msg))
            args, kwargs = m.call_args
            assert isinstance(args[0], Resume)
            assert mocked_handler.send_event.called

    def test_commandReceived(self):
        topic = "%s/client/%s/%s" % (self.env.domain, self.env.uuid, uuid4())

        with mock.patch.object(self.mqtt.log, "error") as m:
            self.mqtt.commandReceived(topic, "{'id'}")
            assert m.called
            args, kwargs = mocked_handler.send_message.call_args
            assert kwargs['topic'] == "%s/to-backend" % topic
            sent_message = loads(args[0])
            assert sent_message['result'] is None

        # key error
        mocked_handler.reset_mock()
        self.mqtt.commandReceived(topic, '{"id": "0", "params": []}')
        args, kwargs = mocked_handler.send_message.call_args
        assert kwargs['topic'] == "%s/to-backend" % topic
        sent_message = loads(args[0])
        assert sent_message['result'] is None

        # key error
        mocked_handler.reset_mock()
        self.mqtt.commandReceived(topic, '{"id": "0", "method": "unknown_method", "params": []}')
        args, kwargs = mocked_handler.send_message.call_args
        assert kwargs['topic'] == "%s/to-backend" % topic
        sent_message = loads(args[0])
        assert sent_message['result'] is None

        # real call
        mocked_handler.reset_mock()
        self.mqtt.commandReceived(topic, '{"id": "0", "method": "getMethods", "params": []}')
        args, kwargs = mocked_handler.send_message.call_args
        assert kwargs['topic'] == "%s/to-backend" % topic

    def test_reAnnounce(self):
        mocked_handler.reset_mock()
        self.mqtt.reAnnounce()
        args, kwargs = mocked_handler.send_event.call_args
        assert stripNs(args[0].xpath('/g:Event/*', namespaces={'g': "http://www.gonicus.de/Events"})[0].tag) == "UserSession"

    def test_ping(self):
        mocked_handler.reset_mock()
        # just wait a second and test if the first ping has been sent
        time.sleep(1)
        args, kwargs = mocked_handler.send_event.call_args
        assert stripNs(args[0].xpath('/g:Event/*', namespaces={'g': "http://www.gonicus.de/Events"})[0].tag) == "ClientPing"
