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
from urllib.parse import urlparse

import zope
from lxml import objectify, etree

from zope.interface import implementer
from gosa.common import Environment, BusClientAvailability
from gosa.common.event import EventMaker
from gosa.common.components.mqtt_handler import MQTTHandler
from gosa.common.handler import IInterfaceHandler


@implementer(IInterfaceHandler)
class MQTTConnectionHandler(MQTTHandler):
    """
    Handle MQTT connection states of the participants (backend, proxies, clients).
    Clients can announce themselves in 2 stages. As soon as they are connected to the
    MQTT Broker they send the 'init' state.
    When they are able to handle requests from other clients they tell them by
    sending the 'ready' state.
    Those two states can be send right after each other when the client does need no
    initialization, but e.g. a backend need a certain amount of time after startup
    to build the index.

    If a client shuts down, it sends the 'leave' state.

    backend <-> default backend broker <-> proxy <-> default proxy broker <-> clients

    .. NOTE:
        Client connections maintained by ClientLeave and ClientAnnounce events
        as those events can have additional information about the clients, needed by GOsa.
        But the clients also use this handler to be informed about active proxies/backends.

    """
    _priority_ = 1
    __active_connections = {}
    __hostname = None

    def __init__(self):
        self.env = Environment.getInstance()
        self.topic = "%s/bus" % self.env.domain
        super(MQTTConnectionHandler, self).__init__(client_id_prefix="MQTTConnectionHandler")

        self.client_type = self.env.mode
        self.e = EventMaker()
        if hasattr(self.env, "core_uuid"):
            self.client_id = self.env.core_uuid
        else:
            self.client_id = self.env.uuid

        self.init = self.__gen_state_event('init')
        self.ready = self.__gen_state_event('ready')
        self.goodbye = self.__gen_state_event('leave')

    def __gen_state_event(self, state):
        if not self.__hostname and self.client_type in ['proxy', 'backend']:
            from gosa.backend.components.httpd import get_server_url
            url = urlparse(get_server_url())
            self.__hostname = url.hostname

        if self.client_type in ['proxy', 'backend']:
            return self.e.Event(self.e.BusClientState(
                self.e.Id(self.client_id),
                self.e.Hostname(self.__hostname),
                self.e.State(state),
                self.e.Type(self.client_type)
            ))
        else:
            return self.e.Event(self.e.BusClientState(
                self.e.Id(self.client_id),
                self.e.State(state),
                self.e.Type(self.client_type)
            ))

    def serve(self):
        # set last will
        self.will_set(self.topic, self.goodbye, qos=1)

        if self.client_type == "backend":
            zope.event.subscribers.append(self.__handle_events)
            self.wait_for_connection(self.send_init)
        else:
            self.wait_for_connection(self.send_ready)

    def send_init(self):
        self.log.info("MQTTConnectionHandler '%s' sending hello (init)" % self.client_type)
        self.send_event(self.init, self.topic, qos=1)

    def send_ready(self):
        self.log.info("MQTTConnectionHandler '%s' sending hello (ready)" % self.client_type)
        self.send_event(self.ready, self.topic, qos=1)

    def stop(self):
        self.log.info("MQTTConnectionHandler sending goodbye")
        self.send_event(self.goodbye, self.topic, qos=2)
        self.close()

    def init_subscriptions(self):
        """ add client subscriptions """
        self.log.info("MQTTConnectionHandler subscribing to '%s' on '%s'" % (self.topic, self.host))
        self.get_client().add_subscription(self.topic, qos=1, callback=self._handle_message)

    def _handle_message(self, topic, message):

        if message[0:1] == "<":
            # event received
            try:
                xml = objectify.fromstring(message)
                if hasattr(xml, "BusClientState"):
                    client_id = xml.BusClientState.Id.text
                    client_type = xml.BusClientState.Type.text
                    client_state = xml.BusClientState.State.text
                    hostname = xml.BusClientState.Hostname.text if hasattr(xml.BusClientState, 'Hostname') else None

                    state_changed = False
                    if client_state in ["init", "ready"]:
                        if client_type not in self.__active_connections:
                            self.__active_connections[client_type] = []
                        if client_id not in self.__active_connections[client_type]:
                            self.__active_connections[client_type].append(client_id)
                            state_changed = True
                    elif client_state == "leave":
                        if client_type in self.__active_connections and client_id in self.__active_connections[client_type]:
                            self.__active_connections[client_type].remove(client_id)
                            state_changed = True

                    if state_changed is True:
                        zope.event.notify(BusClientAvailability(client_id, client_state, client_type, hostname))

                elif hasattr(xml, "ClientPoll"):
                    # say hello
                    self.send_event(self.hello, self.topic, qos=1)

            except etree.XMLSyntaxError as e:
                self.log.error("Message parsing error: %s" % e)

    def __handle_events(self, event):
        """
        React on object modifications, send ready after index scan is finished
        """
        if event.__class__.__name__ == "IndexSyncFinished":
            self.send_ready()
