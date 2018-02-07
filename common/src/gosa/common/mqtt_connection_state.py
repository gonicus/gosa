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
import zope
from lxml import objectify, etree

from zope.interface import implementer, Interface

from gosa.common import Environment
from gosa.common.event import EventMaker
from gosa.common.components.mqtt_handler import MQTTHandler
from gosa.common.handler import IInterfaceHandler


@implementer(IInterfaceHandler)
class MQTTConnectionHandler(MQTTHandler):
    """
    Handle MQTT connection states of the participants (backend, proxies, clients).
    Clients can announce themselved in a 2-staged manner. First sending 'init' state
    and when they are able to handle requests from other clients they tell them by
    sending the 'ready' state.

    If a clients shuts down, it send the 'leave' state.

    backend <-> default backend broker <-> proxy <-> default proxy broker <-> clients

    .. NOTE:
        Client connections maintained by ClientLeave and ClientAnnounce events
        as those events can have additional information about the clients, needed by GOsa.
        But the clients also use this handler to be informed about active proxies/backends.

    """
    _priority_ = 0
    __active_connections = {}

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

        self.init = self.e.Event(self.e.BusClientState(
            self.e.Id(self.client_id),
            self.e.State('init'),
            self.e.Type(self.client_type)
        ))

        self.ready = self.e.Event(self.e.BusClientState(
            self.e.Id(self.client_id),
            self.e.State('ready'),
            self.e.Type(self.client_type)
        ))

        self.goodbye = self.e.Event(self.e.BusClientState(
            self.e.Id(self.client_id),
            self.e.State('leave'),
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
        self.send_event(self.goodbye, self.topic, qos=1)
        self.close()

    def init_subscriptions(self):
        """ add client subscriptions """
        self.log.info("MQTTConnectionHandler subscribing to '%s' on '%s'" % (self.topic, self.host))
        self.get_client().add_subscription(self.topic, qos=1)
        self.get_client().set_subscription_callback(self._handle_message)

    def _handle_message(self, topic, message):
        if message[0:1] != "{":
            # event received
            try:
                xml = objectify.fromstring(message)
                if hasattr(xml, "BusClientState"):
                    client_id = xml.BusClientState.Id.text
                    client_type = xml.BusClientState.Type.text
                    client_state = xml.BusClientState.State.text

                    zope.event.notify(BusClientAvailability(client_id, client_state, client_type))

                    if client_state in ["init", "ready"]:
                        if client_type not in self.__active_connections:
                            self.__active_connections[client_type] = []
                        self.__active_connections[client_type].append(client_id)
                    elif client_state == "leave":
                        if client_type in self.__active_connections and client_id in self.__active_connections[client_type]:
                            self.__active_connections[client_type].remove(client_id)
                elif hasattr(xml, "ClientPoll"):
                    # say hello
                    self.send_event(self.hello, self.topic, qos=1)

            except etree.XMLSyntaxError as e:
                self.log.error("Message parsing error: %s" % e)

    def __handle_events(self, event):
        """
        React on object modifications, send ready after index scan is finished
        """
        if event.__class__.__name__ == "IndexScanFinished":
            self.send_ready()


class IBusClientAvailability(Interface):  # pragma: nocover

    def __init__(self, obj):
        pass


@implementer(IBusClientAvailability)
class BusClientAvailability(object):

    def __init__(self, client_id, state, type):
        self.client_id = client_id
        self.state = state
        self.type = type
