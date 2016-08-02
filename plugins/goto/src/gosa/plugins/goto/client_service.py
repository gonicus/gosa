# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

import re
import os
import string
import random
import hashlib
import ldap
import datetime
import logging
from uuid import uuid4
from copy import copy
from threading import Timer
from lxml import etree

from gosa.backend.components.jsonrpc_service import JsonRpcHandler
from gosa.common.components.mqtt_handler import MQTTHandler
from tornado import gen
from zope.interface import implementer
from gosa.common.components.jsonrpc_proxy import JSONRPCException
from gosa.common.handler import IInterfaceHandler
from gosa.common.event import EventMaker
from gosa.common import Environment
from gosa.common.utils import stripNs, N_
from gosa.common.error import GosaErrorHandler as C
from gosa.common.components.registry import PluginRegistry
from gosa.common.components.mqtt_proxy import MQTTServiceProxy
from gosa.common.components import Plugin
from gosa.common.components.command import Command
from gosa.backend.utils.ldap import LDAPHandler
from base64 import b64encode as encode
from Crypto.Cipher import AES

STATUS_SYSTEM_ON = "O"
STATUS_UPDATABLE = "u"
STATUS_UPDATING = "U"
STATUS_INVENTORY = "i"
STATUS_CONFIGURING = "C"
STATUS_INSTALLING = "I"
STATUS_VM_INITIALIZING = "V"
STATUS_WARNING = "W"
STATUS_ERROR = "E"
STATUS_OCCUPIED = "B"
STATUS_LOCKED = "L"
STATUS_BOOTING = "b"
STATUS_NEEDS_INITIAL_CONFIG = "P"
STATUS_NEEDS_REMOVE_CONFIG = "R"
STATUS_NEEDS_CONFIG = "c"
STATUS_NEEDS_INSTALL = "N"


# Register the errors handled  by us
C.register_codes(dict(
    DEVICE_EXISTS=N_("Device with hardware address '%(topic)s' already exists"),
    USER_NOT_UNIQUE=N_("User '%(topic)s' is not unique"),
    CLIENT_NOT_FOUND=N_("Client '%(topic)s' not found"),
    CLIENT_OFFLINE=N_("Client '%(topic)s' is offline"),
    CLIENT_METHOD_NOT_FOUND=N_("Client '%(topic)s' has no method %(method)s"),
    CLIENT_DATA_INVALID=N_("Invalid data '%(entry)s:%(data)s' for client '%(topic)s provided'"),
    CLIENT_TYPE_INVALID=N_("Device type '%(type)s' for client '%(topic)s' is invalid [terminal, workstation, server, sipphone, switch, router, printer, scanner]"),
    CLIENT_OWNER_NOT_FOUND=N_("Owner '%(owner)s' for client '%(topic)s' not found"),
    CLIENT_UUID_INVALID=N_("Invalid client UUID '%(topic)s'"),
    CLIENT_STATUS_INVALID=N_("Invalid status '%(status)s' for client '%(topic)s'")))


class GOtoException(Exception):
    pass


