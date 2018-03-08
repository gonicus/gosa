# This file is part of the GOsa project.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

"""
The *MQTTClientService* is responsible for connecting the *client* to the MQTT
bus, registers the required queues, listens for commands on that queues
and dispatches incoming commands to the :class:`clacks.client.command.CommandRegistry`.

**Queues**

Every client has a individual queue. It is constructed of these components::

    {domain}.client.{uuid}

The client can publish and subscribe ti this queue.

There is another broadcasting queue for all clients::

    {domain}.client.broadcast

The client can subscribe to this queue, but only the server can publish to that queue.

**Events**

The gosa client produces a **ClientAnnounce** event on startup which tells
the backend about the client capabilities (commands it provides) and
some hardware information.

This information is re-send when the client receives a **ClientPoll** event,
which is generated by the backend.

On client shutdown, a **ClientLeave** is emitted to tell the backend that
the client has passed away.
"""
import sys
import netifaces #@UnresolvedImport
import traceback
import logging
import random
import time
import zope.event
import datetime
from lxml import objectify, etree
from threading import Timer
from netaddr import IPNetwork
from zope.interface import implementer
from gosa.common.gjson import loads, dumps
from gosa.common.components.jsonrpc_utils import BadServiceRequest
from gosa.common.handler import IInterfaceHandler
from gosa.common.components.registry import PluginRegistry
from gosa.common.event import EventMaker
from gosa.common import Environment
from gosa.client.event import Resume


