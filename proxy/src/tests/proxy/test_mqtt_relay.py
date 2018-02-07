import uuid

from lxml import etree
from unittest import TestCase, mock

from gosa.proxy.mqtt_relay import MQTTRelayService

from gosa.common import Environment
from gosa.common.components import PluginRegistry
from gosa.common.event import EventMaker
from gosa.common.gjson import dumps


class MQTTRelayServiceTestCase(TestCase):

    def setUp(self):
        super(MQTTRelayServiceTestCase, self).setUp()
        self.env = Environment.getInstance()
        self.env.core_uuid = str(uuid.uuid4())
        self.service = MQTTRelayService()
        PluginRegistry.modules["ACLResolver"] = mock.MagicMock()
        PluginRegistry.modules["ObjectIndex"] = mock.MagicMock()
        PluginRegistry.modules["CommandRegistry"] = mock.MagicMock()
        self.service.serve()

    def tearDown(self):
        self.service.stop()
        super(MQTTRelayServiceTestCase, self).tearDown()

    def test_handle_backend_message(self):
        e = EventMaker()

        # send client poll
        with mock.patch.object(self.service.proxy_mqtt, "send_message") as mps:

            # send ACLChanged
            m_resolver = PluginRegistry.getInstance("ACLResolver")
            self.service._handle_backend_message("%s/proxy" % self.env.domain,
                                                 etree.tostring(e.Event(e.Trigger(e.Type("ACLChanged"))),
                                                                pretty_print=True).decode())
            assert m_resolver.load_acls.called
            assert not mps.called

            m_index = PluginRegistry.getInstance("ObjectIndex")
            self.service._handle_backend_message("%s/client/broadcast" % self.env.domain,
                                                 etree.tostring(e.Event(e.ClientPoll()),
                                                                pretty_print=True).decode())
            assert m_index.registerProxy.called
            assert mps.called
            mps.reset_mock()

            # send client RPC
            payload = dumps({"id": "mqttrpc", "method": "test", "params": []})
            topic = "%s/client/client_id/request_id/request" % self.env.domain
            self.service._handle_backend_message(topic, payload)
            mps.assert_called_with(payload, topic, qos=1)

    def test_handle_proxy_message(self):

        # send client poll
        with mock.patch.object(self.service.backend_mqtt, "send_message") as mbs:
            payload = dumps({"id": "mqttrpc", "result": "test"})
            topic = "%s/client/client_id/request_id/response" % self.env.domain
            self.service._handle_proxy_message(topic, payload)
            mbs.assert_called_with(payload, topic, qos=1)
