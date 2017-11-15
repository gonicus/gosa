
# This file is part of the GOsa project.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.
import datetime
import logging
import uuid
import sys
from lxml import objectify, etree

import zope
import socket

from sqlalchemy import and_

from gosa.backend.objects import ObjectProxy, ObjectFactory
from gosa.backend.objects.index import ObjectInfoIndex, ExtensionIndex, KeyValueIndex
from gosa.backend.routes.sse.main import SseHandler
from gosa.common import Environment
from gosa.common.components import Plugin, Command
from gosa.common.event import EventMaker
from gosa.common.handler import IInterfaceHandler
from zope.interface import implementer
from gosa.common.error import GosaErrorHandler as C
from gosa.common.utils import N_, generate_random_key, cache_return
from gosa.common.components import PluginRegistry
from gosa.common.gjson import loads, dumps
from base64 import b64encode as encode
from gosa.backend.objects.backend.back_foreman import Foreman as ForemanBackend, ForemanClient, ForemanBackendException

C.register_codes(dict(
    FOREMAN_UNKNOWN_TYPE=N_("Unknown object type '%(type)s'"),
    NO_MAC=N_("No MAC given to identify host '%(hostname)s'"),
    DEVICE_NOT_FOUND=N_("Cannot find device '%(hostname)s'"),
    NO_FOREMAN_OBJECT=N_("This object is not managed by foreman"),
    MULTIPLE_DEVICES_FOUND=N_("(%devices)s found for hostname '%(hostname)s'"),
    HOSTGROUP_NOT_FOUND=N_("Cannot find hostgroup with id '%(group_id)s'"),
    MULTIPLE_HOSTGROUPS_FOUND=N_("(%groups)s found for group id '%(group_id)s'"),
))


