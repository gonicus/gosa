import json
import logging
from urllib.parse import urlparse

from lxml import objectify, etree

from zope.interface import implementer

from gosa.backend.components.httpd import get_server_url
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
     and forwards them to the clients (via the proxies MQTT broker) and the other way around.

     In addition to that this service also handles events sent from the backend to the proxy (those are not forwarded
     to the clients).

     The message routing is done by the following rules:

     **Received from backend MQTT broker**

     * Subscribed to `<domain>/proxy` and `<domain>/client/#` topics
     * all messages with topic not starting with `<domain>/proxy` are forwarded to the proxy MQTT broker
     * `ClientPoll` and `Trigger` events are processed locally

     **Received from proxy MQTT broker**

     * Subscribed to`<domain>/client/#` topics
     * all messages are forwarded to the backend MQTT broker
     * (please note the the ClientService plugin
       is also subscribed to the proxy MQTT broker and handles the client messages locally)
    """

    _priority_ = 10
    backend_mqtt = None
    proxy_mqtt = None

    def __init__(self):
        self.env = Environment.getInstance()
        self.log = logging.getLogger(__name__)
        e = EventMaker()
        url = urlparse(get_server_url())
        self.goodbye = e.Event(e.BusClientState(e.Id(self.env.core_uuid), e.Hostname(url.hostname), e.Type("proxy"), e.State("leave")))
        self.hello = e.Event(e.BusClientState(e.Id(self.env.core_uuid), e.Hostname(url.hostname), e.Type("proxy"), e.State("ready")))

    def serve(self):
        self.backend_mqtt = MQTTHandler(
            host=self.env.config.get("backend.mqtt-host"),
            port=self.env.config.getint("backend.mqtt-port", default=1883),
            use_ssl=self.env.config.getboolean("backend.mqtt-ssl", default=True),
            ca_file=self.env.config.get("backend.mqtt-ca_file"),
            insecure=self.env.config.getboolean("backend.mqtt-insecure", default=None),
        )

        # subscribe to all client relevant topics
        self.backend_mqtt.get_client().add_subscription("%s/client/#" % self.env.domain, qos=1)
        # subscribe to proxy topic
        self.backend_mqtt.get_client().add_subscription("%s/proxy" % self.env.domain, qos=1)
        self.backend_mqtt.get_client().add_subscription("%s/bus" % self.env.domain, qos=1)
        self.backend_mqtt.set_subscription_callback(self._handle_backend_message)

        # set our last will and testament (on the backend broker)
        self.backend_mqtt.will_set("%s/bus" % self.env.domain, self.goodbye, qos=1)

        # connect to the proxy MQTT broker (where the clients are listening)
        self.proxy_mqtt = MQTTHandler(
            host=self.env.config.get("mqtt.host"),
            port=self.env.config.getint("mqtt.port", default=1883))
        self.proxy_mqtt.get_client().add_subscription("%s/client/#" % self.env.domain, qos=1)
        self.proxy_mqtt.get_client().add_subscription("%s/bus" % self.env.domain, qos=1)
        self.proxy_mqtt.set_subscription_callback(self._handle_proxy_message)

        PluginRegistry.getInstance("CommandRegistry").init_backend_proxy(self.backend_mqtt)

        self.backend_mqtt.send_event(self.hello, "%s/bus" % self.env.domain, qos=1)
        self.proxy_mqtt.send_event(self.hello, "%s/bus" % self.env.domain, qos=1)

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
                        checks = None
                        if hasattr(xml.Trigger, "Check") and len(xml.Trigger.Check) > 0:
                            try:
                                checks = json.loads(xml.Trigger.Check)
                            except Exception as e:
                                self.log.error("Error parsing ACLChanged-events Check content: %s" % str(e))
                        resolver.load_acls(checks)
                    else:
                        self.log.warning("unhandled Trigger event of type: %s received" % xml.Trigger.Type)

            except etree.XMLSyntaxError as e:
                self.log.error("Message parsing error: %s" % e)

        if forward is True:
            self.log.debug("forwarding message in topic '%s' to proxy MQTT broker: %s" % (topic, message[0:80]))
            self.proxy_mqtt.send_message(message, topic, qos=1, proxied=True)

    def _handle_proxy_message(self, topic, message):
        """ forwards proxy messages to backend MQTT """
        if message[0:1] != "{":
            # event received
            try:
                xml = objectify.fromstring(message)
                if hasattr(xml, "UserSession"):
                    # these events need to be handled differently when they are relayed by a proxy, so we flag them
                    self.log.debug("Flagging UserSession-Event in topic '%s' as Proxied" % topic)
                    elem = objectify.SubElement(xml.UserSession, "Proxied")
                    elem._setText("true")
                    message = etree.tostring(xml, pretty_print=True).decode('utf-8')

            except etree.XMLSyntaxError as e:
                self.log.error("Message parsing error: %s" % e)

        self.log.debug("forwarding message in topic '%s' to backend MQTT broker: %s" % (topic, message[0:80]))
        self.backend_mqtt.send_message(message, topic, qos=1, proxied=True)

    def __handleClientPoll(self):
        """ register proxy-backend again """
        index = PluginRegistry.getInstance("ObjectIndex")
        index.registerProxy()

    def close(self):
        self.backend_mqtt.close()
        self.proxy_mqtt.close()

    def stop(self):
        self.backend_mqtt.send_event(self.goodbye, "%s/bus" % self.env.domain, qos=1)
        self.close()
        self.backend_mqtt = None
        self.proxy_mqtt = None
