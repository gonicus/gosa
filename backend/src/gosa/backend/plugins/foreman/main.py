
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
import ipaddress
import sys

import requests
import zope
from requests.auth import HTTPBasicAuth
from sqlalchemy import and_

from gosa.backend.objects import ObjectProxy
from gosa.backend.objects.index import ObjectInfoIndex, KeyValueIndex
from gosa.common import Environment
from gosa.common.components import Plugin
from gosa.backend.exceptions import ACLException, EntryNotFound
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
    NO_FOREMAN_HOST=N_("This host is not managed by foreman"),
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
        if self.env.config.get("foreman.host") is None:
            self.log.warning("no foreman host configured")
        else:
            self.log.info("initializing foreman plugin")
            self.client = ForemanClient()

            # Listen for object events
            if not hasattr(sys, '_called_from_test'):
                zope.event.subscribers.append(self.__handle_events)

        # some simple property mapping for data extraction
        self.props = {
            "hostgroup": {
                "name": "cn"
            }
        }

    def serve(self):
        # Load DB session
        self.__session = self.env.getDatabaseSession('backend-database')

    def __handle_events(self, event):
        """
        React on object modifications to keep active ACLs up to date.
        """
        if event.__class__.__name__ == "IndexScanFinished":
            self.log.info("index scan finished, triggered foreman sync")
            self.sync_host_groups()
            self.sync_hosts()

    def sync_hosts(self):
        index = PluginRegistry.getInstance("ObjectIndex")
        new_data = self.client.get("hosts")
        found_ids = []
        for host_data in new_data["results"]:
            try:
                device = self.__get_host_object(host_data["name"])
            except EntryNotFound:
                # create a new host
                device = ObjectProxy(self.env.base, "Device")
                device.extend("ForemanHost")
                device.cn = host_data["name"]
            found_ids.append(host_data["name"])
            self.__update_host(device, host_data)

        if len(found_ids):
            res = index.search({'_type': 'ForemanHost', 'cn': {'not_in_': found_ids}}, {'dn': 1})
        else:
            # delete all
            res = index.search({'_type': 'ForemanHost'}, {'dn': 1})

        for entry in res:
            host = ObjectProxy(entry['dn'])
            self.log.debug("removing foremanHost '%s'" % host.cn)
            host.remove()

    def sync_host_groups(self):
        index = PluginRegistry.getInstance("ObjectIndex")
        new_data = self.client.get("hostgroups")
        found_ids = []
        for hostgroup_data in new_data["results"]:
            group_id = str(hostgroup_data["id"])
            try:
                group = self.__get_hostgroup_object(group_id)
            except EntryNotFound:
                # create a new hostgroup
                group = ObjectProxy(self.env.base, "ForemanHostGroup")
                group.foremanGroupId = group_id

            self.__update_hostgroup(group, hostgroup_data)
            found_ids.append(group_id)

        if len(found_ids):
            res = index.search({'_type': 'ForemanHostGroup', 'foremanGroupId': {'not_in_': found_ids}}, {'dn': 1})
        else:
            res = index.search({'_type': 'ForemanHostGroup'}, {'dn': 1})
        for entry in res:
            group = ObjectProxy(entry['dn'])
            self.log.debug("removing foremanHostGroup '%s'" % group.cn)
            group.remove()

    def __get_resolver(self):
        if self.__acl_resolver is None:
            self.__acl_resolver = PluginRegistry.getInstance("ACLResolver")
        return self.__acl_resolver

    def add_host(self, hostname, base=None):

        # create dn
        if base is None:
            base = self.env.base

        try:
            device = self.__get_host_object(hostname)
            if not device.is_extended_by("ForemanHost"):
                device.extend("ForemanHost")
                device.cn = hostname

        except EntryNotFound:
            device = ObjectProxy(base, "Device")
            device.extend("ForemanHost")
            device.cn = hostname
            # commit now to get a uuid
            device.commit()

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

    def remove_host(self, hostname):
        # find the host
        try:
            device = self.__get_host_object(hostname)

            if not device.is_extended_by("ForemanHost"):
                # do not delete hosts which have not been reported by foreman
                self.log.debug("device '%s' is no foreman host, deletion skipped" % device.dn)
                raise ForemanException(C.make_error('NO_FOREMAN_HOST'))

            # remove it
            device.remove()
        except EntryNotFound:
            # no device found to delete
            self.log.info("no device with hostname '%s' found for deletion" % hostname)

    def update_host(self, host, data=None):
        """Requests current values from the Foreman api and updates the device"""
        hostname = host
        device = host
        if isinstance(host, ObjectProxy):
            hostname = host.cn
        else:
            device = self.__get_host_object(host)

        if not device.is_extended_by("ForemanHost"):
            # do not delete hosts which have not been reported by foreman
            self.log.debug("device '%s' is no foreman host, update skipped" % device.dn)
            raise ForemanException(C.make_error('NO_FOREMAN_HOST'))
        if data is None:
            data = self.client.get("hosts", id=hostname)
        self.__update_host(device, data)

    def __update_host(self, device, data):

        if 'ip' in data and data['ip'] is not None:
            try:
                if not device.is_extended_by("IpHost"):
                    device.extend("IpHost")
                ipaddress.ip_address(data['ip'])
                device.ipHostNumber = data['ip']
            except ValueError:
                pass

        if 'uuid' in data and data['uuid'] is not None and device.is_extended_by("RegisteredDevice"):
            # update the UUID of a joined client
            device.deviceUUID = data['uuid']

        if 'mac' in data and data['mac'] is not None:
            try:
                if not device.is_extended_by("ieee802Device"):
                    device.extend("ieee802Device")
                device.macAddress = data['mac']
            except ValueError:
                pass

        self.log.debug("updating foreman host '%s'" % device.cn)
        device.commit()

        if 'hostgroup_id' in data and data['hostgroup_id'] is not None:
            # check if group exists (create if not)
            index = PluginRegistry.getInstance("ObjectIndex")
            res = index.search({'_type': 'ForemanHostGroup', 'foremanGroupId': str(data['hostgroup_id'])}, {'dn': 1})

            if len(res) == 0:
                # create new host group
                group = ObjectProxy(device.get_adjusted_parent_dn(), "ForemanHostGroup")
                group.cn = data['hostgroup_name']
                group.foremanGroupId = str(data['hostgroup_id'])

                group.member.append(device.dn)
                group.commit()
            else:
                # open group
                group = ObjectProxy(res[0]['dn'])

                if device.dn not in group.member:
                    group.member.append(device.dn)
                    group.commit()

    def __get_host_object(self, hostname):
        query = and_(ObjectInfoIndex.uuid == KeyValueIndex.uuid,
                     KeyValueIndex.key == "cn",
                     KeyValueIndex.value == hostname,
                     ObjectInfoIndex._type == "Device")

        res = self.__session.query(ObjectInfoIndex).filter(query)

        if res.count() == 0:
            raise EntryNotFound(C.make_error("DEVICE_NOT_FOUND", hostname=hostname))
        elif res.count() > 1:
            raise ForemanException(C.make_error("MULTIPLE_DEVICES_FOUND", hostname=hostname, devices=res.count()))
        else:
            res_device = res.first()
            return ObjectProxy(res_device.uuid)

    def __get_hostgroup_object(self, group_id):
        query = and_(ObjectInfoIndex.uuid == KeyValueIndex.uuid,
                     KeyValueIndex.key == "foremanGroupId",
                     KeyValueIndex.value == group_id,
                     ObjectInfoIndex._type == "ForemanHostGroup")

        res = self.__session.query(ObjectInfoIndex).filter(query)

        if res.count() == 0:
            raise EntryNotFound(C.make_error("HOSTGROUP_NOT_FOUND", group_id=group_id))
        elif res.count() > 1:
            raise ForemanException(C.make_error("MULTIPLE_HOSTGROUPS_FOUND", group_id=group_id, groups=res.count()))
        else:
            res_device = res.first()
            return ObjectProxy(res_device.uuid)

    def update_hostgroup(self, group=None, data=None):
        """Requests current values from the Foreman api and updates the device"""
        if group is None:
            if 'id' in data:
                group = str(data['id'])
            else:
                self.log.error("no group id given to update the hostgroup")
                return

        hostgroup = group
        group_id = group
        if isinstance(group, ObjectProxy):
            group_id = group.foremanGroupId
        else:
            try:
                hostgroup = self.__get_hostgroup_object(group_id)
            except EntryNotFound:
                # create a new hostgroup
                hostgroup = ObjectProxy(self.env.base, "ForemanHostGroup")
                hostgroup.foremanGroupId = group_id

        if data is None:
            data = self.client.get("hostgroups", id=group_id)
        self.__update_hostgroup(hostgroup, data)

    def __update_hostgroup(self, hostgroup, data):
        # update the simple values
        for key, value in self.props['hostgroup'].items():
            if key in data and data[key] is not None:
                self.log.debug("set '%s'->'%s' to '%s' in hostgroup" % (key, value, data[key]))
                setattr(hostgroup, value, data[key])

        self.log.debug("updating foreman hostgroup '%s'" % hostgroup.cn)
        hostgroup.commit()

    def remove_hostgroup(self, group_id):
        try:
            hostgroup = self.__get_hostgroup_object(group_id)
            hostgroup.remove()
        except EntryNotFound:
            self.log.debug("no hostgroup with id '%s' found for deletion" % group_id)


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

        if data['action'] == "create":
            # new client -> join it
            key = foreman.add_host(data['hostname'])

            # send key as otp to foremans realm proxy
            request_handler.finish(dumps({
                "randompassword": key
            }))

        elif data['action'] == "delete":
            ForemanBackend.modifier = "foreman"
            foreman.remove_host(data['hostname'])
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

        ForemanBackend.modifier = "foreman"

        if data['event'] == "after_commit" or data['event'] == "update" or data['event'] == "after_create" or data['event'] == "create":
            if type == "hostgroup":
                foreman.update_hostgroup(data=payload_data)
            elif type == "host":
                foreman.update_host(data['object'], data=payload_data)

        elif data['event'] == "after_destroy":
            if type == "hostgroup":
                foreman.remove_hostgroup(payload_data['id'])
            elif type == "host":
                foreman.remove_host(data['object'])

        else:
            self.log.info("unhandled hook event '%s' received for '%s'" % (data['event'], type))

        ForemanBackend.modifier = None


class ForemanException(Exception):
    pass
