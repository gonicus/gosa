# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

import re
import datetime
import logging
from uuid import uuid4
from copy import copy

import zope

from gosa.backend.lock import GlobalLock
from gosa.backend.objects import ObjectProxy
from gosa.common.components.jsonrpc_utils import Binary
from lxml import etree

from gosa.backend.components.jsonrpc_service import JsonRpcHandler
from gosa.common.components.mqtt_handler import MQTTHandler
from tornado import gen
from zope.interface import implementer
from gosa.common.components.jsonrpc_proxy import JSONRPCException
from gosa.common.gjson import loads, dumps
from gosa.common.handler import IInterfaceHandler
from gosa.common.event import EventMaker
from gosa.common import Environment
from gosa.common.utils import stripNs, N_, encrypt_key, generate_random_key, is_uuid
from gosa.common.error import GosaErrorHandler as C
from gosa.common.components.registry import PluginRegistry
from gosa.common.components.mqtt_proxy import MQTTServiceProxy
from gosa.common.components import Plugin
from gosa.common.components.command import Command
from gosa.plugins.goto.in_out_filters import mapping
from base64 import b64encode as encode

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
    entry_attributes = ['cn', 'description', 'gosaApplicationPriority', 'gosaApplicationIcon', 'gosaApplicationName', 'gotoLogonScript', 'gosaApplicationFlags', 'gosaApplicationExecute']
    entry_map = {"gosaApplicationPriority": "prio", "description": "description"}
    printer_attributes = ["gotoPrinterPPD", "labeledURI", "cn", "l", "description"]
    __client_call_queue = {}

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

        # Start maintenance when index scan is finished
        zope.event.subscribers.append(self.__handle_events)

        # Register scheduler task to remove outdated clients
        sched = PluginRegistry.getInstance('SchedulerService').getScheduler()
        sched.add_interval_job(self.__gc, minutes=1, tag='_internal', jobstore="ram")

        # self.register_listener("configureHostPrinters", self._on_client_caps)

    def __handle_events(self, event):
        """
        React on object modifications to keep active ACLs up to date.
        """
        if event.__class__.__name__ == "IndexScanFinished":
            self.__refresh()

    def __refresh(self):
        # Initially check if we need to ask for client caps
        if not self.__client:
            e = EventMaker()
            self.mqtt.send_event(e.Event(e.ClientPoll()), "%s/client/broadcast" % self.env.domain)

    def stop(self):  # pragma: nocover
        pass

    def get_client_uuid(self, name_or_uuid):
        if is_uuid(name_or_uuid):
            return name_or_uuid
        else:
            # hostname used
            for uuid in self.__client:
                if self.__client[uuid]["name"] == name_or_uuid:
                    return uuid
        return name_or_uuid

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
        client = self.get_client_uuid(client)

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

    @Command(__help__=N_("Check if the client supports a method call"))
    def hasCapability(self, client_id, method):
        return client_id in self.__client and method in self.__client[client_id]

    def queuedClientDispatch(self, client, method, *arg, **larg):
        client = self.get_client_uuid(client)

        # Bail out if the client is not available
        if client not in self.__client:
            raise JSONRPCException("client '%s' not available" % client)
        if not self.__client[client]['online']:
            raise JSONRPCException("client '%s' is offline" % client)
        if method not in self.__client[client]['caps']:
            # wait til method gets available
            if client not in self.__client_call_queue:
                self.__client_call_queue[client] = {}
            if method not in self.__client_call_queue[client]:
                self.__client_call_queue[client][method] = []
            if method not in self.__listeners:
                self.register_listener(method, self._on_client_caps)
            self.__client_call_queue[client][method].append((arg, larg))
        else:
            self.clientDispatch(client, method, *arg, **larg)

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
        client = self.get_client_uuid(client)
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
        client = self.get_client_uuid(client)

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
            client = self.get_client_uuid(client)
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

    def __open_device(self, device_uuid):
        device_uuid = self.get_client_uuid(device_uuid)
        index = PluginRegistry.getInstance("ObjectIndex")

        res = index.search({'_type': 'Device', 'deviceUUID': device_uuid},
                           {'_uuid': 1})
        if len(res) != 1:
            raise ValueError(C.make_error("CLIENT_NOT_FOUND", device_uuid, status_code=404))

        return ObjectProxy(res[0]['_uuid'])

    @Command(__help__=N_("Set system status"))
    def systemGetStatus(self, device_uuid):
        """
        TODO
        """
        device = self.__open_device(device_uuid)
        return device.deviceStatus

    @Command(__help__=N_("Set system status"))
    def systemSetStatus(self, device_uuid, status):
        """
        TODO
        """
        if GlobalLock.exists("scan_index"):
            # do not update state during index, clients will be polled after index is done
            return

        device = self.__open_device(device_uuid)
        r = re.compile(r"([+-].)")
        for stat in r.findall(status):
            if stat[1] not in mapping:
                raise ValueError(C.make_error("CLIENT_STATUS_INVALID", device_uuid, status=stat[1]))
            setattr(device, mapping[stat[1]], stat.startswith("+"))
        device.commit()

    @Command(needsUser=True, __help__=N_("Join a client to the GOsa infrastructure."))
    def joinClient(self, user, device_uuid, mac, info=None):
        """
        TODO
        """

        index = PluginRegistry.getInstance("ObjectIndex")

        uuid_check = re.compile(r"^[0-9a-f]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$", re.IGNORECASE)
        if not uuid_check.match(device_uuid):
            raise ValueError(C.make_error("CLIENT_UUID_INVALID", device_uuid))

        # Handle info, if present
        more_info = []

        if info:
            # Check string entries
            for entry in filter(lambda x: x in info, ["serialNumber", "ou", "o", "l", "description"]):

                if not re.match(r"^[\w\s]+$", info[entry]):
                    raise ValueError(C.make_error("CLIENT_DATA_INVALID", device_uuid, entry=entry, data=info[entry]))

                more_info.append((entry, info[entry]))

            # Check desired device type if set
            if "deviceType" in info:
                if re.match(r"^(terminal|workstation|server|sipphone|switch|router|printer|scanner)$", info["deviceType"]):

                    more_info.append(("deviceType", info["deviceType"]))
                else:
                    raise ValueError(C.make_error("CLIENT_TYPE_INVALID", device_uuid, type=info["deviceType"]))

            # Check owner for presence
            if "owner" in info:
                # Take a look at the directory to see if there's  such an owner DN
                res = index.search({'_dn': info["owner"]}, {'_dn': 1})
                if len(res) == 0:
                    raise ValueError(C.make_error("CLIENT_OWNER_NOT_FOUND", device_uuid, owner=info["owner"]))
                more_info.append(("owner", info["owner"]))

        # Generate random client key
        h, key, salt = generate_random_key()

        # Take a look at the directory to see if there's already a joined client with this uuid
        res = index.search({'_type': 'Device', 'macAddress': mac, 'extension': 'RegisteredDevice'},
                           {'dn': 1})

        if len(res) > 0:
            record = ObjectProxy(res[0]['dn'])
            for ext in ["simpleSecurityObject", "ieee802Device"]:
                if not record.is_extended_by(ext):
                    record.extend(ext)

            if record.is_extended_by("ForemanHost") and record.otp is not None:
                record.otp = None

            record.userPassword = ["{SSHA}" + encode(h.digest() + salt).decode()]
            for k, value in more_info:
                setattr(record, k, value)
            cn = record.deviceUUID
            record.status_Online = False
            record.status_Offline = True
            record.status_InstallationInProgress = False

            record.commit()
            self.log.info("UUID '%s' joined as %s" % (device_uuid, record.dn))
        else:

            # While the client is going to be joined, generate a random uuid and an encoded join key
            cn = str(uuid4())
            device_key = encrypt_key(device_uuid.replace("-", ""), cn + key)

            # Resolve manager
            res = index.search({'_type': 'User', 'uid': user},
                               {'dn': 1})

            if len(res) != 1:
                raise GOtoException(C.make_error("USER_NOT_UNIQUE" if res else "UNKNOWN_USER", target=user))
            manager = res[0]['dn']

            # Create new machine entry
            dn = ",".join([self.env.config.get("goto.machine-rdn", default="ou=systems"), self.env.base])
            record = ObjectProxy(dn, "Device")
            record.extend("RegisteredDevice")
            record.extend("ieee802Device")
            record.extend("simpleSecurityObject")
            record.deviceUUID = cn
            record.deviceKey = Binary(device_key)
            record.cn = "mac%s" % mac.replace(":", "")
            record.manager = manager
            record.status_Offline = True
            record.macAddress = mac.encode("ascii", "ignore")
            record.userPassword = ["{SSHA}" + encode(h.digest() + salt).decode()]
            for k, value in more_info:
                setattr(record, k, value)

            record.commit()
            self.log.info("UUID '%s' joined as %s" % (device_uuid, record.dn))

        # make sure the client has the access rights he needs
        self.applyClientRights(cn)

        return [key, cn]

    def __eventProcessor(self, topic, message):
        if message[0:1] == "{":
            # RPC response
            self.log.debug("RPC response received in channel %s: '%s'" % (topic, message))
        else:
            try:
                data = etree.fromstring(message, PluginRegistry.getEventParser())
                eventType = stripNs(data.xpath('/g:Event/*', namespaces={'g': "http://www.gonicus.de/Events"})[0].tag)
                if hasattr(self, "_handle"+eventType):
                    func = getattr(self, "_handle" + eventType)
                    func(data)
                else:
                    self.log.debug("unhandled event %s" % eventType)
            except etree.XMLSyntaxError as e:
                self.log.error("XML parse error %s on message %s" % (e, message))

    def _handleUserSession(self, data):
        data = data.UserSession
        id = str(data.Id)
        if hasattr(data.User, 'Name'):
            users = list(map(str, data.User.Name))
            if id in self.__user_session:
                new_users = list(set.difference(set(users), set(self.__user_session[id])))
            else:
                # all users are new
                new_users = users

            self.__user_session[id] = users

            for user in users:
                self.preUserSession(id, user, skip_config=True)

            if len(new_users):
                self.log.debug("configuring new users: %s" % new_users)
                self.configureUsers(id, new_users)

        else:
            self.__user_session[id] = []
            self.systemSetStatus(id, "-B")

        self.log.debug("updating client '%s' user session: %s" % (id, ','.join(self.__user_session[id])))

    @Command(__help__=N_("Prepare a user session after a user has logged in"))
    def preUserSession(self, client_id, user_name, skip_config=False):
        # save login time and system<->user references
        client = self.__open_device(client_id)
        client.gotoLastUser = user_name
        client.commit()

        index = PluginRegistry.getInstance("ObjectIndex")
        res = index.search({"_type": "User", "uid": user_name}, {"dn": 1})
        for u in res:
            user = ObjectProxy(u["dn"])
            if not user.is_extended_by("GosaAccount"):
                user.extend("GosaAccount")
            user.gotoLastSystemLogin = datetime.datetime.now()
            user.gotoLastSystem = client.dn
            user.commit()

        self.systemSetStatus(client_id, "+B")

        if skip_config is False:
            user_config = self.__collect_user_configuration(client_id, [user_name])
            if user_config is not None and user_name in user_config:
                return user_config[user_name]

        return None

    @Command(__help__=N_("Cleanup a user session after a user has logged out"))
    def postUserSession(self, client_id, user):
        """
        :param client_id: clients deviceUUID
        :param user: uid of the user that has logged out
        """
        if client_id not in self.__user_session:
            self.__user_session[client_id] = []
        if user in self.__user_session[client_id]:
            self.__user_session[client_id].remove(user)
        if len(self.__user_session[client_id]) == 0:
            self.systemSetStatus(client_id, "-B")

    @Command(__help__="Send user configurations of all logged in user to a client")
    def configureUsers(self, client_id, users):
        users_config = self.__collect_user_configuration(client_id, users)
        for uid, config in users_config.items():
            if "menu" in config:
                # send to client
                self.log.debug("sending generated menu for user %s" % uid)
                self.queuedClientDispatch(client_id, "dbus_configureUserMenu", uid, dumps(config["menu"]))

            if "printer-setup" in config:
                self.configureHostPrinters(client_id, config["printer-setup"])

            if "resolution" in config and config["resolution"] is not None and len(config["resolution"]):
                self.log.debug("sending screen resolution: %sx%s for user %s to client %s" % (config["resolution"][0], config["resolution"][1], uid, client_id))
                self.queuedClientDispatch(client_id, "dbus_configureUserScreen", uid, config["resolution"][0], config["resolution"][1])

    def __collect_user_configuration(self, client_id, users):
        """
        :param client_id: deviceUUID or hostname
        :param users: list of currently logged in users on the client
        """
        client = self.__open_device(client_id)
        group = None
        index = PluginRegistry.getInstance("ObjectIndex")
        res = index.search({"_type": "GroupOfNames", "member": client.dn}, {"dn": 1})
        if len(res) > 0:
            group = ObjectProxy(res[0]["dn"])
        config = {}

        resolution = None
        if group is not None and group.is_extended_by("GotoEnvironment") and group.gotoXResolution is not None:
            resolution = group.gotoXResolution

        if client.is_extended_by("GotoEnvironment") and client.gotoXResolution is not None:
            resolution = client.gotoXResolution

        release = None
        if client.is_extended_by("GotoMenu"):
            release = client.getReleaseName()
        elif group is not None and group.is_extended_by("ForemanHostGroup"):
            release = group.getReleaseName()
            parent_group = group
            while release is None and parent_group is not None and parent_group.parent_id is not None:
                res = index.search({"_type": "GroupOfNames", "extension": "ForemanHostGroup", "foremanGroupId": parent_group.parent_id}, {"dn": 1})
                if len(res) == 0:
                    break
                else:
                    parent_group = ObjectProxy(res[0]["dn"])
                    release = parent_group.getReleaseName()

        if release is None:
            self.log.error("no release found for client/user combination (%s/%s)" % (client_id, users))

        client_menu = None

        if hasattr(client, "gotoMenu") and client.gotoMenu is not None:
            client_menu = loads(client.gotoMenu)

        # collect users DNs
        query_result = index.search({"_type": "User", "uid": {"in_": users}}, {"dn": 1})
        for entry in query_result:
            user = ObjectProxy(entry["dn"])
            config[user.uid] = {}

            if release is not None:
                menus = []
                if client_menu is not None:
                    menus.append(client_menu)

                # get all groups the user is member of which have a menu for the given release
                query = {'_type': 'GroupOfNames', "member": user.dn, "extension": "GotoMenu", "gotoLsbName": release}

                for res in index.search(query, {"gotoMenu": 1}):
                    # collect user menus
                    for m in res["gotoMenu"]:
                        menus.append(loads(m))

                if len(menus):
                    user_menu = None
                    for menu_entry in menus:
                        if user_menu is None:
                            user_menu = self.get_submenu(menu_entry)
                        else:
                            self.merge_submenu(user_menu, self.get_submenu(menu_entry))
                    config[user.uid]["menu"] = user_menu

            # collect printer settings for user, starting with the clients printers
            settings = self.__collect_printer_settings(group)
            printer_names = [x["cn"] for x in settings["printers"]]
            for res in index.search({'_type': 'GroupOfNames', "member": user.dn, "extension": "GotoEnvironment"},
                                    {"dn": 1}):
                user_group = ObjectProxy(res["dn"])
                if user_group.dn == group.dn:
                    continue
                s = self.__collect_printer_settings(user_group)

                if user_group.gotoXResolution is not None:
                    resolution = user_group.gotoXResolution

                for p in s["printers"]:
                    if p["cn"] not in printer_names:
                        settings["printers"].append(p)
                        printer_names.append(p["cn"])

                if s["defaultPrinter"] is not None:
                    settings["defaultPrinter"] = s["defaultPrinter"]

            # override group environment settings if the client has one
            s = self.__collect_printer_settings(client)
            if len(s["printers"]) > 0:
                settings["printers"] = s["printers"]
                settings["defaultPrinter"] = s["defaultPrinter"]

            if user.is_extended_by("GosaAccount") and user.gosaDefaultPrinter is not None:
                # check if the users default printer is send to the client
                found = False
                for printer_settings in settings["printers"]:
                    if printer_settings["cn"] == user.gosaDefaultPrinter:
                        found = True
                        break

                def process(res):
                    if len(res) == 0:
                        self.log.warning("users defaultPrinter not found: %s" % user.gosaDefaultPrinter)
                        return None
                    elif len(res) == 1:
                        # add this one to the result set
                        printer = ObjectProxy(res[0]["dn"])
                        p_conf = {}
                        for attr in self.printer_attributes:
                            p_conf[attr] = getattr(printer, attr)
                        return p_conf
                    return False

                if found is False:
                    # find the printer and add it to the settings
                    res = index.search({"_type": "GotoPrinter", "cn": user.gosaDefaultPrinter}, {"dn": 1})
                    printer_config = process(res)
                    if printer_config is False:
                        # more than 1 printers found by this CN, try to look in the users subtree
                        res = index.search({
                            "_type": "GotoPrinter",
                            "cn": user.gosaDefaultPrinter,
                            "_adjusted_parent_dn": user.get_adjusted_parent_dn()
                        }, {"dn": 1})
                        printer_config = process(res)

                    if isinstance(printer_config, dict):
                        settings["printers"].append(printer_config)
                        settings["defaultPrinter"] = user.gosaDefaultPrinter
                    else:
                        self.log.warning("users defaultPrinter not found: %s" % user.gosaDefaultPrinter)
                else:
                    settings["defaultPrinter"] = user.gosaDefaultPrinter

            config[user.uid]["printer-setup"] = settings
            config[user.uid]["resolution"] = None

            if resolution is not None:
                config[user.uid]["resolution"] = [int(x) for x in resolution.split("x")]

            # TODO: collect and send login scripts to client
        return config

    def merge_submenu(self, menu1, menu2):
        for cn, app in menu2.get('apps', {}).items():
            if cn in menu1['apps']:
                prio1 = int(menu1[cn].get('gosaApplicationPriority', '0'))
                prio2 = int(menu2[cn].get('gosaApplicationPriority', '0'))
                if prio2 >= prio1:
                    menu1['apps'][cn] = app
            else:
                menu1['apps'][cn] = app

        for menu_entry in menu2.get('menus', {}):
            if menu_entry in menu1['menus']:
                for cn, app in menu2['menus'][menu_entry].get('apps', {}).items():
                    if cn in menu1['menus'][menu_entry]['apps']:
                        prio1 = int(menu1['menus'][menu_entry]['apps'][cn].get('gosaApplicationPriority', '0'))
                        prio2 = int(menu2['menus'][menu_entry]['apps'][cn].get('gosaApplicationPriority', '0'))
                        if prio2 >= prio1:
                            menu1['menus'][menu_entry]['apps'][cn] = app
                    else:
                        menu1['menus'][menu_entry]['apps'][cn] = app
            else:
                menu1['menus'][menu_entry] = menu2['menus'][menu_entry]

            if 'menus' in menu2['menus'][menu_entry]:
                if menu_entry in menu1['menus'] and 'menus' in menu1['menus'][menu_entry]:
                    self.merge_submenu(menu1['menus'][menu_entry], menu2['menus'][menu_entry])
                else:
                    menu1['menus'][menu_entry]['menus'] = menu2['menus'][menu_entry]['menus']

    def get_submenu(self, entries):
        result = None
        for entry in entries:
            if result is None:
                result = {'apps': {}}

            if 'children' in entry:
                if not 'menus' in result:
                    result['menus'] = {}
                result['menus'][entry.get('name', N_('Unbekannt'))] = self.get_submenu(entry['children'])
            else:
                application = self.get_application(entry)
                result['apps'][application.get('cn', 'name')] = application

        return result

    def get_application(self, application):
        result = None
        if 'name' in application and 'dn' in application:
            result = {'name': application.get('name')}
            if 'gosaApplicationParameter' in application:
                result['gosaApplicationParameter'] = application.get('gosaApplicationParameter')

            application = ObjectProxy(application.get('dn'))
            if application is not None:
                for attribute in self.entry_attributes:
                    if hasattr(application, attribute):
                        attribute_name = self.entry_map.get(attribute, attribute)
                        result[attribute_name] = getattr(application, attribute)

        return result

    @Command(__help__=N_("Send user specific configuration (e.g. printers) to a clients active user sessions"))
    def configureClient(self, client_id):
        """
        :param client_id: deviceUUID or hostname
        """
        if client_id in self.__user_session:
            self.configureUsers(client_id, self.__user_session[client_id])

    def configureHostPrinters(self, client_id, config):
        """ configure the printers for this client via dbus. """
        if "printers" not in config or len(config["printers"]) == 0:
            return
        # delete old printers first
        self.queuedClientDispatch(client_id, "dbus_deleteAllPrinters")

        for p_conf in config["printers"]:
            self.queuedClientDispatch(client_id, "dbus_addPrinter", p_conf)

        if "defaultPrinter" in config and config["defaultPrinter"] is not None:
            self.queuedClientDispatch(client_id, "dbus_defaultPrinter", config["defaultPrinter"])

    def __collect_printer_settings(self, object):
        settings = {"printers": [], "defaultPrinter": None}
        if object is not None and object.is_extended_by("GotoEnvironment") and len(object.gotoPrinters):
            # get default printer
            settings["defaultPrinter"] = object.gotoDefaultPrinter

            # collect printer PPDs
            for printer_dn in object.gotoPrinters:
                printer = ObjectProxy(printer_dn)
                p_conf = {}
                for attr in self.printer_attributes:
                    p_conf[attr] = getattr(printer, attr)
                settings["printers"].append(p_conf)
        return settings

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
            self.log.debug("client %s provides method %s" % (client, method.Name.text))
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
        self.systemSetStatus(client, "+O-o")

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

        self.__client[client] = info

        # Handle pending "P"repare actions for that client
        if "P" in self.systemGetStatus(client):
            try:
                rm = PluginRegistry.getInstance("RepositoryManager")
                rm.prepareClient(client)
            except ValueError:
                pass

    def _on_client_caps(self, cid, method, status):
        if status is False:
            return

        self.log.debug("client %s provides method %s" % (cid, method))
        if cid in self.__client_call_queue and method in self.__client_call_queue[cid]:
            for arg, larg in self.__client_call_queue[cid][method]:
                self.clientDispatch(cid, method, *arg, **larg)
            del self.__client_call_queue[cid][method]

            if len(self.__client_call_queue[cid].keys()) == 0:
                del self.__client_call_queue[cid]

            # check if we still have listeners for that method
            delete = True
            for client_id, queue in self.__client_call_queue.items():
                if method in queue:
                    delete = False
                    break

            if delete is True:
                self.unregister_listener(method, self._on_client_caps)

    def _handleClientLeave(self, data):
        data = data.ClientLeave
        client = data.Id.text
        self.log.info("client '%s' is leaving" % client)
        self.__set_client_offline(client, True)

    def __set_client_online(self, client):
        self.systemSetStatus(client, "+O-o")
        if client in self.__client:
            self.__client[client]['online'] = True

    def __set_client_offline(self, client, purge=False):
        try:
            self.systemSetStatus(client, "-O+o")
        except ValueError as e:
            id = C.get_error_id(str(e))
            error = C.getError(None, None, id, keep=True)
            if error.status_code == 404:
                pass
            else:
                raise e

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

    def applyClientRights(self, device_uuid):
        # check rights
        acl = PluginRegistry.getInstance("ACLResolver")
        if not acl.check(device_uuid, "%s.%s.%s" % (self.env.domain, "command", "preUserSession"), "x"):
            role_name = "$$ClientDevices"
            # create AclRole for joining if not exists
            index = PluginRegistry.getInstance("ObjectIndex")
            res = index.search({"_type": "AclRole", "name": role_name}, {"dn": 1})
            if len(res) == 0:
                # create
                role = ObjectProxy(self.env.base, "AclRole")
                role.name = role_name

                # create rule
                aclentry = {
                    "priority": 0,
                    "scope": "sub",
                    "actions": [
                        {
                            "topic": "%s\.command\.(joinClient|preUserSession|postUserSession)" % self.env.domain,
                            "acl": "x",
                            "options": {}
                        }
                    ]}
                role.AclRoles = [aclentry]
                role.commit()

            # check if device has role
            found = False
            base = ObjectProxy(self.env.base)
            if base.is_extended_by("Acl"):
                for entry in base.AclSets:
                    if entry["rolename"] == role_name and device_uuid in entry["members"]:
                        found = True
                        break
            else:
                base.extend("Acl")

            if found is False:
                acl_entry = {"priority": 0,
                             "members": [device_uuid],
                             "rolename": role_name}
                base.AclSets.append(acl_entry)
                base.commit()