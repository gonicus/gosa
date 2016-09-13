# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

import socket
import logging
import asyncio
from lxml import etree
from gosa.common.components.mqtt_client import MQTTClient
from gosa.common.utils import find_bus_service
from gosa.common import Environment
from tornado import gen


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

    def __init__(self, autostart=True):
        """
        Construct a new MQTTClientHandler instance based on the configuration
        stored in the environment.

        @type env: Environment
        @param env: L{Environment} object
        """
        self.log = logging.getLogger(__name__)
        self.log.debug("initializing MQTT client handler")
        self.env = Environment.getInstance()

        # Load configuration
        self.host = self.env.config.get('mqtt.host')
        self.port = self.env.config.get('mqtt.port', default=1883)

        # Auto detect if possible
        if not self.host:
            svcs = find_bus_service()
            if svcs:
                self.host, self.port = svcs[0]

        # Bail out?
        if not self.host:
            self.log.error("no MQTT host available for bus communication")
            raise Exception("no MQTT host available")

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
        self.__client = MQTTClient(self.host, port=self.port, keepalive=self.keep_alive)

        self.__client.authenticate(user, key)

        self.init_subscriptions()

        if autostart:
            # Start connection
            self.start()

    def init_subscriptions(self): # pragma: nocover
        pass

    def set_subscription_callback(self, callback):
        self.__client.set_subscription_callback(callback)

    def get_client(self):
        return self.__client

    def send_message(self, data, topic, qos=0):
        """ Send message via proxy to mqtt. """
        return self.__client.publish(topic, data, qos=qos)

    def send_event(self, event, topic, qos=0):
        data = etree.tostring(event, pretty_print=True).decode('utf-8')
        self.send_message(data, topic, qos=qos)

    def will_set(self, topic, event, qos=0, retain=False):
        """
        Set a Will to be sent to the broker. If the client disconnects without calling disconnect(),
        the broker will publish the message on its behalf.
        """
        data = etree.tostring(event, pretty_print=True).decode('utf-8')
        self.__client.will_set(topic, data, qos, retain)

    @gen.coroutine
    def send_sync_message(self, data, topic):
        """Send request and return the response"""
        result = yield self.__client.get_sync_response(topic, data)
        raise gen.Return(result)

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
