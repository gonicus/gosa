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
import thread
import logging
from lxml import etree
from urlparse import urlparse
from qpid.messaging import Connection
from qpid.messaging.util import auto_fetch_reconnect_urls
from qpid.messaging.exceptions import NotFound
from clacks.common.components import AMQPServiceProxy
from clacks.common.components.amqp import AMQPHandler, EventProvider
from clacks.common.components.zeroconf_client import ZeroconfClient
from clacks.common.utils import parseURL
from clacks.common import Environment

# Global lock
a_lock = thread.allocate_lock()


class AMQPClientHandler(AMQPHandler):
    """
    This class handles the AMQP connection, incoming and outgoing connections
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
        Construct a new AMQPClientHandler instance based on the configuration
        stored in the environment.

        @type env: Environment
        @param env: L{Environment} object
        """
        env = Environment.getInstance()
        self.log = logging.getLogger(__name__)
        self.log.debug("initializing AMQP client handler")
        self.env = env

        # Load configuration
        self.url = parseURL(self.env.config.get('amqp.url', None))
        self.domain = self.env.config.get('ampq.domain', default="org.clacks")
        self.dns_domain = socket.getfqdn().split('.', 1)[1]

        # Use zeroconf if there's no URL
        if self.url:
            o = urlparse(self.url['source'])

        else:
            url = ZeroconfClient.discover(['_amqps._tcp', '_amqp._tcp'], domain=self.domain)[0]
            o = urlparse(url)

            # pylint: disable=E1101
            self.domain = o.path[1::]

        # Configure system
        user = self.env.uuid

        key = self.env.config.get('amqp.key')
        if key:
            # pylint: disable=E1101
            self.url = parseURL('%s://%s:%s@%s%s' % (o.scheme, user, key, o.netloc, o.path))
        else:
            self.url = parseURL(url)

        # Make proxy connection
        self.log.info("using service '%s/%s'" % (self.url['host'], self.url['path']))
        self.__proxy = AMQPServiceProxy(self.url['source'])

        # Set params and go for it
        self.reconnect = self.env.config.get('amqp.reconnect', True)
        self.reconnect_interval = self.env.config.get('amqp.reconnect-interval', 3)
        self.reconnect_limit = self.env.config.get('amqp.reconnect-limit', 0)

        # Check if credentials are supplied
        if not self.env.config.get("amqp.key"):
            raise Exception("no key supplied - please join the client")

        # Start connection
        self.start()

    def get_proxy(self):
        return self.__proxy

    def sendEvent(self, data):
        """ Override original sendEvent. Use proxy instead. """
        if not isinstance(data, str):
            data = etree.tostring(data)

        return self.__proxy.sendEvent(data)

    def start(self):
        """
        Enable AMQP queueing. This method puts up the event processor and
        sets it to "active".
        """
        self.log.debug("enabling AMQP queueing")

        # Evaluate username
        user = self.env.uuid

        # Create initial broker connection
        url = "%s:%s" % (self.url['host'], self.url['port'])
        self._conn = Connection.establish(url, reconnect=self.reconnect,
            username=user,
            password=self.env.config.get("amqp.key"),
            transport=self.url['transport'],
            reconnect_interval=self.reconnect_interval,
            reconnect_limit=self.reconnect_limit)

        # Do automatic broker failover if requested
        if self.env.config.get('amqp.failover', default=False):
            auto_fetch_reconnect_urls(self._conn)

        # Create event provider
        try:
            self._eventProvider = EventProvider(self.env, self._conn)
        except NotFound as e:
            self.env.log.critical("queue has gone: %s" % str(e))
            self.env.requestRestart()

    def close(self):
        self.log.debug("shutting down AMQP client handler")
        if self._conn:
            self._conn.close()

    def __del__(self):
        self.close()
