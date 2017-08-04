
# This file is part of the GOsa project.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.
import logging
import uuid
import sys

import requests
import zope
from requests.auth import HTTPBasicAuth

from gosa.backend.objects import ObjectProxy, ObjectFactory
from gosa.common import Environment
from gosa.common.components import Plugin, Command
from gosa.common.handler import IInterfaceHandler
from zope.interface import implementer
from gosa.common.error import GosaErrorHandler as C
from gosa.common.utils import N_, generate_random_key, encrypt_key
from gosa.common.components import PluginRegistry
from gosa.common.gjson import loads, dumps
from gosa.common.components.jsonrpc_utils import Binary
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
    _priority_ = 99
    _target_ = "foreman"
    __session = None
    __acl_resolver = None
    client = None

    def __init__(self):
        self.env = Environment.getInstance()
        self.log = logging.getLogger(__name__)
        self.factory = ObjectFactory.getInstance()
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
            self._sync_type("ForemanHostGroup")
            self._sync_type("ForemanHost")

    def _sync_type(self, object_type):
        """ sync foreman objects, request data from foreman API and apply those values to the object """
        index = PluginRegistry.getInstance("ObjectIndex")
        backend_attributes = self.factory.getObjectBackendProperties(object_type)

        if "Foreman" not in backend_attributes:
            self.log.warning("no foreman backend attributes found for '%s' object" % object_type)
            return

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
                foreman_object = ObjectProxy(self.env.base, base_type)
                # if types["base"] is False:
                #     # no base object extend it
                #     for required_ext in types["requires"]:
                #         foreman_object.extend(required_ext)
                #
                #     foreman_object.extend(object_type)

                # set the identifier attribute
                setattr(foreman_object, backend_attributes["Foreman"]["_uuidAttribute"], str(oid))

                # # set all required attributes to make the object storeable
                # if "setOnCreate" in backend_attributes["Foreman"]:
                #     initial_data = {}
                #     for attr_name in backend_attributes["Foreman"]["setOnCreate"].split(","):
                #         if attr_name in data and data[attr_name] is not None:
                #             initial_data[attr_name] = data[attr_name]
                #
                #     foreman_object.apply_data({
                #         object_type: {
                #             "Foreman": initial_data
                #         }
                #     })
                # # save initially to have in in the db for relations
                # foreman_object.commit()
                #
                # foreman_object = ObjectProxy(foreman_object.dn, data={object_type: {"Foreman": data}})
        else:
            # open existing object
            self.log.debug(">>> open existing %s with DN: %s" % (object_type, res[0]["dn"]))
            foreman_object = ObjectProxy(res[0]["dn"], data={object_type: {"Foreman": data}})

        return foreman_object

    def update_type(self, object_type, object, data, uuid_attribute=None):
        """ directly update the object attribute values """
        # now apply the values

        properties = self.factory.getObjectProperties(object_type)

        if uuid_attribute is None:
            backend_attributes = self.factory.getObjectBackendProperties(object_type)
            uuid_attribute = backend_attributes["Foreman"]["_uuidSourceAttribute"] \
                if '_uuidSourceAttribute' in backend_attributes["Foreman"] else backend_attributes["Foreman"]["_uuidAttribute"]

        update_data = {}
        for key, value in data.items():
            if key == uuid_attribute and object.get_mode() != "create":
                continue
            try:
                # collect extensions etc.
                if hasattr(object, key) and key in properties:
                    if value is not None:
                        # check if we need to extend the object before setting the property
                        extension = object.get_extension_off_attribute(key)
                        if extension not in update_data:
                            update_data[extension] = {}
                        for backend in properties[key]['backend']:
                            if backend not in update_data[extension]:
                                update_data[extension][backend] = {}
                            update_data[extension][backend][key] = value

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

    @Command(__help__=N_("Get available foreman compute resources."))
    def getForemanComputeResources(self):
        res = []
        if self.client:
            data = self.client.get("compute_resources")

            if "results" in data:
                for entry in data["results"]:
                    res.append(entry["id"])
        return res

    def __get_resolver(self):
        if self.__acl_resolver is None:
            self.__acl_resolver = PluginRegistry.getInstance("ACLResolver")
        return self.__acl_resolver

    def add_host(self, hostname, base=None):

        # create dn
        if base is None:
            base = "%s,%s" % (self.env.config.get("foreman.incomingRdn", "ou=incoming"), self.env.base)

        ForemanBackend.modifier = "foreman"

        device = self.get_object("ForemanHost", hostname, create=False)
        if device is None:
            device = ObjectProxy(base, "Device")
            device.extend("ForemanHost")
            device.cn = hostname
            # commit now to get a uuid
            device.commit()

        elif not device.is_extended_by("ForemanHost"):
            device.extend("ForemanHost")
            device.cn = hostname

        try:
            # re-open to get a clean object
            device = ObjectProxy(device.uuid)

            # Generate random client key
            h, key, salt = generate_random_key()

            # While the client is going to be joined, generate a random uuid and an encoded join key
            cn = str(uuid.uuid4())
            device_key = encrypt_key(device.uuid.replace("-", ""), cn + key)

            device.extend("RegisteredDevice")
            device.extend("simpleSecurityObject")
            device.deviceUUID = cn
            device.deviceKey = Binary(device_key)
            # device.manager = manager
            device.status_Offline = True
            device.userPassword = "{SSHA}" + encode(h.digest() + salt).decode()

            device.commit()
            return key

        except:
            # remove created device again because something went wrong
            # self.remove_host(hostname)
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
        self.log.info(request_handler.request.body)
        data = loads(request_handler.request.body)

        ForemanBackend.modifier = "foreman"
        if data['action'] == "create":
            # new client -> join it
            key = foreman.add_host(data['hostname'])

            # send key as otp to foremans realm proxy
            request_handler.finish(dumps({
                "randompassword": key
            }))

        # elif data['action'] == "delete":
            # foreman.remove_host(data['hostname'])

        ForemanBackend.modifier = None


