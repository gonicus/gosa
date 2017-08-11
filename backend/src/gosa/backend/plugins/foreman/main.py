
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

import requests
import zope
from requests.auth import HTTPBasicAuth
from sqlalchemy import and_

from gosa.backend.objects import ObjectProxy, ObjectFactory
from gosa.backend.objects.index import ObjectInfoIndex, ExtensionIndex, KeyValueIndex
from gosa.common import Environment
from gosa.common.components import Plugin, Command
from gosa.common.handler import IInterfaceHandler
from zope.interface import implementer
from gosa.common.error import GosaErrorHandler as C
from gosa.common.utils import N_, generate_random_key, cache_return
from gosa.common.components import PluginRegistry
from gosa.common.gjson import loads, dumps
from base64 import b64encode as encode
from gosa.backend.objects.backend.back_foreman import Foreman as ForemanBackend

C.register_codes(dict(
    FOREMAN_UNKNOWN_TYPE=N_("Unknown object type '%(type)s'"),
    NO_MAC=N_("No MAC given to identify host '%(hostname)s'"),
    DEVICE_NOT_FOUND=N_("Cannot find device '%(hostname)s'"),
    NO_FOREMAN_OBJECT=N_("This object is not managed by foreman"),
    MULTIPLE_DEVICES_FOUND=N_("(%devices)s found for hostname '%(hostname)s'"),
    HOSTGROUP_NOT_FOUND=N_("Cannot find hostgroup with id '%(group_id)s'"),
    MULTIPLE_HOSTGROUPS_FOUND=N_("(%groups)s found for group id '%(group_id)s'"),
))


class ForemanClient(object):
    """Client for the Foreman REST-API v2"""
    headers = {'Accept': 'version=2,application/json'}

    def __init__(self):
        self.env = Environment.getInstance()
        self.log = logging.getLogger(__name__)
        self.foreman_host = self.env.config.get("foreman.host", "http://localhost/api")

    def get(self, type, id=None):

        url = "%s/%s" % (self.foreman_host, type)
        if id is not None:
            url += "/%s" % id

        self.log.debug("sending GET request to %s" % url)
        response = requests.get(url,
                                headers=self.headers,
                                verify=self.env.config.get("foreman.verify", "true") == "true",
                                auth=HTTPBasicAuth(self.env.config.get("foreman.user"), self.env.config.get("foreman.password")))
        if response.ok:
            data = response.json()
            return data
        else:
            response.raise_for_status()


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
        if self.env.config.get("foreman.host") is None:
            self.log.warning("no foreman host configured")
        else:
            self.log.info("initializing foreman plugin")
            self.client = ForemanClient()

            # Listen for object events
            if not hasattr(sys, '_called_from_test'):
                zope.event.subscribers.append(self.__handle_events)

    def serve(self):
        # Load DB session
        self.__session = self.env.getDatabaseSession('backend-database')

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
            self.log.debug(">>> START creating new foreman object of type '%s' with id '%s'" % (object_type, data[uuid_attribute]))
            foreman_object = self.get_object(object_type, data[uuid_attribute], data=data)
            if foreman_type == "discovered_hosts":
                # add status to data
                update_data = {}
                extension = foreman_object.get_extension_off_attribute("status")
                update_data[extension] = {"LDAP": {"status": "discovered"}}
                self.update_type(object_type, foreman_object, data, uuid_attribute, update_data=update_data)
            else:
                self.update_type(object_type, foreman_object, data, uuid_attribute)
            self.log.debug("<<< DONE creating new foreman object of type '%s' with id '%s'" % (object_type, data[uuid_attribute]))
            self.log.debug("<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<")

        # delete not existing ones
        if len(found_ids):
            res = index.search({'_type': object_type, backend_attributes["Foreman"]["_uuidAttribute"]: {'not_in_': found_ids}}, {'dn': 1})
        else:
            res = index.search({'_type': object_type}, {'dn': 1})

        for entry in res:
            foreman_object = ObjectProxy(entry['dn'])
            self.log.debug("removing %s '%s'" % (object_type, foreman_object.dn))
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

        if uuid_attribute is None:

            uuid_attribute = backend_attributes["Foreman"]["_uuidSourceAttribute"] \
                if '_uuidSourceAttribute' in backend_attributes["Foreman"] else backend_attributes["Foreman"]["_uuidAttribute"]

        if update_data is None:
            update_data = {}

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
        object.apply_data(update_data)
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

    @Command(__help__=N_("Get details of a single foreman hostgroup."))
    @cache_return(timeout_secs=60)
    def getForemanHostgroup(self, id, attributes=None):
        res = {}
        if self.client:
            data = self.client.get("hostgroups", id=id)
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
        return self.__get_key_values("hostgroups")

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

    @Command(needsUser=True, __help__=N_("Get discovered hosts."))
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
            device = ObjectProxy(base, "Device")
            device.extend("ForemanHost")
            device.cn = hostname
            # commit now to get a uuid
            device.commit()

            # re-open to get a clean object
            device = ObjectProxy(device.dn)

        try:

            if not device.is_extended_by("ForemanHost"):
                device.extend("ForemanHost")

            # Generate random client key
            h, key, salt = generate_random_key()

            # While the client is going to be joined, generate a random uuid and an encoded join key
            cn = str(uuid.uuid4())
            device.extend("RegisteredDevice")
            device.extend("simpleSecurityObject")
            device.deviceUUID = cn
            device.status_Offline = True
            device.userPassword = "{SSHA}" + encode(h.digest() + salt).decode()

            device.commit()
            return "%s|%s" % (key, cn)

        except:
            # remove created device again because something went wrong
            # self.remove_type("ForemanHost", hostname)
            raise

        finally:
            ForemanBackend.modifier = None


