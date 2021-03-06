
# This file is part of the GOsa project.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.
import collections
import datetime
import hashlib
import logging
import uuid
import sys

import ldap
from ldap.dn import dn2str, str2dn
from lxml import objectify, etree

import zope
import socket

from sqlalchemy import and_

from gosa.backend.exceptions import ProxyException
from gosa.backend.components.httpd import get_server_url
from gosa.backend.lock import GlobalLock
from gosa.backend.objects import ObjectProxy, ObjectFactory
from gosa.backend.objects.index import ObjectInfoIndex, ExtensionIndex, KeyValueIndex, Cache, Schema
from gosa.backend.routes.sse.main import SseHandler
from gosa.common import Environment
from gosa.common.components import Plugin, Command
from gosa.common.env import make_session
from gosa.common.event import EventMaker
from gosa.common.handler import IInterfaceHandler
from zope.interface import implementer
from gosa.common.error import GosaErrorHandler as C
from gosa.common.utils import N_, generate_random_key, cache_return
from gosa.common.components import PluginRegistry
from gosa.common.gjson import loads, dumps
from base64 import b64encode as encode
from gosa.backend.objects.backend.back_foreman import Foreman as ForemanBackend, ForemanClient, ForemanBackendException, ForemanClientCache

C.register_codes(dict(
    FOREMAN_UNKNOWN_TYPE=N_("Unknown object type '%(type)s'"),
    NO_MAC=N_("No MAC given to identify host '%(hostname)s'"),
    DEVICE_NOT_FOUND=N_("Cannot find device '%(hostname)s'"),
    NO_FOREMAN_OBJECT=N_("This object is not managed by foreman"),
    MULTIPLE_DEVICES_FOUND=N_("%(devices)s found for hostname '%(hostname)s'"),
    HOSTGROUP_NOT_FOUND=N_("Cannot find hostgroup with id '%(group_id)s'"),
    MULTIPLE_HOSTGROUPS_FOUND=N_("%(groups)s found for group id '%(group_id)s'"),
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
    syncing = False
    __sync_retry_interval = 1

    def __init__(self):
        self.env = Environment.getInstance()
        self.log = logging.getLogger(__name__)
        self.factory = ObjectFactory.getInstance()
        incoming_base = self.env.config.get("foreman.host-rdn")
        self._after_sync_callbacks = collections.deque()

        if incoming_base is not None and len(incoming_base.strip()) > 0 and incoming_base != "None":
            incoming_base = "%s,%s" % (incoming_base, self.env.base)
        else:
            incoming_base = self.env.base
        self.type_bases = {"ForemanHost": incoming_base}

        group_rdn = self.env.config.get("foreman.group-rdn")
        if group_rdn is not None and len(group_rdn.strip()) > 0 and group_rdn != "None":
            self.type_bases["ForemanHostGroup"] = "%s,%s" % (group_rdn, self.env.base)
        else:
            self.type_bases["ForemanHostGroup"] = self.env.base

        self.__marked_hosts = {}
        if self.env.config.get("foreman.host") is None:
            self.log.warning("no foreman host configured")
        else:
            self.init_client(self.env.config.get("foreman.host"))
            self.gosa_server = "%s/rpc" % get_server_url()
            self.mqtt_host = None

            mqtt_host = self.env.config.get('mqtt.host')
            if mqtt_host is not None:
                if mqtt_host == "localhost":
                    mqtt_host = socket.getfqdn()
                self.mqtt_host = "%s:%s" % (mqtt_host, self.env.config.get('mqtt.port', default=1883))

            # Listen for object events
            self.log.info("Initial-Sync: %s, startpassive: %s" % (self.env.config.getboolean("foreman.initial-sync", default=True), self.env.config.getboolean("core.startpassive", default=False)))
            if not hasattr(sys, '_called_from_test') and \
                    self.env.config.getboolean("foreman.initial-sync", default=True) is True and \
                    self.env.mode != "proxy":
                zope.event.subscribers.append(self.__handle_events)

    def init_client(self, url):
        self.client = ForemanClient(url)

    def serve(self):

        if self.client and self.env.mode != "proxy" and not hasattr(sys, '_called_from_test'):
            sched = PluginRegistry.getInstance("SchedulerService").getScheduler()
            sched.add_interval_job(self.flush_parameter_setting, seconds=60, tag='_internal', jobstore="ram")

        # create needed container is they do not exist
        try:
            o = ObjectProxy(self.type_bases['ForemanHost'])
        except ProxyException as e:
            # create container
            dn_parts = str2dn(self.type_bases['ForemanHost'], flags=ldap.DN_FORMAT_LDAPV3)
            base_dn = dn2str(dn_parts[1:])
            o = ObjectProxy(base_dn, 'OrganizationalUnit')
            setattr(o, dn_parts[0][0][0], dn_parts[0][0][1])
            o.commit()

        if self.type_bases['ForemanHostGroup'] != self.type_bases['ForemanHost']:
            try:
                o = ObjectProxy(self.type_bases['ForemanHostGroup'])
            except ProxyException as e:
                # create container
                dn_parts = str2dn(self.type_bases['ForemanHostGroup'], flags=ldap.DN_FORMAT_LDAPV3)
                base_dn = dn2str(dn_parts[1:])
                o = ObjectProxy(base_dn, 'OrganizationalUnit')
                setattr(o, dn_parts[0][0][0], dn_parts[0][0][1])
                o.commit()

    def __handle_events(self, event):
        """
        React on object modifications to keep active ACLs up to date.
        """
        if event.__class__.__name__ == "IndexScanFinished":
            self.log.info("index scan finished, triggered foreman sync")
            self.__full_sync()

    def __full_sync(self):
        Foreman.syncing = True
        try:
            self.create_container()

            self.sync_release_names()

            self.sync_type("ForemanHostGroup")
            self.sync_type("ForemanHost")

            # read discovered hosts
            self.sync_type("ForemanHost", "discovered_hosts")

            Foreman.syncing = False
            while len(self._after_sync_callbacks):
                cb = self._after_sync_callbacks.popleft()
                cb()
            self.__sync_retry_interval = 1

        except Exception as e:
            # sync process did not succeed
            self.log.warning("Foreman sync process failed with error: %s. Re-scheduling sync in %s minutes." %
                             (str(e), self.__sync_retry_interval))
            sobj = PluginRegistry.getInstance("SchedulerService")
            sobj.getScheduler().add_date_job(self.__full_sync,
                                             datetime.datetime.now() + datetime.timedelta(minutes=self.__sync_retry_interval),
                                             tag='_internal', jobstore='ram')
            self.__sync_retry_interval *= min(2, 60)

        finally:
            Foreman.syncing = False

    def add_after_sync_callback(self, cb):
        self._after_sync_callbacks.append(cb)

    def create_container(self):
        # create incoming ou if not exists
        index = PluginRegistry.getInstance("ObjectIndex")
        res = index.search({'_parent_dn': self.type_bases["ForemanHost"], '_type': 'IncomingDeviceContainer'}, {'dn': 1})

        if len(res) == 0:
            ou = ObjectProxy(self.type_bases["ForemanHost"], "IncomingDeviceContainer")
            ou.commit()

        res = index.search({'_parent_dn': self.type_bases["ForemanHostGroup"], '_type': 'GroupContainer'}, {'dn': 1})
        if len(res) == 0:
            ou = ObjectProxy(self.type_bases["ForemanHostGroup"], "GroupContainer")
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

        uuid_attribute = backend_attributes["Foreman"]["_uuidSourceAttribute"] \
            if '_uuidSourceAttribute' in backend_attributes["Foreman"] else backend_attributes["Foreman"]["_uuidAttribute"]

        for data in new_data["results"]:
            found_ids.append(str(data[uuid_attribute]))
            self.log.debug(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
            self.log.debug(">>> START syncing foreman object of type '%s' with id '%s'" % (object_type, data[uuid_attribute]))
            foreman_object, delay_update = self.get_object(object_type, data[uuid_attribute], data=data)
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
            foreman_object = ObjectProxy(entry['dn'], open_mode="delete")
            self.log.debug("removing %s '%s'" % (base_type, foreman_object.dn))
            foreman_object.remove(skip_backend_writes=["Foreman"])

    def get_object(self, object_type, oid, create=True, data=None, read_only=False, from_db_only=False):
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

            # lookup the dirty ones
            dirty = index.get_dirty_objects()
            # check if the device is currently updated
            for entry in list(dirty.values()):
                if (hasattr(entry['obj'], backend_attributes["Foreman"]["_uuidAttribute"]) and
                        getattr(entry['obj'], backend_attributes["Foreman"]["_uuidAttribute"]) == str(oid) and
                        (types["base"] is False and entry["obj"].is_extended_by(object_type)) or
                        (types["base"] is True and entry["obj"].get_base_type() == base_type)):
                    # obj is currently being committed, we cannot change things in it
                    # but need a new instance
                    res.append({"dn": entry["obj"].dn})
                    return entry["obj"], True

            if create is True:
                # no object found -> create one
                self.log.debug(">>> creating new %s" % object_type)
                base_dn = self.env.base
                if object_type == "ForemanHost":
                    # get the IncomingDevice-Container
                    res = index.search({"_type": "IncomingDeviceContainer", "_parent_dn": self.type_bases["ForemanHost"]}, {"dn": 1})
                    if len(res) > 0:
                        base_dn = res[0]["dn"]
                    else:
                        base_dn = self.type_bases["ForemanHost"]
                elif object_type in self.type_bases:
                    base_dn = self.type_bases[object_type]
                foreman_object = ObjectProxy(base_dn, base_type)
                uuid_extension = foreman_object.get_extension_off_attribute(backend_attributes["Foreman"]["_uuidAttribute"])
                if base_type != uuid_extension and not foreman_object.is_extended_by(uuid_extension):
                    foreman_object.extend(uuid_extension)
                setattr(foreman_object, backend_attributes["Foreman"]["_uuidAttribute"], str(oid))
        else:
            # open existing object
            self.log.debug(">>> open existing %s with DN: %s" % (object_type, res[0]["dn"]))
            foreman_object = ObjectProxy(
                res[0]["dn"],
                data={object_type: {"Foreman": data}} if data is not None else None,
                read_only=read_only,
                from_db_only=from_db_only,
                skip_value_population=True
            )
            self.log.debug(">>> opened")

        return foreman_object, False

    def update_type(self, object_type, object, data, uuid_attribute=None, backend_data=None, update_data=None, delay_update=False):
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

        if backend_data is None:
            backend_data = {}

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
            if extension not in backend_data:
                backend_data[extension] = {}
            if backend is not None:
                if backend not in backend_data[extension]:
                    backend_data[extension][backend] = {}
                backend_data[extension][backend][key] = value
            else:
                for backend_name in properties[key]['backend']:
                    if backend_name not in backend_data[extension]:
                        backend_data[extension][backend_name] = {}
                    backend_data[extension][backend_name][key] = value

        for key, value in data.items():
            if key == uuid_attribute and object.get_mode() != "create":
                continue
            try:
                # collect extensions etc.
                if key in properties and hasattr(object, key):
                    if value is not None and (not isinstance(value, str) or len(value) > 0):
                        update(key, value)
                        if key in mappings:
                            update(mappings[key], value)

            except Exception as e:
                self.log.warning("error updating attribute '%s' of object %s (%s) with value '%s': '%s" %
                                 (key, object.uuid, object_type, value, e))
                raise e

        if delay_update is True:
            self.log.debug(">>> delay applying data to '%s': %s" % (object_type, update_data))
            PluginRegistry.getInstance("ObjectIndex").add_delayed_update(object, backend_data, inject=True)
            if update_data is not None:
                PluginRegistry.getInstance("ObjectIndex").add_delayed_update(object, update_data, inject=False)
        else:
            self.log.debug(">>> applying data to '%s': %s | %s" % (object_type, backend_data, update_data))
            object.inject_backend_data(backend_data, force_update=True)
            if update_data is not None:
                object.apply_update(update_data)
            self.log.debug(">>> commiting '%s'" % object_type)
            object.commit(skip_backend_writes=['Foreman'])

    def remove_type(self, object_type, oid):
        factory = ObjectFactory.getInstance()

        foreman_object, delay_update = self.get_object(object_type, oid, create=False)
        if foreman_object is not None:
            types = factory.getObjectTypes()[object_type]
            base_type = object_type if types["base"] is True else types["extends"][0]
            if base_type is False:
                if not foreman_object.is_extended_by(object_type):
                    # do not delete object which does not have the extension
                    self.log.debug("device '%s' has no '%s' extension, deletion skipped" % (foreman_object.dn, object_type))
                    raise ForemanException(C.make_error('NO_FOREMAN_OBJECT'))

            # delete the complete object
            foreman_object.remove(skip_backend_writes=['Foreman'])

            # else:
            #     # no base type just retract
            #     foreman_object.retract(object_type)
            #     foreman_object.commit()

    def sync_release_names(self):
        """
        The GOsa proxies need to know the release names of the operating systems,
        as we do not store them within any object, we save them in the Cache-Database.
        Proxies can query their replicated database for them
        """
        if self.client:
            data = self.client.get("operatingsystems")
            if "results" in data:
                # clear Database
                with make_session() as session:
                    session.query(Cache).filter((Cache.key.ilike("foreman.operating_system.%"))).delete(synchronize_session='fetch')
                    for entry in data["results"]:
                        self.sync_release_name(entry, session)
                    session.commit()

    def sync_release_name(self, data, session, check_if_exists=False, event="create"):
        id = "foreman.operating_system.%s" % data["id"]

        if check_if_exists is False and event == "after_commit":
            check_if_exists = True

        if event in ["create", "after_create", "after_commit"]:
            if check_if_exists is True:
                res = session.query(Cache).filter(Cache.key == id).one_or_none()
                if res is not None:
                    res.data = data
                    res.time = datetime.datetime.now()
                    return

            cache = Cache(
                key=id,
                data=data,
                time=datetime.datetime.now()
            )
            session.add(cache)
        elif event == "after_destroy":
            session.query(Cache).filter(Cache.key == id).delete()


    @Command(__help__=N_("Get all available foreman LSB names"), type="READONLY")
    @cache_return(timeout_secs=60)
    def getForemanLsbNames(self):
        res = {}
        with make_session() as session:
            for r in session.query(Cache.data).filter(Cache.key.ilike("foreman.operating_system.%")).all():
                res[r[0]["release_name"]] = {"value": r[0]["release_name"]}
        return res

    @Command(__help__=N_("Get release name of an operating system"), type="READONLY")
    @cache_return(timeout_secs=600)
    def getForemanReleaseName(self, operatingsystem_id):
        if operatingsystem_id is not None:
            with make_session() as session:
                res = session.query(Cache.data).filter(Cache.key == "foreman.operating_system.%s" % operatingsystem_id).one_or_none()
                if res is not None:
                    return res[0]["release_name"]
        return None

    @Command(__help__=N_("Get details of a single foreman hostgroup."))
    @cache_return(timeout_secs=60)
    def getForemanHostgroup(self, id, attributes=None):
        res = {}
        if self.client:
            data = self.client.get("hostgroups", object_id=id)
            parent_id = data["parent_id"]
            while parent_id is not None:
                pdata = self.client.get("hostgroups", object_id=parent_id)
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
                        pdata = self.client.get("hostgroups", object_id=parent_id)
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
            data = self.client.get("discovered_hosts", object_id=name)
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

    @Command(__help__=N_("Get all SystemsContainer search key(dn): value(dn) pairs."))
    def getSystemsContainers(self, *args):
        index = PluginRegistry.getInstance("ObjectIndex")

        res = index.search({"_type": {"in_": ["SystemsContainer"]}}, {"dn": 1})

        selection_data = {}

        for entry in res:
            selection_data[entry["dn"]] = {"value": entry["dn"]}

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

        with make_session() as session:
            query_result = session.query(ObjectInfoIndex).filter(query)
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
                data = self.client.get("settings", object_id=setting_id)
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

    def add_host(self, hostname, base=None, preliminary=False):
        """
        Add a new host with the given hostname (if it does not exist) and create a one time password for it
        :param hostname: FQDN of the host
        :param base: parent DN
        :param preliminary: set this to True if the host does not exist in foreman yet (e.g. during a realm request)
        :return: combination of key and uuid separated by |
        """

        # create dn
        index = PluginRegistry.getInstance("ObjectIndex")
        if base is None:
            # get the IncomingDevice-Container
            res = index.search({"_type": "IncomingDeviceContainer", "_parent_dn": self.type_bases["ForemanHost"]}, {"dn": 1})
            if len(res) > 0:
                base = res[0]["dn"]
            else:
                base = self.type_bases["ForemanHost"]

        device, delay_update = self.get_object("ForemanHost", hostname, create=False, from_db_only=True)
        update = {}

        if device is None:
            self.log.debug("Realm request: creating new host with hostname: %s" % hostname)
            device = ObjectProxy(base, "Device")
            update['cn'] = hostname
            if preliminary is False:
                device.extend("ForemanHost")
            device.cn = hostname
            # commit now to get a uuid
            device.commit(skip_backend_writes=["Foreman"])

            # re-open to get a clean object
            device = ObjectProxy(device.dn, from_db_only=True)
            delay_update = False
        else:
            self.log.debug("Realm request: use existing host with hostname: %s" % hostname)

        try:
            update['__extensions__'] = ['RegisteredDevice', 'simpleSecurityObject']
            if preliminary is False:
                update['__extensions__'].append("ForemanHost")

            # Generate random client key
            h, key, salt = generate_random_key()

            # While the client is going to be joined, generate a random uuid and an encoded join key
            if device.deviceUUID is None:
                update['deviceUUID'] = str(uuid.uuid4())
                device_uuid = update['deviceUUID']
            else:
                device_uuid = device.deviceUUID

            update['userPassword'] = device.userPassword
            if update['userPassword'] is None:
                update['userPassword'] = []
            elif device.otp is not None:
                update['userPassword'].remove(device.otp)
            update['userPassword'].append("{SSHA}" + encode(h.digest() + salt).decode())

            # make sure the client has the access rights he needs
            client_service = PluginRegistry.getInstance("ClientService")
            client_service.applyClientRights(device_uuid)

            if delay_update is True:
                # process the update when the current dirty object has been processed
                index.add_delayed_update(device, update)
            else:
                device.apply_update(update)
                device.commit(skip_backend_writes=["Foreman"])
            self.mark_for_parameter_setting(hostname, {"status": "added"})
            return "%s|%s" % (key, device_uuid)
        except Exception as e:
            self.log.error("Error during host creation: %s", str(e))


    def mark_for_parameter_setting(self, hostname, status):
        """ mark this host to be parametrized later """
        self.__marked_hosts[hostname] = status

    def flush_parameter_setting(self, hostname=None):
        id = None
        if hostname in self.__marked_hosts and self.__marked_hosts[hostname]["use_id"] is not None:
            id = self.__marked_hosts[hostname]["use_id"]
        if hostname is not None:
            done = False
            try:
                self.write_parameters(hostname, use_id=id)
            except ForemanBackendException as e:
                done = e.response.status_code == 404
            except Exception as e:
                self.log.error("Error writing host parameters: %s" % str(e))

            if done is True and hostname in self.__marked_hosts:
                    del self.__marked_hosts[hostname]
        else:
            if len(self.__marked_hosts.keys()) == 0:
                return

            done = []
            for hostname in list(self.__marked_hosts):
                try:
                    status = self.__marked_hosts[hostname]
                    self.write_parameters(hostname, use_id=status["use_id"] if "use_id" in status else None)
                    done.append(hostname)
                except ForemanBackendException as e:
                    if e.response.status_code == 404:
                        # this host does not exist anymore
                        done.append(hostname)

                except Exception as e:
                    self.log.error("Error writing host parameters: %s" % str(e))

            self.__marked_hosts = {hostname: entry for hostname, entry in self.__marked_hosts.items() if hostname not in done}

    def write_parameters(self, hostname=None, use_id=None):
        """
        Write foreman parameters either global if no hostname/use_id is given or as host parameter

        :param hostname: host name (optional)
        :param use_id: host ID (optional)
        """
        write_params = self.env.config.get('foreman.write-params', default='server,mqtt,domain')
        if write_params.lower() != "none":
            self.log.debug("writing host parameters to %s" % hostname)
            if 'server' in write_params:
                self.client.set_common_parameter("gosa-server", self.gosa_server, host=use_id if use_id is not None else hostname)
            if self.mqtt_host is not None and 'mqtt' in write_params:
                self.client.set_common_parameter("gosa-mqtt", self.mqtt_host, host=use_id if use_id is not None else hostname)

            if 'domain' in write_params:
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
        if GlobalLock.exists("scan_index"):
            request_handler.finish(dumps({
                "error": "GOsa is currently re-creating its index, all requests are blocked"
            }))
            return

        if Foreman.syncing is True:
            request_handler.finish(dumps({
                "error": "GOsa is currently syncing with Foreman, all requests are blocked"
            }))
            return

        foreman = PluginRegistry.getInstance("Foreman")
        self.log.debug(request_handler.request.body)
        data = loads(request_handler.request.body)

        if data["action"] in ForemanRealmReceiver.skip_next_event:
            del ForemanRealmReceiver.skip_next_event[data["action"]]
            return

        if self.env.config.get("foreman.event-log") is not None:
            with open(self.env.config.get("foreman.event-log"), "a") as f:
                f.write("%s,\n" % dumps(data, indent=4, sort_keys=True))

        self.log.debug("Hostevent: '%s' for '%s'" % (data['action'], data['hostname']))
        if data['action'] == "create":
            # new client -> join it
            try:
                self.log.debug("adding host")
                key = foreman.add_host(data['hostname'], preliminary=True)
                self.log.debug("returning otp key to foreman")
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
            # this is handled by the after_destroy hook, which is triggered before the host delete
            pass

class ForemanHookReceiver(object):
    """ Webhook handler for foreman hook events (Content-Type: application/vnd.foreman.hookevent+json) """
    skip_next_event = {}
    _queued_requests = []

    def __init__(self):
        self.type = N_("Foreman hook event")
        self.env = Environment.getInstance()
        self.log = logging.getLogger(__name__)
        self.index = PluginRegistry.getInstance("ObjectIndex")

    def process_queue(self):
        if Foreman.syncing is True:
            # still syncing
            self.log.info("GOsa is currently syncing with Foreman, cannot process the queue now. Waiting 10 seconds...")
            sobj = PluginRegistry.getInstance("SchedulerService")
            sobj.getScheduler().add_date_job(self.process_queue,
                                             datetime.datetime.now() + datetime.timedelta(seconds=10),
                                             tag='_internal', jobstore='ram')
            return
        queue = self._queued_requests
        self._queued_requests = []
        for data in queue:
            self._handle_data(data)

    def handle_request(self, request_handler):
        if GlobalLock.exists("scan_index"):
            request_handler.finish(dumps({
                "error": "GOsa is currently re-creating its index, all requests are blocked"
            }))
            return
        data = loads(request_handler.request.body)
        try:
            # respond before processing to avoid blocking
            request_handler.finish()
            self._handle_data(data)
        except Exception as e:
            self.log.error("Error during webhook processing: %s" % str(e))

    def check_for_change(self, uuid, hash, save_if_changed=True):
        """ Check if the incoming data contains a change we are interested in"""
        changed = False
        with make_session() as session:
            hash_entry = session.query(Schema).get('%s|Foreman' % uuid)
            if hash_entry is None:
                self.log.debug("no hash entry for UUID: %s" % uuid)
                changed = True
            else:
                self.log.debug("hash entry for UUID %s: %s == %s" % (uuid, hash_entry.hash, hash))
                changed = hash_entry.hash != hash

        if save_if_changed is True and changed is True:
            self._save_hash(uuid, hash)
        return changed

    def __to_hash(self, filtered_payload):
        dump = ""
        for key in sorted(filtered_payload):
            dump += "%s=%s," % (key, filtered_payload[key])
        md5s = hashlib.md5()
        md5s.update(dump.encode('utf-8'))
        return md5s.hexdigest()

    def _save_hash(self, uuid, hash):
        with make_session() as session:
            schema = Schema(type='%s|Foreman' % uuid, hash=hash)
            session.add(schema)
            session.commit()

    def _handle_data(self, data):
        foreman = PluginRegistry.getInstance("Foreman")

        if Foreman.syncing is True:
            self.log.error("GOsa is currently syncing with Foreman, all requests are blocked")
            if len(self._queued_requests) == 0:
                # add callback
                foreman.add_after_sync_callback(self.process_queue)
            self._queued_requests.append(data)
            return

        if self.env.config.get("foreman.event-log") is not None:
            with open(self.env.config.get("foreman.event-log"), "a") as f:
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

        if type == "operatingsystem":
            with make_session() as session:
                foreman.sync_release_name(payload_data, session, event=data['event'])
                session.commit()
                return
        factory = ObjectFactory.getInstance()
        foreman_type = type
        if type == "discovered_host":
            type = "host"

        object_types = factory.getObjectNamesWithBackendSetting("Foreman", "type", "%ss" % type)
        object_type = object_types[0] if len(object_types) else None

        backend_attributes = factory.getObjectBackendProperties(object_type) if object_type is not None else None
        self.log.debug("Hookevent: '%s' for '%s' (%s [%s])" % (data['event'], data['object'], object_type, foreman_type))

        uuid_attribute = None
        if "Foreman" in backend_attributes:
            uuid_attribute = backend_attributes["Foreman"]["_uuidSourceAttribute"] \
                if '_uuidSourceAttribute' in backend_attributes["Foreman"] else backend_attributes["Foreman"]["_uuidAttribute"]

        backend_props = [k for k in factory.getObjectProperties(object_type).keys() if "Foreman" in factory.getObjectProperties(object_type)[k]["backend"]]
        filtered_payload = {k: v for (k, v) in payload_data.items() if k in backend_props}

        backend_data = {}
        delay_update = False
        object_uuid = None

        if data['event'] == "after_commit":
            host = None
            update = {'__extensions__': []}
            filtered_payload_hash = self.__to_hash(filtered_payload)
            self.log.debug("filtered_payload: %s \n>>> Hash: %s" % (filtered_payload, filtered_payload_hash))
            if foreman_type == "host":

                id = payload_data["id"] if "id" in payload_data else None
                foreman.mark_for_parameter_setting(data['object'], {
                    "status": "created",
                    "use_id": id
                })
                index = PluginRegistry.getInstance("ObjectIndex")
                if "mac" in payload_data and payload_data["mac"] is not None:
                    # check if we have an discovered host for this mac
                    for entry in index.get_dirty_objects().values():
                        if entry["obj"].is_extended_by("ForemanHost") and \
                                hasattr(entry["obj"], "macAddress") and entry["obj"].macAddress == payload_data["mac"]:
                            host = entry["obj"]
                            object_uuid = entry["obj"].uuid
                            self.log.debug("found dirty host %s" % entry["obj"].dn)
                            delay_update = True
                            break

                    if host is None:
                        res = index.search({
                            "_type": "Device",
                            "extension": ["ForemanHost", "ieee802Device"],
                            "macAddress": payload_data["mac"]
                        }, {"dn": 1})

                        if len(res):
                            self.log.debug("update received for existing host with dn: %s" % res[0]["dn"])
                            object_uuid = res[0]["_uuid"]
                            if self.check_for_change(object_uuid, filtered_payload_hash, save_if_changed=True) is True:
                                host = ObjectProxy(res[0]["dn"], from_db_only=True)
                            else:
                                self.log.debug("skipping update for %s: no change detected" % res[0]["dn"])
                                return
                    elif self.check_for_change(object_uuid, filtered_payload_hash, save_if_changed=True) is False:
                        self.log.debug("skipping update for %s: no change detected" % host.dn)
                        return

                    if host is not None and foreman_type != "discovered_host" and host.is_extended_by("ForemanHost"):
                        update['status'] = "unknown"

                if host is None and "name" in payload_data and payload_data["name"] is not None:
                    # check if this host already exists (from a realm request)
                    for entry in index.get_dirty_objects().values():
                        if entry["obj"].is_extended_by("RegisteredDevice") and \
                                entry["obj"].is_extended_by("simpleSecurityObject") and \
                                hasattr(entry["obj"], "cn") and entry["obj"].cn == payload_data["name"]:
                            host = entry["obj"]
                            object_uuid = entry["obj"].uuid
                            self.log.debug("found dirty host %s" % entry["obj"].dn)
                            delay_update = True
                            break

                    if host is None:
                        res = index.search({
                            "_type": "Device",
                            "extension": ["RegisteredDevice", "simpleSecurityObject"],
                            "cn": payload_data["name"]
                        }, {"dn": 1})

                        if len(res):
                            self.log.debug("update received for existing host with dn: %s" % res[0]["dn"])
                            object_uuid = res[0]["_uuid"]
                            if self.check_for_change(object_uuid, filtered_payload_hash, save_if_changed=True) is True:
                                host = ObjectProxy(res[0]["dn"], from_db_only=True)
                            else:
                                self.log.debug("skipping update for %s: no change detected" % res[0]["dn"])
                                return

                    elif self.check_for_change(object_uuid, filtered_payload_hash, save_if_changed=True) is False:
                        self.log.debug("skipping update for %s: no change detected" % host.dn)
                        return

            # clear foreman client cache for this value
            ForemanClientCache.delete_cache(object_type, object_id=payload_data[uuid_attribute])

            foreman_object, skip_this = foreman.get_object(object_type, payload_data[uuid_attribute], data=payload_data, create=host is None, from_db_only=True)
            if foreman_object and host:
                if foreman_object.uuid != host.uuid:
                    self.log.debug("using known host instead of creating a new one")
                    # host is the formerly discovered host, which might have been changed in GOsa for provisioning
                    # so we want to use this one, foreman_object is the joined one, so copy the credentials from foreman_object to host
                    update['__extensions__'].extend(['RegisteredDevice', 'simpleSecurityObject'])
                    for attr in ['deviceUUID', 'userPassword', 'otp', 'userPassword']:
                        update[attr] = getattr(foreman_object, attr)

                    # now delete the formerly joined host
                    foreman_object.remove()
                    foreman_object = host

            elif foreman_object is None and host is not None:
                foreman_object = host

            elif foreman_type == "discovered_host":
                self.log.debug("setting discovered state for %s" % payload_data[uuid_attribute])
                update['__extensions__'].append('ForemanHost')
                update['status'] = 'discovered'

            if foreman_type == "host":
                old_build_state = foreman_object.build

            foreman.update_type(object_type,
                                foreman_object,
                                payload_data,
                                uuid_attribute,
                                backend_data=backend_data,
                                update_data=update,
                                delay_update=delay_update)

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

    def cleanup_event_skipper(self, event, id):
        if event in ForemanHookReceiver.skip_next_event and id in ForemanHookReceiver.skip_next_event[event]:
            self.log.warning("'%s' event for object '%s' has been marked for skipping but was never received. Removing the mark now" % (event, id))
            ForemanHookReceiver.skip_next_event[event].remove(id)


class ForemanException(Exception):
    pass
