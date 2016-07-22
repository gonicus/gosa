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
from urllib.parse import urlparse
from gosa.common.components.mqtt_proxy import MQTTServiceProxy
from gosa.common import Environment


class MQTTClientHandler(object):
    """
    This class handles the MQTT connection, incoming and outgoing connections
    and allows event callback registration.
    """
    _conn = None
    __capabilities = {}
    __peers = {}
    _eventProvider = None
    __proxy = None
    url = None
    joined = False

    def __init__(self):
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
        self.keepalive = self.env.config.get('mqtt.keepalive', default=60)
        self.domain = self.env.config.get('mqtt.domain', default="gosa")
        self.dns_domain = socket.getfqdn().split('.', 1)[1]

        # Check if credentials are supplied
        if not self.env.config.get("mqtt.key"):
            raise Exception("no key supplied - please join the client")

        # Configure system
        user = self.env.uuid
        key = self.env.config.get('mqtt.key')

        # Make proxy connection
        self.log.info("using service '%s:%s'" % (self.host, self.port))
        self.__proxy = MQTTServiceProxy(self.host, port=self.port, keepalive=self.keepalive)

        self.__proxy.authenticate(user, key)

        # add subscriptions
        self.__proxy.add_subscription("%s/client/broadcast" % self.domain)
        self.__proxy.add_subscription("%s/client/%s" % (self.domain, user))
        self.__proxy.add_subscription("%s/client/%s/#" % (self.domain, user))

        # Start connection
        self.start()

    def set_subscription_callback(self, callback):
        self.__proxy.set_subscription_callback(callback)

    def get_proxy(self):
        return self.__proxy

    def send_message(self, data, topic=None):
        """ Send message via proxy to mqtt. """
        if not isinstance(data, str):
            data = etree.tostring(data)
        if topic is None:
            topic = "%s/client/%s" % (self.domain, self.env.uuid)
        return self.__proxy.publish(topic, data)

    def start(self):
        """
        Enable MQTT connection. This method puts up the event processor and
        sets it to "active".
        """
        self.log.debug("enabling MQTT connection")

        # Create initial broker connection
        self.__proxy.connect()

    def close(self):
        self.log.debug("shutting down MQTT client handler")
        if self.__proxy:
            self.__proxy.disconnect()

    def __del__(self):
        self.close()