class ForemanRealmReceiver(object):
    """
    Webhook handler for foreman realm events (Content-Type: application/vnd.foreman.hostevent+json).
    Foreman sends these events whenaver a new host is created with gosa-realm provider, or e.g. the hostgroup of an existing host
    has been changed to a hostgroup with gosa-realm provider set.
    """

    def __init__(self):
        self.type = N_("Foreman host event")
        self.env = Environment.getInstance()
        self.log = logging.getLogger(__name__)

    def handle_request(self, request_handler):
        foreman = PluginRegistry.getInstance("Foreman")
        self.log.debug(request_handler.request.body)
        data = loads(request_handler.request.body)
        with open("foreman-log.json", "a") as f:
            f.write("%s,\n" % dumps(data, indent=4, sort_keys=True))

        ForemanBackend.modifier = "foreman"
        if data['action'] == "create":
            # new client -> join it
            try:
                key = foreman.add_host(data['hostname'])
                print(key)

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

    def __init__(self):
        self.type = N_("Foreman hook event")
        self.env = Environment.getInstance()
        self.log = logging.getLogger(__name__)
        self.skip_next_event = {}

    def handle_request(self, request_handler):
        foreman = PluginRegistry.getInstance("Foreman")
        data = loads(request_handler.request.body)
        self.log.debug(data)

        with open("foreman-log.json", "a") as f:
            f.write("%s,\n" % dumps(data, indent=4, sort_keys=True))

        if data["event"] in self.skip_next_event and data["object"] in self.skip_next_event[data["event"]]:
            self.skip_next_event[data["event"]].remove(data["object"])
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
                    host = ObjectProxy(res[0]["dn"])

            foreman_object = foreman.get_object(object_type, payload_data[uuid_attribute], create=host is None)
            if foreman_object and host:
                # host is the formerly discovered host, which might have been changed in GOsa for provisioning
                # so we want to use this one, foreman_object is the joined one, so copy the credentials from foreman_object to host
                if host.is_extended_by("RegisteredObject"):
                    host.extend("RegisteredDevice")
                if host.is_extended_by("simpleSecurityObject"):
                    host.extend("simpleSecurityObject")
                host.deviceUUID = foreman_object.deviceUUID
                host.userPassword = foreman_object.userPassword
                host.cn = foreman_object.cn

                # now delete the formerly joined host
                foreman_object.remove()
                foreman_object = host

            update_data = {}

            if foreman_type == "discovered_host":
                extension = foreman_object.get_extension_off_attribute("status")
                update_data[extension] = {"LDAP": {"status": "discovered"}}

            foreman.update_type(object_type, foreman_object, payload_data, uuid_attribute, update_data=update_data)

        elif data['event'] == "after_destroy":
            # print("Payload: %s" % payload_data)
            foreman.remove_type(object_type, payload_data[uuid_attribute])

            # because foreman sends the after_commit event after the after_destroy event
            # we need to skip this event, otherwise the host would be re-created
            if "after_commit" not in self.skip_next_event:
                self.skip_next_event["after_commit"] = [data['object']]
            else:
                self.skip_next_event["after_commit"].append(data['object'])

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
        if event in self.skip_next_event and id in self.skip_next_event[event]:
            self.log.warning("'%s' event for object '%s' has been marked for skipping but was never received. Removing the mark now" % (event, id))
            self.skip_next_event[event].remove(id)


class ForemanException(Exception):
    pass
