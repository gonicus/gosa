import logging

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

     In addition to that this service also handles events sent from the backend to the proxy (those are not forwarded
     to the clients)
    """

    _priority_ = 10
    backend_mqtt = None
    proxy_mqtt = None

    def __init__(self):
        self.env = Environment.getInstance()
        self.log = logging.getLogger(__name__)

    def serve(self):
        self.backend_mqtt = MQTTHandler(
            host=self.env.config.get("backend.mqtt-host"),
            port=self.env.config.getint("backend.mqtt-port", default=1883))

        # subscribe to all client relevant topics
        self.backend_mqtt.get_client().add_subscription("%s/client/#" % self.env.domain, qos=1)
        # subscribe to proxy topic
        self.backend_mqtt.get_client().add_subscription("%s/proxy" % self.env.domain, qos=1)
        self.backend_mqtt.set_subscription_callback(self._handle_backend_message)

        # set our last will and testament
        e = EventMaker()
        goodbye = e.Event(e.ClientLeave(e.Id(self.env.core_uuid)))
        self.backend_mqtt.will_set("%s/proxy" % self.env.domain, goodbye, qos=1)

        # connect to the proxy MQTT broker (where the clients are listening)
        self.proxy_mqtt = MQTTHandler(
            host=self.env.config.get("mqtt.host"),
            port=self.env.config.getint("mqtt.port", default=1883))
        self.proxy_mqtt.get_client().add_subscription("%s/client/#" % self.env.domain, qos=1)
        self.proxy_mqtt.set_subscription_callback(self._handle_proxy_message)

    def _handle_backend_message(self, topic, message):
        """ forwards backend messages to proxy MQTT and handles received events"""

        forward = not topic.startswith("%s/proxy" % self.env.domain)
        if message[0:1] != "{":
            # event received
            try:
                xml = objectify.fromstring(message)
                if hasattr(xml, "ClientPoll"):
                    self.__handleClientPoll()
                elif hasattr(xml, "Trigger"):
                    if xml.Trigger.Type == "ACLChanged":
                        self.log.debug("ACLChanged trigger received, reloading ACLs")
                        resolver = PluginRegistry.getInstance("ACLResolver")
                        resolver.load_acls()
                    else:
                        self.log.warning("unhandled Trigger event of type: %s received" % xml.Trigger.Type)

            except etree.XMLSyntaxError as e:
                self.log.error("Message parsing error: %s" % e)

        if forward is True:
            self.proxy_mqtt.send_message(message, topic, qos=1)

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

    def stop(self):
        self.close()
        self.backend_mqtt = None
        self.proxy_mqtt = None
