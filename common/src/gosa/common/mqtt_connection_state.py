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
    Handle MQTT connection states of the participants (backend, proxies).
    hello and goodbye events are send to the default mqtt broker:

    backend <-> default backend broker <-> proxy <-> default proxy broker <-> clients

    .. NOTE:
        Client connections maintained by ClientLeave and ClientAnnounce events
        as those events can have additional information about the clients, needed by GOsa.

    """
    _priority_ = 90
    __active_connections = {}

    def __init__(self):
        self.env = Environment.getInstance()
        self.topic = "%s/bus" % self.env.domain
        super(MQTTConnectionHandler, self).__init__()
        self.e = EventMaker()

        self.client_id = self.env.core_uuid
        self.client_type = "proxy" if self.env.mode == "proxy" else "backend"

        self.hello = self.e.Event(self.e.BusClientState(
            self.e.Id(self.client_id),
            self.e.State('enter'),
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

        # proxies and backend must announce themselves
        self.send_event(self.hello, self.topic, qos=1)

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

                    if client_state == "enter":
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


class IBusClientAvailability(Interface):  # pragma: nocover

    def __init__(self, obj):
        pass


@implementer(IBusClientAvailability)
class BusClientAvailability(object):

    def __init__(self, client_id, state, type):
        self.client_id = client_id
        self.state = state
        self.type = type
