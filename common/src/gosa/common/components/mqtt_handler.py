# This file is part of the clacks framework.
#
#  http://clacks-project.org
#
# Copyright:
#  (C) 2010-2012 GONICUS GmbH, Germany, http://www.gonicus.de
#
# License:
#  GPL-2: http://www.gnu.org/licenses/gpl-2.0.html
#
# See the LICENSE file in the project's top-level directory for details.

import socket
import logging
from lxml import etree
from gosa.common.components.mqtt_client import MQTTClient
from gosa.common import Environment


class MQTTHandler(object):
    """
    This class handles the MQTT connection, incoming and outgoing connections
    and allows event callback registration.
    """
    _conn = None
    __capabilities = {}
    __peers = {}
    _eventProvider = None
    __client = None
    url = None
    joined = False

    def __init__(self,loop_forever=False):
        """
        Construct a new MQTTClientHandler instance based on the configuration
        stored in the environment.

        @type env: Environment
        @param env: L{Environment} object
        """
        env = Environment.getInstance()
        self.log = logging.getLogger(__name__)
        self.log.debug("initializing MQTT client handler")
        self.env = env

        # Load configuration
        self.host = self.env.config.get('mqtt.host', default="localhost")
        self.port = self.env.config.get('mqtt.port', default=1883)
        self.keep_alive = self.env.config.get('mqtt.keepalive', default=60)
        self.domain = self.env.domain
        domain_parts = socket.getfqdn().split('.', 1)
        self.dns_domain = domain_parts[1] if len(domain_parts) == 2 else "local"

        # Check if credentials are supplied
        if not self.env.config.get("jsonrpc.key") and not hasattr(self.env, "core_key"):
            raise Exception("no key supplied - please join the client")

        # Configure system
        if hasattr(self.env, "core_uuid") and hasattr(self.env, "core_key"):
            user = self.env.core_uuid
            key = self.env.core_key
        else:
            user = self.env.uuid
            key = self.env.config.get('jsonrpc.key')

        # Make proxy connection
        self.log.info("using service '%s:%s'" % (self.host, self.port))
        self.__client = MQTTClient(self.host, port=self.port, keepalive=self.keep_alive, loop_forever=loop_forever)

        self.__client.authenticate(user, key)

        self.init_subscriptions()

        # Start connection
        self.start()

    def init_subscriptions(self):
        pass

    def set_subscription_callback(self, callback):
        self.__client.set_subscription_callback(callback)

    def get_client(self):
        return self.__client

    def send_message(self, data, topic):
        """ Send message via proxy to mqtt. """
        return self.__client.publish(topic, data)

    def send_event(self, event, topic):
        data = etree.tostring(event, pretty_print=True).decode()
        self.send_message(data, topic)

    def start(self):
        """
        Enable MQTT connection. This method puts up the event processor and
        sets it to "active".
        """
        self.log.debug("enabling MQTT connection")

        # Create initial broker connection
        self.__client.connect()

    def close(self):
        self.log.debug("shutting down MQTT client handler")
        if self.__client:
            self.__client.disconnect()

    def __del__(self):
        self.close()