class ForemanHookReceiver(object):
    """ Webhook handler for foreman realm events (Content-Type: application/vnd.foreman.hookevent+json) """

    def __init__(self):
        self.type = N_("Foreman hook event")
        self.env = Environment.getInstance()
        self.log = logging.getLogger(__name__)

    def handle_request(self, request_handler):
        foreman = PluginRegistry.getInstance("Foreman")
        data = loads(request_handler.request.body)
        type = list(data['data'].keys())[0]

        # search for real data
        if len(data['data'][type].keys()) == 1 and type in data['data'][type]:
            # something like {data: 'host': {host: {...}}}
            payload_data = data['data'][type][type]
        else:
            payload_data = data['data'][type]

        factory = ObjectFactory.getInstance()
        object_types = factory.getObjectNamesWithBackendSetting("Foreman", "type", "%ss" % type)
        object_type = object_types[0] if len(object_types) else None

        backend_attributes = factory.getObjectBackendProperties(object_type) if object_type is not None else None

        uuid_attribute = None
        if "Foreman" in backend_attributes:
            uuid_attribute = backend_attributes["Foreman"]["_uuidSourceAttribute"] \
                if '_uuidSourceAttribute' in backend_attributes["Foreman"] else backend_attributes["Foreman"]["_uuidAttribute"]

        ForemanBackend.modifier = "foreman"

        if data['event'] == "after_commit" or data['event'] == "update" or data['event'] == "after_create" or data['event'] == "create":
            foreman_object = foreman.get_object(object_type, payload_data[uuid_attribute])
            foreman.update_type(object_type, foreman_object, payload_data, uuid_attribute)

        elif data['event'] == "after_destroy":
            foreman.remove_type(object_type, payload_data[uuid_attribute])

        else:
            self.log.info("unhandled hook event '%s' received for '%s'" % (data['event'], type))

        ForemanBackend.modifier = None


class ForemanException(Exception):
    pass