@implementer(IInterfaceHandler)
class Foreman(Plugin):
    """
    The Foreman plugin takes care about syncing the required data between the foreman and GOsa.
    Currently the following foreman objects are synced:

    * ``hosts``, ``discovered_hosts`` as ``ForemanHost`` objects
    * ``hostgroups`` as ``Foreman`` objects

    This class is also used by the ForemanHook classes :py:class:`.ForemanHookReceiver` and :py:class:`.ForemanRealmReceiver` to execute the
    required changes to the objects.
    """
    _priority_ = 99
    _target_ = "foreman"
    __session = None
    __acl_resolver = None
    client = None

    def __init__(self):
        self.env = Environment.getInstance()
        self.log = logging.getLogger(__name__)
        self.factory = ObjectFactory.getInstance()
        self.incoming_base = "%s,%s" % (self.env.config.get("foreman.incoming-rdn", "ou=incoming"), self.env.base)
        self.__marked_hosts = {}
        if self.env.config.get("foreman.host") is None:
            self.log.warning("no foreman host configured")
        else:
            self.init_client(self.env.config.get("foreman.host"))

            host = socket.getfqdn() if self.env.config.get("http.host", default="localhost") in ["0.0.0.0", "127.0.0.1"] else self.env.config.get("http.host", default="localhost")
            ssl = self.env.config.get('http.ssl', default=None)
            protocol = "https" if ssl and ssl.lower() in ['true', 'yes', 'on'] else "http"

            self.gosa_server = "%s://%s:%s/rpc" % (protocol, host, self.env.config.get('http.port', default=8080))
            self.mqtt_host = None

            mqtt_host = self.env.config.get('mqtt.host')
            if mqtt_host is not None:
                if mqtt_host == "localhost":
                    mqtt_host = host
                self.mqtt_host = "%s:%s" % (mqtt_host, self.env.config.get('mqtt.port', default=1883))

            # Listen for object events
            if not hasattr(sys, '_called_from_test'):
                zope.event.subscribers.append(self.__handle_events)

    def init_client(self, url):
        self.client = ForemanClient(url)

    def serve(self):
        # Load DB session
        self.__session = self.env.getDatabaseSession('backend-database')

        if self.client:
            sched = PluginRegistry.getInstance("SchedulerService").getScheduler()
            sched.add_interval_job(self.flush_parameter_setting, seconds=10, tag='_internal', jobstore="ram")

    def __handle_events(self, event):
        """
        React on object modifications to keep active ACLs up to date.
        """
        if event.__class__.__name__ == "IndexScanFinished":
            self.log.info("index scan finished, triggered foreman sync")
            self.create_container()

            self.sync_type("ForemanHostGroup")
            self.sync_type("ForemanHost")

            # read discovered hosts
            self.sync_type("ForemanHost", "discovered_hosts")

    def create_container(self):
        # create incoming ou if not exists
        index = PluginRegistry.getInstance("ObjectIndex")
        res = index.search({'dn': self.incoming_base}, {'_type': 1})

        if len(res) == 0:
            ou = ObjectProxy(self.env.base, "IncomingDeviceContainer")
            ou.commit()

    def sync_type(self, object_type, foreman_type=None):
        """ sync foreman objects, request data from foreman API and apply those values to the object """
        index = PluginRegistry.getInstance("ObjectIndex")
        backend_attributes = self.factory.getObjectBackendProperties(object_type)

        if "Foreman" not in backend_attributes:
            self.log.warning("no foreman backend attributes found for '%s' object" % object_type)
            return

        if foreman_type is None:
            foreman_type = backend_attributes["Foreman"]["type"]

        new_data = self.client.get(foreman_type)
        found_ids = []
        ForemanBackend.modifier = "foreman"

        uuid_attribute = backend_attributes["Foreman"]["_uuidSourceAttribute"] \
            if '_uuidSourceAttribute' in backend_attributes["Foreman"] else backend_attributes["Foreman"]["_uuidAttribute"]

        for data in new_data["results"]:
            found_ids.append(str(data[uuid_attribute]))
            self.log.debug(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
            self.log.debug(">>> START syncing foreman object of type '%s' with id '%s'" % (object_type, data[uuid_attribute]))
            foreman_object = self.get_object(object_type, data[uuid_attribute], data=data)
            if foreman_type == "discovered_hosts":
                # add status to data
                if not foreman_object.is_extended_by("ForemanHost"):
                    foreman_object.extend("ForemanHost")
                foreman_object.status = "discovered"
                self.update_type(object_type, foreman_object, data, uuid_attribute)
            else:
                self.update_type(object_type, foreman_object, data, uuid_attribute)
            self.log.debug("<<< DONE syncing foreman object of type '%s' with id '%s'" % (object_type, data[uuid_attribute]))
            self.log.debug("<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<")

        types = self.factory.getObjectTypes()[object_type]
        base_type = object_type if types["base"] is True else types["extends"][0]

        # delete not existing ones
        query = {'_type': base_type}
        if base_type != object_type:
            query["extension"] = object_type

        if len(found_ids):
            query[backend_attributes["Foreman"]["_uuidAttribute"]] = {'not_in_': found_ids}
        if foreman_type == "discovered_hosts":
            query["status"] = "discovered"

        res = index.search(query, {'dn': 1})

        for entry in res:
            foreman_object = ObjectProxy(entry['dn'])
            self.log.debug("removing %s '%s'" % (base_type, foreman_object.dn))
            foreman_object.remove()

        ForemanBackend.modifier = None

    def get_object(self, object_type, oid, create=True, data=None):
        backend_attributes = self.factory.getObjectBackendProperties(object_type)
        foreman_object = None

        if "Foreman" not in backend_attributes:
            self.log.warning("no foreman backend attributes found for '%s' object" % object_type)
            return

        types = self.factory.getObjectTypes()[object_type]
        base_type = object_type if types["base"] is True else types["extends"][0]

        index = PluginRegistry.getInstance("ObjectIndex")

        # check if the object already exists
        query = {
            '_type': base_type,
            backend_attributes["Foreman"]["_uuidAttribute"]: str(oid)
        }
        if types["base"] is False:
            query["extension"] = object_type

        res = index.search(query, {'dn': 1})

        if len(res) == 0:
            if create is True:
                # no object found -> create one
                self.log.debug(">>> creating new %s" % object_type)
                base_dn = self.env.base
                if object_type == "ForemanHost":
                    base_dn = self.incoming_base
                foreman_object = ObjectProxy(base_dn, base_type)
                uuid_extension = foreman_object.get_extension_off_attribute(backend_attributes["Foreman"]["_uuidAttribute"])
                if base_type != uuid_extension and not foreman_object.is_extended_by(uuid_extension):
                    foreman_object.extend(uuid_extension)
                setattr(foreman_object, backend_attributes["Foreman"]["_uuidAttribute"], str(oid))
        else:
            # open existing object
            self.log.debug(">>> open existing %s with DN: %s" % (object_type, res[0]["dn"]))
            foreman_object = ObjectProxy(res[0]["dn"], data={object_type: {"Foreman": data}} if data is not None else None)

        return foreman_object

    def update_type(self, object_type, object, data, uuid_attribute=None, update_data=None):
        """
        Directly updates the objects attribute values. Generates a dict with structure:

        .. code-block:: python

            { "extension_name": {
                    "backend_name": {
                        "attribute_name": "attribute_value",
                        ...
                    },
                    ...
                },
                ...
            }

        This data is directly applied to the object in the same way as if it has been requested from the related backend.
        So all in-filters and type conversion are processed.

        :param object_type: GOsa object name as defined in the object definitions (e.g. ForemanHost)
        :type object_type: string
        :param object: Object that should be updated
        :type object: :py:class:`gosa.backend.objects.proxy.ObjectProxy`
        :param data: key/values of attributes to update
        :type data: dict
        :param uuid_attribute: Name of the identifier attribute in the foreman backend (e.g. id)
        :type uuid_attribute: string
        :param update_data: additional data to be applied {<extension_name>: {<backend_name>: { <attribute_name>: <attribute_value>, ...}}}
        :type update_data: dict
        """

        properties = self.factory.getObjectProperties(object_type)
        backend_attributes = self.factory.getObjectBackendProperties(object_type)
        mappings = ForemanBackend.extract_mapping(backend_attributes["Foreman"])
        set_on_create = []
        if "setoncreate" in backend_attributes["Foreman"]:
            set_on_create = [x.split(":") for x in backend_attributes["Foreman"]["setoncreate"].split(",") if len(x)]

        if uuid_attribute is None:

            uuid_attribute = backend_attributes["Foreman"]["_uuidSourceAttribute"] \
                if '_uuidSourceAttribute' in backend_attributes["Foreman"] else backend_attributes["Foreman"]["_uuidAttribute"]

        if update_data is None:
            update_data = {}

        if object.get_mode() == "create":
            for entry in set_on_create:
                value = data[entry[0]] if entry[0] in data else None
                if entry[0][0:5] == "self." and hasattr(object, entry[0][5:]):
                    value = getattr(object, entry[0][5:])

                if value is not None:
                    current_value = getattr(object, entry[1])

                    if current_value is None:
                        self.log.info("setting %s to %s" % (entry[1], value))
                        setattr(object, entry[1], value)
                    elif isinstance(current_value, list) and len(current_value) == 0:
                        self.log.info("setting %s to %s" % (entry[1], [value]))
                        setattr(object, entry[1], [value])

        def update(key, value, backend=None):
            # check if we need to extend the object before setting the property
            extension = object.get_extension_off_attribute(key)
            if extension not in update_data:
                update_data[extension] = {}
            if backend is not None:
                if backend not in update_data[extension]:
                    update_data[extension][backend] = {}
                update_data[extension][backend][key] = value
            else:
                for backend_name in properties[key]['backend']:
                    if backend_name not in update_data[extension]:
                        update_data[extension][backend_name] = {}
                    update_data[extension][backend_name][key] = value

        for key, value in data.items():
            if key == uuid_attribute and object.get_mode() != "create":
                continue
            try:
                # collect extensions etc.
                if hasattr(object, key) and key in properties:
                    if value is not None:
                        update(key, value)
                        if key in mappings:
                            update(mappings[key], value)

            except Exception as e:
                self.log.warning("error updating attribute '%s' of object %s (%s) with value '%s': '%s" %
                                 (key, object.uuid, object_type, value, e))
                raise e

        self.log.debug(">>> applying data to '%s': %s" % (object_type, update_data))
        object.apply_data(update_data, force_update=True)
        self.log.debug(">>> commiting '%s'" % object_type)
        object.commit()

    def remove_type(self, object_type, oid):
        ForemanBackend.modifier = "foreman"
        factory = ObjectFactory.getInstance()

        foreman_object = self.get_object(object_type, oid, create=False)
        if foreman_object is not None:
            types = factory.getObjectTypes()[object_type]
            base_type = object_type if types["base"] is True else types["extends"][0]
            if base_type is False:
                if not foreman_object.is_extended_by(object_type):
                    # do not delete object which does not have the extension
                    self.log.debug("device '%s' has no '%s' extension, deletion skipped" % (foreman_object.dn, object_type))
                    raise ForemanException(C.make_error('NO_FOREMAN_OBJECT'))

            # delete the complete object
            foreman_object.remove()

            # else:
            #     # no base type just retract
            #     foreman_object.retract(object_type)
            #     foreman_object.commit()

        ForemanBackend.modifier = None

    @Command(__help__=N_("Get all available foreman LSB names"))
    @cache_return(timeout_secs=60)
    def getForemanLsbNames(self):
        res = {}
        if self.client:
            data = self.client.get("operatingsystems")
            if "results" in data:
                for entry in data["results"]:
                    res[entry["release_name"]] = {"value": entry["release_name"]}
        return res

    @Command(__help__=N_("Get release name of an operating system"))
    @cache_return(timeout_secs=600)
    def getForemanReleaseName(self, operatingsystem_id):
        if self.client:
            data = self.client.get("operatingsystems", id=operatingsystem_id)
            return data["release_name"]
        return None

    @Command(__help__=N_("Get details of a single foreman hostgroup."))
    @cache_return(timeout_secs=60)
    def getForemanHostgroup(self, id, attributes=None):
        res = {}
        if self.client:
            data = self.client.get("hostgroups", id=id)
            parent_id = data["parent_id"]
            while parent_id is not None:
                pdata = self.client.get("hostgroups", id=parent_id)
                data.update({k:v for k,v in pdata.items() if v})
                parent_id = pdata["parent_id"]

            if isinstance(attributes, list) and len(attributes) > 0:
                res = [data[x] for x in attributes if x in data]
            else:
                res = data
        return res

    @Command(__help__=N_("Get available foreman compute resources."))
    def getForemanComputeResources(self, *args):
        """
        Command for populating a list of foreman compute resource as dict.
        Example:

        .. code-block:: python

            { <resource-id>: {"value": <resource-name>}}

        """
        return self.__get_key_values("compute_resources", value_format="{name} ({provider})")

    @Command(__help__=N_("Get available foreman domains."))
    def getForemanDomains(self, *args):
        return self.__get_key_values("domains")

    @Command(__help__=N_("Get available foreman hostgroups."))
    def getForemanHostgroups(self, *args):
        path = "hostgroups"
        if len(args) and "hostgroup_id" in args[0] and args[0]["hostgroup_id"] is not None:
            path += "/%s" % args[0]["hostgroup_id"]
        return self.__get_hostgroup_key_values(path)

    @cache_return(timeout_secs=60)
    def __get_hostgroup_key_values(self, path):
        res = {}
        if self.client:
            data = self.client.get(path)

            if "results" in data:
                for entry in data["results"]:
                    name = entry["name"]
                    parent_id = entry["parent_id"]
                    while parent_id is not None:
                        pdata = self.client.get("hostgroups", id=parent_id)
                        name = "%s/%s" % (pdata["name"], name)
                        parent_id = pdata["parent_id"]
                    res[entry["id"]] = {"value": name}
        return res

    @Command(__help__=N_("Get available foreman operating systems."))
    def getForemanOperatingSystems(self, *args):
        return self.__get_key_values("operatingsystems")

    @Command(__help__=N_("Get available foreman architectures."))
    def getForemanArchitectures(self, *args):
        return self.__get_os_related_key_values("architectures", args[0] if len(args) else None)

    @Command(__help__=N_("Get available foreman operating systems."))
    def getForemanOperatingSystems(self, *args):
        return self.__get_key_values("operatingsystems")

    @Command(__help__=N_("Get available foreman partition tables."))
    def getForemanPartitionTables(self, *args):
        return self.__get_os_related_key_values("ptables", args[0] if len(args) else None)

    @Command(__help__=N_("Get available foreman media."))
    def getForemanMedia(self, *args):
        return self.__get_os_related_key_values("media", args[0] if len(args) else None)

    def __get_os_related_key_values(self, path, data=None):
        if data is not None and "operatingsystem_id" in data and data["operatingsystem_id"] is not None:
            path = "operatingsystems/%s/%s" % (data["operatingsystem_id"], path)
        return self.__get_key_values(path)

    @Command(__help__=N_("Get available foreman hostgroups."))
    def getForemanDiscoveredHostId(self, name):
        if self.client:
            data = self.client.get("discovered_hosts", id=name)
            return data["id"]

    @cache_return(timeout_secs=60)
    def __get_key_values(self, type, key_name="id", value_format="{name}"):
        res = {}
        if self.client:
            data = self.client.get(type)

            if "results" in data:
                for entry in data["results"]:
                    res[entry[key_name]] = {"value": value_format.format(**entry)}
        return res

    @Command(__help__=N_("Get discovered hosts as search key(dn): value(cn) pairs."))
    def getForemanDiscoveredHostsForSelection(self, *args):
        index = PluginRegistry.getInstance("ObjectIndex")

        res = index.search({
            "_type": "Device",
            "extension": "ForemanHost",
            "status": "discovered"
        }, {"dn": 1, "cn": 1})

        selection_data = {}

        for entry in res:
            selection_data[entry["dn"]] = {"value": entry["cn"][0]}

        return selection_data

    @Command(__help__=N_("Get foreman hosts as search key(dn): value(cn) pairs."))
    def getForemanHostsForSelection(self, *args):
        index = PluginRegistry.getInstance("ObjectIndex")

        res = index.search({
            "_type": "Device",
            "extension": "ForemanHost",
            "not_": {"status": "discovered"}
        }, {"dn": 1, "cn": 1})

        selection_data = {}

        for entry in res:
            selection_data[entry["dn"]] = {"value": entry["cn"][0]}

        return selection_data

    @Command(needsUser=True, __help__=N_("Get discovered hosts as search result."))
    def getForemanDiscoveredHosts(self, user):
        methods = PluginRegistry.getInstance("RPCMethods")

        query = and_(
            ObjectInfoIndex.uuid == ExtensionIndex.uuid,
            ObjectInfoIndex.uuid == KeyValueIndex.uuid,
            ObjectInfoIndex._type == "Device",
            ExtensionIndex.extension == "ForemanHost",
            KeyValueIndex.key == "status",
            KeyValueIndex.value == "discovered"
        )

        query_result = self.__session.query(ObjectInfoIndex).filter(query)
        res = {}
        for item in query_result:
            methods.update_res(res, item, user, 1)

        return list(res.values())

    @Command(needsUser=True, __help__=N_("Force a Puppet agent run on the host"))
    def doPuppetRun(self, user, host_id):
        self.__run_host_command(host_id, "puppetrun", None)

    @Command(needsUser=True, __help__=N_("Boot host from specified device"))
    def bootHost(self, user, host_id, device):
        """
        :param user: user name
        :param host_id: foreman host id
        :param device: boot device, valid devices are disk, cdrom, pxe, bios
        :return:
        """
        self.__run_host_command(host_id, "boot", {"device": device})

    @Command(needsUser=True, __help__=N_("Run a power operation on host"))
    def powerHost(self, user, host_id, power_action):
        """
        :param user: user name
        :param host_id: foreman host id
        :param power_action: power action, valid actions are (on/start), (off/stop), (soft/reboot), (cycle/reset), (state/status)
        """
        self.__run_host_command(host_id, "power", {"power_action": power_action})

    @Command(__help__=N_("Checks if a host supports power operations"))
    def supportsPower(self, uuid, compute_resource_id):
        return uuid is not None and compute_resource_id is not None

    @Command(__help__=N_("Get a foreman setting by ID"))
    def getForemanSetting(self, setting_id):
        if self.client:
            try:
                data = self.client.get("settings", id=setting_id)
                return data["value"]
            except ForemanBackendException as e:
                self.log.error("Error requesting foreman setting %s: %s" % (setting_id, e.message))
                return None

    def __run_host_command(self, host_id, command, data):
        if self.client:
            self.client.put("hosts/%s" % host_id, command, data)

    def __get_resolver(self):
        if self.__acl_resolver is None:
            self.__acl_resolver = PluginRegistry.getInstance("ACLResolver")
        return self.__acl_resolver

    def add_host(self, hostname, base=None):

        # create dn
        if base is None:
            base = self.incoming_base

        ForemanBackend.modifier = "foreman"

        device = self.get_object("ForemanHost", hostname, create=False)
        if device is None:
            self.log.debug("Realm request: creating new host with hostname: %s" % hostname)
            device = ObjectProxy(base, "Device")
            device.extend("ForemanHost")
            device.cn = hostname
            # commit now to get a uuid
            device.commit()

            # re-open to get a clean object
            device = ObjectProxy(device.dn)
        else:
            self.log.debug("Realm request: use existing host with hostname: %s" % hostname)

        try:

            if not device.is_extended_by("ForemanHost"):
                device.extend("ForemanHost")

            # Generate random client key
            h, key, salt = generate_random_key()

            # While the client is going to be joined, generate a random uuid and an encoded join key
            cn = str(uuid.uuid4())
            if not device.is_extended_by("RegisteredDevice"):
                device.extend("RegisteredDevice")
            if not device.is_extended_by("simpleSecurityObject"):
                device.extend("simpleSecurityObject")
            device.deviceUUID = cn
            device.status_Offline = True

            # reset discovered status
            if device.status == "discovered":
                device.status = "unknown"

            device.userPassword = "{SSHA}" + encode(h.digest() + salt).decode()

            device.commit()
            self.mark_for_parameter_setting(hostname, {"status": "added"})
            return "%s|%s" % (key, cn)

        except Exception as e:
            # remove created device again because something went wrong
            # self.remove_type("ForemanHost", hostname)
            self.log.error(str(e))
            raise e

        finally:
            ForemanBackend.modifier = None

    def mark_for_parameter_setting(self, hostname, status):
        """ mark this host to be parametrized later """
        self.__marked_hosts[hostname] = status

    def flush_parameter_setting(self, hostname=None):
        id = None
        if hostname in self.__marked_hosts and self.__marked_hosts[hostname]["use_id"] is not None:
            id = self.__marked_hosts[hostname]["use_id"]
        if hostname is not None:
            self.write_parameters(hostname, use_id=id)
            if hostname in self.__marked_hosts:
                del self.__marked_hosts[hostname]
        else:
            if len(self.__marked_hosts.keys()) == 0:
                return

            for hostname in list(self.__marked_hosts):
                try:
                    status = self.__marked_hosts[hostname]
                    self.write_parameters(hostname, use_id=status["use_id"] if "use_id" in status else None)
                except:
                    pass

    def write_parameters(self, hostname=None, use_id=None):
        """
        Write foreman parameters either global if no hostname/use_id is given or as host parameter

        :param hostname: host name (optional)
        :param use_id: host ID (optional)
        """
        self.log.debug("writing host parameters to %s" % hostname)
        self.client.set_common_parameter("gosa-server", self.gosa_server, host=use_id if use_id is not None else hostname)
        if self.mqtt_host is not None:
            self.client.set_common_parameter("gosa-mqtt", self.mqtt_host, host=use_id if use_id is not None else hostname)
        self.client.set_common_parameter("gosa-domain", self.env.domain, host=use_id if use_id is not None else hostname)

        if hostname is not None and hostname in self.__marked_hosts:
            del self.__marked_hosts[hostname]


class ForemanRealmReceiver(object):
    """
    Webhook handler for foreman realm events (Content-Type: application/vnd.foreman.hostevent+json).
    Foreman sends these events whenever a new host is created with gosa-realm provider, or e.g. the hostgroup of an existing host
    has been changed to a hostgroup with gosa-realm provider set.
    """
    skip_next_event = {}

    def __init__(self):
        self.type = N_("Foreman host event")
        self.env = Environment.getInstance()
        self.log = logging.getLogger(__name__)

    def handle_request(self, request_handler):
        foreman = PluginRegistry.getInstance("Foreman")
        self.log.debug(request_handler.request.body)
        data = loads(request_handler.request.body)

        if data["action"] in ForemanRealmReceiver.skip_next_event:
            del ForemanRealmReceiver.skip_next_event[data["action"]]
            return

        # TODO disable hook logging to file
        with open("foreman-log.json", "a") as f:
            f.write("%s,\n" % dumps(data, indent=4, sort_keys=True))

        ForemanBackend.modifier = "foreman"
        if data['action'] == "create":
            # new client -> join it
            try:
                key = foreman.add_host(data['hostname'])

                # send key as otp to foremans realm proxy
                request_handler.finish(dumps({
                    "randompassword": key
                }))
            except Exception as e:
                request_handler.finish(dumps({
                    "error": "%s" % e
                }))
                raise e

        elif data['action'] == "delete":
            try:
                foreman.remove_type("ForemanHost", data['hostname'])
            except Exception as e:
                request_handler.finish(dumps({
                    "error": "%s" % e
                }))
                raise e

        ForemanBackend.modifier = None


class ForemanHookReceiver(object):
    """ Webhook handler for foreman realm events (Content-Type: application/vnd.foreman.hookevent+json) """
    skip_next_event = {}

    def __init__(self):
        self.type = N_("Foreman hook event")
        self.env = Environment.getInstance()
        self.log = logging.getLogger(__name__)

    def handle_request(self, request_handler):
        foreman = PluginRegistry.getInstance("Foreman")
        data = loads(request_handler.request.body)
        self.log.debug(data)

        # TODO disable hook logging to file
        with open("foreman-log.json", "a") as f:
            f.write("%s,\n" % dumps(data, indent=4, sort_keys=True))

        if data["event"] in ForemanHookReceiver.skip_next_event and data["object"] in ForemanHookReceiver.skip_next_event[data["event"]]:
            ForemanHookReceiver.skip_next_event[data["event"]].remove(data["object"])
            self.log.info("skipped '%s' event for object: '%s'" % (data["event"], data["object"]))
            return

        data_keys = list(data['data'].keys())
        if len(data_keys) == 1:
            type = data_keys[0]
        else:
            # no type given -> skipping this event as other might come with more information
            self.log.warning("skipping event '%s' for object '%s' as no type information is given in data: '%s'" % (data["event"],
                                                                                                                  data["object"],
                                                                                                                  data["data"]))
            return

        # search for real data
        if len(data['data'][type].keys()) == 1:
            # something like {data: 'host': {host: {...}}}
            #             or {data: 'discovered_host': {host: {...}}}
            payload_data = data['data'][type][list(data['data'][type].keys())[0]]
        else:
            payload_data = data['data'][type]

        factory = ObjectFactory.getInstance()
        foreman_type = type
        if type == "discovered_host":
            type = "host"

        object_types = factory.getObjectNamesWithBackendSetting("Foreman", "type", "%ss" % type)
        object_type = object_types[0] if len(object_types) else None

        backend_attributes = factory.getObjectBackendProperties(object_type) if object_type is not None else None
        self.log.debug("Hookevent: '%s' for '%s' (%s)" % (data['event'], data['object'], object_type))

        uuid_attribute = None
        if "Foreman" in backend_attributes:
            uuid_attribute = backend_attributes["Foreman"]["_uuidSourceAttribute"] \
                if '_uuidSourceAttribute' in backend_attributes["Foreman"] else backend_attributes["Foreman"]["_uuidAttribute"]

        ForemanBackend.modifier = "foreman"
        update_data = {}

        if data['event'] in ["update", "create"] and foreman_type == "host":
            id = payload_data["id"] if "id" in payload_data else None
            try:
                foreman.write_parameters(id if id is not None else data['object'])
            except:
                foreman.mark_for_parameter_setting(data['object'], {
                    "status": "created",
                    "use_id": id
                })

        if data['event'] == "after_commit" or data['event'] == "update" or data['event'] == "after_create" or data['event'] == "create":
            host = None
            if data['event'] == "update" and foreman_type == "host" and "mac" in payload_data and payload_data["mac"] is not None:
                # check if we have an discovered host for this mac
                index = PluginRegistry.getInstance("ObjectIndex")
                res = index.search({
                    "_type": "Device",
                    "extension": ["ForemanHost", "ieee802Device"],
                    "macAddress": payload_data["mac"],
                    "status": "discovered"
                }, {"dn": 1})

                if len(res):
                    self.log.debug("update received for existing host with dn: %s" % res[0]["dn"])
                    host = ObjectProxy(res[0]["dn"])

                    if foreman_type != "discovered_host" and host.is_extended_by("ForemanHost"):
                        host.status = "unknown"

            foreman_object = foreman.get_object(object_type, payload_data[uuid_attribute], create=host is None)
            if foreman_object and host:
                if foreman_object != host:
                    self.log.debug("using known host instead of creating a new one")
                    # host is the formerly discovered host, which might have been changed in GOsa for provisioning
                    # so we want to use this one, foreman_object is the joined one, so copy the credentials from foreman_object to host
                    if not host.is_extended_by("RegisteredDevice"):
                        host.extend("RegisteredDevice")
                    if not host.is_extended_by("simpleSecurityObject"):
                        host.extend("simpleSecurityObject")
                    host.deviceUUID = foreman_object.deviceUUID
                    host.userPassword = foreman_object.userPassword
                    host.cn = foreman_object.cn

                    # now delete the formerly joined host
                    foreman_object.remove()
                    foreman_object = host

            elif foreman_object is None and host is not None:
                foreman_object = host

            elif foreman_type == "discovered_host":
                self.log.debug("setting discovered state for %s" % payload_data[uuid_attribute])
                if not foreman_object.is_extended_by("ForemanHost"):
                    foreman_object.extend("ForemanHost")
                foreman_object.status = "discovered"

            if foreman_type == "host":
                old_build_state = foreman_object.build

            foreman.update_type(object_type, foreman_object, payload_data, uuid_attribute, update_data=update_data)
            if foreman_type == "host" and old_build_state is True and foreman_object.build is False and \
                            foreman_object.status == "ready":
                # send notification
                e = EventMaker()
                ev = e.Event(e.Notification(
                    e.Title(N_("Host ready")),
                    e.Body(N_("Host '%s' has been successfully build." % foreman_object.cn)),
                    e.Icon("@Ligature/pc"),
                    e.Timeout("10000")
                ))
                event_object = objectify.fromstring(etree.tostring(ev, pretty_print=True).decode('utf-8'))
                SseHandler.notify(event_object)

        elif data['event'] == "after_destroy":
            # print("Payload: %s" % payload_data)
            foreman.remove_type(object_type, payload_data[uuid_attribute])

            # because foreman sends the after_commit event after the after_destroy event
            # we need to skip this event, otherwise the host would be re-created
            if "after_commit" not in ForemanHookReceiver.skip_next_event:
                ForemanHookReceiver.skip_next_event["after_commit"] = [data['object']]
            else:
                ForemanHookReceiver.skip_next_event["after_commit"].append(data['object'])

            # add garbage collection for skip
            sobj = PluginRegistry.getInstance("SchedulerService")
            sobj.getScheduler().add_date_job(self.cleanup_event_skipper,
                                             datetime.datetime.now() + datetime.timedelta(minutes=1),
                                             args=("after_commit", data['object']),
                                             tag='_internal', jobstore='ram')

        else:
            self.log.info("unhandled hook event '%s' received for '%s'" % (data['event'], type))

        ForemanBackend.modifier = None

    def cleanup_event_skipper(self, event, id):
        if event in ForemanHookReceiver.skip_next_event and id in ForemanHookReceiver.skip_next_event[event]:
            self.log.warning("'%s' event for object '%s' has been marked for skipping but was never received. Removing the mark now" % (event, id))
            ForemanHookReceiver.skip_next_event[event].remove(id)


class ForemanException(Exception):
    pass
