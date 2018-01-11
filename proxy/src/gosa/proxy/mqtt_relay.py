from lxml import objectify, etree

from zope.interface import implementer

from gosa.common import Environment
from gosa.common.components import PluginRegistry
from gosa.common.components.mqtt_handler import MQTTHandler
from gosa.common.event import EventMaker
from gosa.common.handler import IInterfaceHandler


@implementer(IInterfaceHandler)
class MQTTRelayService(object):
    """
     This service acts as a proxy between the backend and proxy MQTT brokers
     to forward messages from one to the other.

     In detail this service listens to (event-)messages from the backend to the clients on the backends MQTT broker
     and forwards then to the clients (via the proxies MQTT broker) and the other way around.
    """

    _priority_ = 10
    backend_mqtt = None
    proxy_mqtt = None

    def __init__(self):
        self.env = Environment.getInstance()

    def serve(self):
        self.backend_mqtt = MQTTHandler(
            host=self.env.config.get("backend.mqtt-host"),
            port=self.env.config.getint("backend.mqtt-port", default=1883))

        # subscribe to all client relevant topics
        self.backend_mqtt.get_client().add_subscription("%s/client/#" % self.env.domain, qos=1)
        self.backend_mqtt.set_subscription_callback(self._handle_backend_message)

        e = EventMaker()
        goodbye = e.Event(e.ClientLeave(e.Id(self.env.core_uuid)))
        self.backend_mqtt.will_set("%s/proxy" % self.env.domain, goodbye, qos=1)

        self.proxy_mqtt = MQTTHandler(
            host=self.env.config.get("mqtt.host"),
            port=self.env.config.getint("mqtt.port", default=1883))
        self.proxy_mqtt.get_client().add_subscription("%s/client/#" % self.env.domain, qos=1)
        self.proxy_mqtt.set_subscription_callback(self._handle_proxy_message)

    def _handle_backend_message(self, topic, message):
        """ forwards backend messages to proxy MQTT """
        self.proxy_mqtt.send_message(message, topic, qos=1)
        if message[0:1] != "{":
            # event received
            try:
                xml = objectify.fromstring(message)
                if hasattr(xml, "ClientPoll"):
                    self.__handleClientPoll()

            except etree.XMLSyntaxError as e:
                self.log.error("Message parsing error: %s" % e)

    def _handle_proxy_message(self, topic, message):
        """ forwards backend messages to proxy MQTT """
        self.backend_mqtt.send_message(message, topic, qos=1)

    def __handleClientPoll(self):
        """ register proxy-backend again """
        index = PluginRegistry.getInstance("ObjectIndex")
        index.registerProxy()

    def close(self):
        self.backend_mqtt.close()
        self.proxy_mqtt.close()