@implementer(IInterfaceHandler)
class MQTTClientService(object):
    """
    Internal class to serve all available queues and commands to
    the MQTT broker.
    """
    _priority_ = 10

    # Time instance that helps us preventing re-announce-event flooding
    time_obj = None
    time_int = 3
    client = None
    __last_announce = None

    def __init__(self):
        env = Environment.getInstance()
        self.log = logging.getLogger(__name__)
        self.log.debug("initializing MQTT service provider")
        self.env = env
        self.__cr = None
        e = EventMaker()
        self.goodbye = e.Event(e.ClientLeave(
            e.Id(Environment.getInstance().uuid)
        ))

    def _handle_message(self, topic, message):
        if message[0:1] == "{":
            # RPC command
            self.commandReceived(topic, message)
        else:
            # event received
            try:
                xml = objectify.fromstring(message)
                if hasattr(xml, "ClientPoll"):
                    self.__handleClientPoll()
                else:
                    self.log.debug("unhandled event received '%s'" % xml.getchildren()[0].tag)
            except etree.XMLSyntaxError as e:
                self.log.error("Message parsing error: %s" % e)

    def serve(self):
        """ Start MQTT service for this gosa service provider. """
        # Load MQTT and Command registry instances
        self.client = PluginRegistry.getInstance('MQTTClientHandler')
        self.client.get_client().add_connection_listener(self._on_connection_change)
        self.__cr = PluginRegistry.getInstance('ClientCommandRegistry')

        self.client.set_subscription_callback(self._handle_message)

    def _on_connection_change(self, connected):
        if connected is True:
            if self.__last_announce is None or self.__last_announce < (datetime.datetime.now() - datetime.timedelta(minutes=5)):
                self.__announce(send_client_announce=True, send_user_session=True)

            # Send a ping on a regular base
            if self._ping_job is None:
                timeout = float(self.env.config.get('client.ping-interval', default=600))
                sched = PluginRegistry.getInstance("SchedulerService").getScheduler()
                self._ping_job = sched.add_interval_job(self.__ping, seconds=timeout, start_date=datetime.datetime.now() + datetime.timedelta(seconds=1))
        else:
            if self._ping_job is not None:
                sched = PluginRegistry.getInstance("SchedulerService").getScheduler()
                sched.unschedule_job(self._ping_job)
                self._ping_job = None

    def stop(self):
        self.client.send_event(self.goodbye, qos=1)
        self.client.close()

    def __ping(self):
        e = EventMaker()
        info = e.Event(e.ClientPing(e.Id(self.env.uuid)))
        self.client.send_event(info)

    def reAnnounce(self):
        """
        Re-announce signature changes to the agent.

        This method waits a given amount of time and then sends re-sends
        the client method-signatures.
        """
        if self.__cr:

            # Cancel running jobs
            if self.time_obj:
                self.time_obj.cancel()

            self.time_obj = Timer(self.time_int, self._reAnnounce)
            self.time_obj.start()

    def _reAnnounce(self):
        """
        Re-announces the client signatures
        """
        self.__announce(send_client_announce=False, send_user_session=False)

    def commandReceived(self, topic, message):
        """
        Process incoming commands, coming in with session and message
        information.

        ================= ==========================
        Parameter         Description
        ================= ==========================
        message           Received MQTT message
        ================= ==========================

        Incoming messages are coming from an
        :class:`gosa.common.components.mqtt_proxy.MQTTServiceProxy`. The command
        result is written to the '<domain>.client.<client-uuid>' queue.
        """
        err = None
        res = None
        name = None
        args = None
        kwargs = None
        id_ = ''

        response_topic = "%s/response" % "/".join(topic.split("/")[0:4])

        try:
            req = loads(message)
        except Exception as e:
            err = str(e)
            self.log.error("ServiceRequestNotTranslatable: %s" % err)
            req = {'id': topic.split("/")[-2]}

        if err is None:
            try:
                id_ = req['id']
                name = req['method']
                args = req['params']
                kwargs = req['kwparams']

            except KeyError as e:
                self.log.error("KeyError: %s" % e)
                err = str(BadServiceRequest(message))
        self.log.debug("received call [%s] for %s: %s(%s,%s)" % (id_, topic, name, args, kwargs))

        # Try to execute
        if err is None:
            try:
                res = self.__cr.dispatch(name, *args, **kwargs)
            except Exception as e:
                err = str(e)

                # Write exception to log
                exc_type, exc_value, exc_traceback = sys.exc_info()
                self.log.error(traceback.format_exception(exc_type, exc_value, exc_traceback))

        self.log.debug("returning call [%s]: %s / %s" % (id_, res, err))

        response = dumps({"result": res, "id": id_})

        # Get rid of it...
        self.client.send_message(response, topic=response_topic)

    def __handleClientPoll(self):
        delay = random.randint(0, 30)
        self.log.debug("received client poll - will answer in %d seconds" % delay)
        time.sleep(delay)
        self.__announce(send_client_announce=True, send_user_session=True)

        # Send a resume to all registered plugins
        zope.event.notify(Resume())

    def __announce(self, send_client_announce=False, send_user_session=True):
        e = EventMaker()

        # Assemble network information
        more = []
        netinfo = []
        self.__last_announce = datetime.datetime.now()
        for interface in netifaces.interfaces():
            i_info = netifaces.ifaddresses(interface)

            # Skip lo interfaces
            if not netifaces.AF_INET in i_info:
                continue

            # Skip lo interfaces
            if not netifaces.AF_LINK in i_info:
                continue
            if i_info[netifaces.AF_LINK][0]['addr'] == '00:00:00:00:00:00':
                continue

            # Assemble ipv6 information
            ip6 = ""
            if netifaces.AF_INET6 in i_info:
                ip = IPNetwork("%s/%s" % (i_info[netifaces.AF_INET6][0]['addr'].split("%", 1)[0],
                                        i_info[netifaces.AF_INET6][0]['netmask']))
                ip6 = str(ip)

            netinfo.append(
                e.NetworkDevice(
                    e.Name(interface),
                    e.IPAddress(i_info[netifaces.AF_INET][0]['addr']),
                    e.IPv6Address(ip6),
                    e.MAC(i_info[netifaces.AF_LINK][0]['addr']),
                    e.Netmask(i_info[netifaces.AF_INET][0]['netmask']),
                    e.Broadcast(i_info[netifaces.AF_INET][0]['broadcast'])))

        more.append(e.NetworkInformation(*netinfo))

        # Build event
        if send_client_announce is True:
            info = e.Event(
                e.ClientAnnounce(
                    e.Id(self.env.uuid),
                    e.Name(self.env.id),
                    *more))

            self.client.send_event(info, qos=1)

        # Assemble capabilities
        more = []
        caps = []
        for command, dsc in self.__cr.commands.items():
            caps.append(
                e.ClientMethod(
                e.Name(command),
                e.Path(dsc['path']),
                e.Signature(','.join(dsc['sig'])),
                e.Documentation(dsc['doc'])))
        more.append(e.ClientCapabilities(*caps))

        info = e.Event(
            e.ClientSignature(
                e.Id(self.env.uuid),
                e.Name(self.env.id),
                *more))

        self.client.send_event(info, qos=1)

        if send_user_session is True:
            try:
                sk = PluginRegistry.getInstance('SessionKeeper')
                sk.sendSessionNotification()
            except:  # pragma: nocover
                pass