@implementer(IInterfaceHandler)
class ClientService(Plugin):
    """
    Plugin to register clients and expose their functionality
    to the users.

    Keys for configuration section **goto**

    +------------------+------------+-------------------------------------------------------------+
    + Key              | Format     +  Description                                                |
    +==================+============+=============================================================+
    + machine-rdn      | String     + RDN to initially place new machines in.                     |
    +------------------+------------+-------------------------------------------------------------+
    + timeout          | Integer    + Client ping interval.                                       |
    +------------------+------------+-------------------------------------------------------------+

    """
    
    _priority_ = 90
    _target_ = 'goto'
    __client = {}
    __proxy = {}
    __user_session = {}
    __listeners = {}

    def __init__(self):
        """
        Construct a new ClientService instance based on the configuration
        stored in the environment.
        """
        env = Environment.getInstance()
        self.log = logging.getLogger(__name__)
        self.log.info("initializing client service")
        self.env = env
        self.__cr = None
        self.mqtt = None

    def __get_handler(self):
        if self.mqtt is None:
            self.mqtt = MQTTHandler()
        return self.mqtt

    def serve(self):
        # Add event processor
        mqtt = self.__get_handler()
        mqtt.get_client().add_subscription('%s/client/+' % self.env.domain)
        self.log.debug("subscribing to %s event queue" % '%s/client/+' % self.env.domain)
        mqtt.set_subscription_callback(self.__eventProcessor)

        # Get registry - we need it later on
        self.__cr = PluginRegistry.getInstance("CommandRegistry")

        # Start maintenance with a delay of 5 seconds
        timer = Timer(5.0, self.__refresh)
        timer.start()
        self.env.threads.append(timer)

        # Register scheduler task to remove outdated clients
        sched = PluginRegistry.getInstance('SchedulerService').getScheduler()
        sched.add_interval_job(self.__gc, minutes=1, tag='_internal', jobstore="ram")

    def __refresh(self):
        # Initially check if we need to ask for client caps
        if not self.__client:
            e = EventMaker()
            self.mqtt.send_event(e.Event(e.ClientPoll()), "%s/client/broadcast" % self.env.domain)

    def stop(self):  # pragma: nocover
        pass

    @Command(__help__=N_("List available clients."))
    def getClients(self):
        """
        List available domain clients.

        ``Return:`` dict with name and timestamp information, indexed by UUID
        """
        res = {}
        for uuid, info in self.__client.items():
            if info['online']:
                res[uuid] = {'name': info['name'], 'last-seen': info['last-seen']}
        return res

    @gen.coroutine
    @Command(__help__=N_("Call method exposed by client."))
    def clientDispatch(self, client, method, *arg, **larg):
        """
        Dispatch a method on the client.

        ========= ================================
        Parameter Description
        ========= ================================
        client    Device UUID of the client
        method    Method name to call
        *         Method arguments
        ========= ================================

        ``Return:`` varies
        """

        # Bail out if the client is not available
        if not client in self.__client:
            raise JSONRPCException("client '%s' not available" % client)
        if not self.__client[client]['online']:
            raise JSONRPCException("client '%s' is offline" % client)
        if not method in self.__client[client]['caps']:
            raise JSONRPCException("client '%s' has no method '%s' exported" % (client, method))

        # Generate tag queue name
        queue = '%s/client/%s' % (self.env.domain, client)
        self.log.debug("got client dispatch: '%s(%s)', sending to %s" % (method, arg, queue))

        # client queue -> mqtt rpc proxy
        if not client in self.__proxy:
            self.__proxy[client] = MQTTServiceProxy(mqttHandler=self.mqtt, serviceAddress=queue)

        # Call her to the moon...
        methodCall = getattr(self.__proxy[client], method)

        # Do the call
        res = yield methodCall(*arg, **larg)
        raise gen.Return(res)

    @Command(__help__=N_("Get the client Interface/IP/Netmask/Broadcast/MAC list."))
    def getClientNetInfo(self, client):
        """
        Get brief information about the client network setup.

        Example:

        .. doctest::

            >>> getClientNetInfo("eb5e72d4-c53f-4612-81a3-602b14a8da69")
            {'eth0': {
                'Broadcast': '10.89.1.255',
                'MAC': '00:01:6c:9d:b9:fa',
                'IPAddress': '10.89.1.31',
                'Netmask': '255.255.255.0',
                'IPv6Address': 'fe80::201:6cff:fe9d:b9fa/64'}}

        ``Return:`` dict with network information
        """

        if not client in self.__client:
            return []

        res = self.__client[client]['network']
        return res

    @Command(__help__=N_("List available client methods for specified client."))
    def getClientMethods(self, client):
        """
        Get list of available client methods and their signature.

        ``Return:`` dict of client methods
        """
        if not client in self.__client:
            return []
        if not self.__client[client]['online']:
            return []

        return self.__client[client]['caps']

    @Command(__help__=N_("List user sessions per client"))
    def getUserSessions(self, client=None):
        """
        TODO
        """
        if client:
            return list(self.__user_session[client]) if client in self.__user_session else []

        return list(self.__user_session)

    @Command(__help__=N_("List clients a user is logged in"))
    def getUserClients(self, user):
        """
        TODO
        """
        return [client for client, users in self.__user_session.items() if user in users]

    @Command(__help__=N_("Send synchronous notification message to user"))
    def notifyUser(self, users, title, message, timeout=10, level='normal', icon="dialog-information"):
        """
        Send a notification request to the user client.
        """

        if icon is None:
            icon = "_no_icon_"

        if users:
            # Notify a single / group of users
            if type(users) != list:
                users = [users]

            for user in users:
                clients = self.getUserClients(user)
                if clients:
                    for client in clients:
                        try:
                            self.clientDispatch(client, "notify", user, title, message,
                                    timeout, icon)
                        #pylint: disable=W0141
                        except Exception as e:
                            import traceback
                            traceback.print_exc()
                            self.log.error("sending message failed: %s" % str(e))
                else:
                    self.log.error("sending message failed: no client found for user '%s'" % user)

                # Notify websession user if available
                if JsonRpcHandler.user_sessions_available(user):
                    mqtt = self.__get_handler()
                    mqtt.send_event(self.notification2event(user, title, message, timeout, icon), topic="%s/client/%s" % (self.env.domain, user))

        else:
            # Notify all users
            for client in self.__client.keys():
                try:
                    self.clientDispatch(client, "notify_all", title, message,
                            timeout, icon)
                #pylint: disable=W0141
                except Exception:
                    pass

            # Notify all websession users if any
            if JsonRpcHandler.user_sessions_available(None):
                mqtt = self.__get_handler()
                mqtt.send_event(self.notification2event("*", title, message, timeout, icon))

    def notification2event(self, user, title, message, timeout, icon):
        e = EventMaker()
        data = [e.Target(user)]
        if title:
            data.append(e.Title(title))
        data.append(e.Body(message))
        if timeout:
            data.append(e.Timeout(str(timeout * 1000)))
        if icon != "_no_icon_":
            data.append(e.Icon(icon))

        return e.Event(e.Notification(*data))

    @Command(__help__=N_("Set system status"))
    def systemGetStatus(self, device_uuid):
        """
        TODO
        """
        #TODO: use object backends instead of LDAP
        lh = LDAPHandler.get_instance()
        fltr = "deviceUUID=%s" % device_uuid

        with lh.get_handle() as conn:
            res = conn.search_s(lh.get_base(), ldap.SCOPE_SUBTREE,
                "(&(objectClass=device)(%s))" % fltr, ['deviceStatus'])

            if len(res) != 1:
                raise ValueError(C.make_error("CLIENT_NOT_FOUND", device_uuid))

            if 'deviceStatus' in res[0][1]:
                return res[0][1]["deviceStatus"][0].decode().strip('[""]')

        return ""

    @Command(__help__=N_("Set system status"))
    def systemSetStatus(self, device_uuid, status):
        """
        TODO
        """

        #TODO: use object backends instead of LDAP

        # Check params
        valid = [STATUS_SYSTEM_ON, STATUS_LOCKED, STATUS_UPDATABLE,
            STATUS_UPDATING, STATUS_INVENTORY, STATUS_CONFIGURING,
            STATUS_INSTALLING, STATUS_VM_INITIALIZING, STATUS_WARNING,
            STATUS_ERROR, STATUS_OCCUPIED, STATUS_BOOTING,
            STATUS_NEEDS_INSTALL, STATUS_NEEDS_CONFIG,
            STATUS_NEEDS_INITIAL_CONFIG, STATUS_NEEDS_REMOVE_CONFIG]

        # Write to LDAP
        lh = LDAPHandler.get_instance()
        fltr = "deviceUUID=%s" % device_uuid
        with lh.get_handle() as conn:
            res = conn.search_s(lh.get_base(), ldap.SCOPE_SUBTREE,
                "(&(objectClass=device)(%s))" % fltr, ['deviceStatus'])

            if len(res) != 1:
                raise ValueError(C.make_error("CLIENT_NOT_FOUND", device_uuid))
            devstat = res[0][1]['deviceStatus'][0] if 'deviceStatus' in res[0][1] else b""
            is_new = not bool(devstat)
            devstat = list(devstat.decode().strip('[""]'))

            r = re.compile(r"([+-].)")
            for stat in r.findall(status):
                if not stat[1] in valid:
                    raise ValueError(C.make_error("CLIENT_STATUS_INVALID", device_uuid, status=stat[1]))
                if stat.startswith("+"):
                    if not stat[1] in devstat:
                        devstat.append(stat[1])
                else:
                    if stat[1] in devstat:
                        devstat.remove(stat[1])
            devstat = bytes('["%s"]' % "".join(str(x) for x in devstat), 'utf-8')
            if is_new:
                conn.modify(res[0][0], [(ldap.MOD_ADD, "deviceStatus", [devstat])])
            else:
                conn.modify(res[0][0], [(ldap.MOD_REPLACE, "deviceStatus", [devstat])])

    @Command(needsUser=True, __help__=N_("Join a client to the GOsa infrastructure."))
    def joinClient(self, user, device_uuid, mac, info=None):
        """
        TODO
        """

        #TODO: use objects

        uuid_check = re.compile(r"^[0-9a-f]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$", re.IGNORECASE)
        if not uuid_check.match(device_uuid):
            raise ValueError(C.make_error("CLIENT_UUID_INVALID", device_uuid))

        lh = LDAPHandler.get_instance()

        # Handle info, if present
        more_info = []

        if info:
            # Check string entries
            for entry in filter(lambda x: x in info,
                ["serialNumber", "ou", "o", "l", "description"]):

                if not re.match(r"^[\w\s]+$", info[entry]):
                    raise ValueError(C.make_error("CLIENT_DATA_INVALID", device_uuid, entry=entry, data=info[entry]))

                more_info.append((entry, info[entry]))

            # Check desired device type if set
            if "deviceType" in info:
                if re.match(r"^(terminal|workstation|server|sipphone|switch|router|printer|scanner)$",
                    info["deviceType"]):

                    more_info.append(("deviceType", info["deviceType"]))
                else:
                    raise ValueError(C.make_error("CLIENT_TYPE_INVALID", device_uuid, type=info["deviceType"]))

            # Check owner for presence
            if "owner" in info:
                with lh.get_handle() as conn:

                    # Take a look at the directory to see if there's
                    # such an owner DN
                    try:
                        conn.search_s(info["owner"], ldap.SCOPE_BASE, attrlist=['dn'])
                        more_info.append(("owner", info["owner"]))
                    except Exception:
                        raise ValueError(C.make_error("CLIENT_OWNER_NOT_FOUND", device_uuid, owner=info["owner"]))

        # Generate random client key
        random.seed()
        key = ''.join(random.Random().sample(string.ascii_letters + string.digits, 32))
        salt = os.urandom(4)
        h = hashlib.sha1(key.encode('ascii'))
        h.update(salt)

        # Do LDAP operations to add the system
        with lh.get_handle() as conn:

            # Take a look at the directory to see if there's
            # already a joined client with this uuid
            res = conn.search_s(lh.get_base(), ldap.SCOPE_SUBTREE,
                "(&(objectClass=registeredDevice)(macAddress=%s))" % mac, ["macAddress"])

            # Already registered?
            if len(res) > 0:
                raise GOtoException(C.make_error("DEVICE_EXISTS", mac))

            # While the client is going to be joined, generate a random uuid and
            # an encoded join key
            cn = str(uuid4())
            device_key = self.__encrypt_key(device_uuid.replace("-", ""), cn + key)

            # Resolve manger
            res = conn.search_s(lh.get_base(), ldap.SCOPE_SUBTREE,
                    "(uid=%s)" % user, [])
            if len(res) != 1:
                raise GOtoException(C.make_error("USER_NOT_UNIQUE" if res else "UNKNOWN_USER", target=user))
            manager = res[0][0]

            # Create new machine entry
            record = [
                ('objectclass', [b'device', b'ieee802Device', b'simpleSecurityObject', b'registeredDevice']),
                ('deviceUUID', bytes(cn, 'utf-8')),
                ('deviceKey', [device_key]),
                ('cn', [bytes(cn, 'utf-8')]),
                ('manager', [bytes(manager, 'utf-8')]),
                ('macAddress', [mac.encode("ascii", "ignore")]),
                ('userPassword', [b"{SSHA}" + encode(h.digest() + salt)])
            ]
            record += more_info

            # Evaluate base
            #TODO: take hint from "info" parameter, to allow "joiner" to provide
            #      a target base
            base = lh.get_base()

            # Add record
            dn = ",".join(["cn=" + cn, self.env.config.get("goto.machine-rdn",
                default="ou=systems"), base])
            conn.add_s(dn, record)

            self.log.info("UUID '%s' joined as %s" % (device_uuid, dn))

            return [key, cn]

        return None

    def __encrypt_key(self, key, data):
        """
        Encrypt a data using key
        """

        # Calculate padding length
        key_pad = AES.block_size - len(key) % AES.block_size
        data_pad = AES.block_size - len(data) % AES.block_size

        # Pad data PKCS12 style
        if key_pad != AES.block_size:
            key += chr(key_pad) * key_pad
        if data_pad != AES.block_size:
            data += chr(data_pad) * data_pad

        return AES.new(key, AES.MODE_ECB).encrypt(data)

    def __eventProcessor(self, topic, message):
        if message[0:1] == "{":
            # RPC response
            self.log.debug("RPC response received in channel %s: '%s'" % (topic, message))
        else:
            try:
                data = etree.fromstring(message, PluginRegistry.getEventParser())
                eventType = stripNs(data.xpath('/g:Event/*', namespaces={'g': "http://www.gonicus.de/Events"})[0].tag)
                self.log.debug("Incoming MQTT event[%s]: '%s'" % (eventType, data))
                if hasattr(self, "_handle"+eventType):
                    func = getattr(self, "_handle" + eventType)
                    func(data)
                else:
                    self.log.debug("unhandled event %s" % eventType)
            except etree.XMLSyntaxError as e:
                self.log.error("XML parse error %s on message %s" % (e, message))

    def _handleUserSession(self, data):
        data = data.UserSession
        if hasattr(data.User, 'Name'):
            self.__user_session[str(data.Id)] = list(map(str, data.User.Name))
            self.systemSetStatus(str(data.Id), "+B")
        else:
            self.__user_session[str(data.Id)] = []
            self.systemSetStatus(str(data.Id), "-B")

        self.log.debug("updating client '%s' user session: %s" % (data.Id,
                ','.join(self.__user_session[str(data.Id)])))

    def _handleClientPing(self, data):
        data = data.ClientPing
        client = data.Id.text
        self.__set_client_online(data.Id.text)
        if client in self.__client:
            self.__client[client]['last-seen'] = datetime.datetime.utcnow()

    def _handleClientSignature(self, data):
        data = data.ClientSignature
        client = data.Id.text
        self.log.info("client '%s' has an signature update for us" % client)

        # Remove remaining proxy values for this client
        if client in self.__proxy:
            self.__proxy[client].close()
            del self.__proxy[client]

        # Assemble caps
        caps = {}
        for method in data.ClientCapabilities.ClientMethod:
            caps[method.Name.text] = {
                'path': method.Path.text,
                'sig': method.Signature.text,
                'doc': method.Documentation.text}

        # This may happen if we get a stuck event
        if not data.Id.text in self.__client:
            return

        # Decide if we need to notify someone about new methods
        current = copy(self.__client[data.Id.text]['caps'])
        self.__client[data.Id.text]['caps'] = caps
        for method in [m for m in current.keys() if not m in caps]:
            self.notify_listeners(data.Id.text, method, False)
        for method in [m for m in caps if not m in current.keys()]:
            self.notify_listeners(data.Id.text, method, True)

    def notify_listeners(self, cid, method, status):
        if method in self.__listeners:
            for cb in self.__listeners[method]:
                cb(cid, method, status)

    def register_listener(self, method, callback):
        if not method in self.__listeners:
            self.__listeners[method] = []

        if not callback in self.__listeners[method]:
            self.__listeners[method].append(callback)

    def unregister_listener(self, method, callback):
        if not method in self.__listeners:
            return

        if not callback in self.__listeners[method]:
            return

        self.__listeners[method].pop(self.__listeners[method].index(callback))

    def _handleClientAnnounce(self, data):
        data = data.ClientAnnounce
        client = data.Id.text
        self.log.info("client '%s' is joining us" % client)
        self.systemSetStatus(client, "+O")

        # Assemble network information
        network = {}
        for interface in data.NetworkInformation.NetworkDevice:
            network[interface.Name.text] = {
                'IPAddress': interface.IPAddress.text,
                'IPv6Address': interface.IPv6Address.text,
                'MAC': interface.MAC.text,
                'Netmask': interface.Netmask.text,
                'Broadcast': interface.Broadcast.text}

        # Add recieve time to be able to sort out dead nodes
        t = datetime.datetime.utcnow()
        info = {
            'name': data.Name.text,
            'last-seen': t,
            'online': True,
            'caps': {},
            'network': network
        }

        self.__client[data.Id.text] = info

        # Handle pending "P"repare actions for that client
        if "P" in self.systemGetStatus(client):
            try:
                rm = PluginRegistry.getInstance("RepositoryManager")
                rm.prepareClient(client)
            except ValueError:
                pass

    def _handleClientLeave(self, data):
        data = data.ClientLeave
        client = data.Id.text
        self.log.info("client '%s' is leaving" % client)
        self.__set_client_offline(client, True)

    def __set_client_online(self, client):
        self.systemSetStatus(client, "+O")
        if client in self.__client:
            self.__client[client]['online'] = True

    def __set_client_offline(self, client, purge=False):
        self.systemSetStatus(client, "-O")

        if client in self.__client:
            if purge:
                del self.__client[client]

                if client in self.__proxy:
                    self.__proxy[client].close()
                    del self.__proxy[client]

                if client in self.__user_session:
                    del self.__user_session[client]

            else:
                self.__client[client]['online'] = False

    def __gc(self):
        interval = int(self.env.config.get("goto.timeout", default="600"))

        for client, info in self.__client.items():
            if not info['online']:
                continue

            if info['last-seen'] < datetime.datetime.utcnow() - datetime.timedelta(seconds=2 * interval):
                self.log.info("client '%s' looks dead - setting to 'offline'" % client)
                self.__set_client_offline(client)
