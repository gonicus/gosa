
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
import requests
import zope
from requests.auth import HTTPBasicAuth
from sqlalchemy import and_

from gosa.backend.objects import ObjectProxy
from gosa.backend.objects.index import ObjectInfoIndex, KeyValueIndex
from gosa.common import Environment
from gosa.common.components import Command
from gosa.common.components import Plugin
from gosa.backend.exceptions import ACLException
from gosa.common.handler import IInterfaceHandler
from zope.interface import implementer
from gosa.common.error import GosaErrorHandler as C
from gosa.common.utils import N_
from gosa.common.components import PluginRegistry
from gosa.common.gjson import loads


C.register_codes(dict(
    FOREMAN_UNKNOWN_TYPE=N_("Unknown object type '%(type)s'"),
    NO_MAC=N_("No MAC given to identify host '%(hostname)s'"),
    DEVICE_NOT_FOUND=N_("Cannot find device '%(hostname)s'"),
    NO_FOREMAN_HOST=N_("This host is not managed by foreman"),
    MULTIPLE_DEVICES_FOUND=N_("(%devices)s found for hostname '%(hostname)s'")
))

FM_STATUS_GLOBAL_OK = 0
FM_STATUS_GLOBAL_WARNING = 1
FM_STATUS_GLOBAL_ERROR = 2

FM_STATUS_BUILD = 0
FM_STATUS_BUILD_PENDING = 1

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
        elif response.status_code == 404:
            raise ForemanException(C.make_error('FOREMAN_UNKNOWN_TYPE', type=type))
        else:
            response.raise_for_status()

    def update_host_groups(self):
        index = PluginRegistry.getInstance("ObjectIndex")
        new_data = self.get("hostgroups")
        for hostgroup_data in new_data["results"]:
            # check if hostgroup already exists
            res = index.search({'_type': 'ForemanHostGroup', 'cn': hostgroup_data['name']}, {'dn': 1})

            if len(res) == 0:
                # create new host group
                group = ObjectProxy(self.env.base, "ForemanHostGroup")
            else:
                # open group
                group = ObjectProxy(res[0]['dn'])

            # update values
            group.cn = hostgroup_data['name']
            # TODO: needs to be replaced with an extra attribute for this purpose (_uuidAttribute in object definition needs to be
            # changed too)
            group.description = str(hostgroup_data['id'])
            group.os = hostgroup_data["operatingsystem_name"]
            group.domain = hostgroup_data["domain_name"]
            group.environment = hostgroup_data["environment_name"]
            group.commit()


@implementer(IInterfaceHandler)
class Foreman(Plugin):
    _priority_ = 99
    _target_ = "foreman"
    __session = None
    __acl_resolver = None

    def __init__(self):
        self.env = Environment.getInstance()
        self.log = logging.getLogger(__name__)
        self.log.info("initializing foreman plugin")
        self.client = ForemanClient()

        # Listen for object events
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
            self.client.update_host_groups()

    def __get_resolver(self):
        if self.__acl_resolver is None:
            self.__acl_resolver = PluginRegistry.getInstance("ACLResolver")
        return self.__acl_resolver

    @Command(needsUser=True, __help__=N_("Adds a host"))
    def addHost(self, user, hostname, params=None, base=None):

        # create dn
        if base is None:
            base = self.env.base

        if user != self:
            topic = "%s.objects.Device" % self.env.domain
            result = self.__get_resolver().check(user, topic, "c")
            if result is None:
                raise ACLException(C.make_error('PERMISSION_CREATE', target=base))

        if params is None or 'mac' not in params:
            # no MAC to identify the host
            raise ForemanException(C.make_error("NO_MAC", hostname=hostname))
        mac = params['mac']
        obj = ObjectProxy(base, "Device")
        obj.extend("ieee802Device")
        obj.extend("IpHost")
        obj.extend("ForemanHost")
        obj.cn = hostname
        obj.macAddress = mac
        self.__update_host(obj, params)
        return obj

    @Command(needsUser=True, __help__=N_("Deletes a host"))
    def removeHost(self, user, hostname, params=None):
        # find the host
        device = self.__get_host_object(hostname)
        if not device.is_extended_by("ForemanHost"):
            # do not delete hosts which have not been reported by foreman
            self.log.debug("device '%s' is not foreman host, deletion skipped" % device.dn)
            raise ForemanException(C.make_error('NO_FOREMAN_HOST'))

        if user != self:
            # check ACL
            topic = "%s.objects.Device" % self.env.domain
            result = self.__get_resolver().check(user, topic, "d", base=device.get_parent_dn())
            if result is None:
                raise ACLException(C.make_error('PERMISSION_REMOVE', target=device.get_parent_dn()))

        # remove it
        device.remove()

    def update_host(self, hostname):
        """Requests current values from the Foreman api and updates the device"""
        device = self.__get_host_object(hostname)
        if not device.is_extended_by("ForemanHost"):
            # do not delete hosts which have not been reported by foreman
            self.log.debug("device '%s' is not foreman host, deletion skipped" % device.dn)
            raise ForemanException(C.make_error('NO_FOREMAN_HOST'))

        new_data = self.client.get("hosts", id=hostname)
        self.__update_host(device, new_data["results"])

    def __update_host(self, device, data):
        if 'location_id' in data:
            device.l = data['location_id']

        if 'ip' in data:
            try:
                ipaddress.ip_address(data['ip'])
                device.ipHostNumber = data['ip']
            except ValueError:
                pass

        foreman_status = data['global_status']

        if foreman_status == FM_STATUS_GLOBAL_OK:
            # request build status from foreman
            res = self.client.get("hosts/%s/status/build" % device.cn)
            if res['status'] == FM_STATUS_BUILD:
                device.status = "ready"
            if res['status'] == FM_STATUS_BUILD_PENDING:
                device.status = "pending"

        elif foreman_status == FM_STATUS_GLOBAL_WARNING:
            device.status = "warning"

        elif foreman_status == FM_STATUS_GLOBAL_ERROR:
            device.status = "error"

        device.commit()

        if 'hostgroup_name' in data:
            # check if group exists (create if not)
            index = PluginRegistry.getInstance("ObjectIndex")
            res = index.search({'_type': 'ForemanHostGroup', 'cn': data['hostgroup_name']}, {'dn': 1})

            if len(res) == 0:
                # create new host group
                group = ObjectProxy(device.get_adjusted_parent_dn(), "ForemanHostGroup")
                group.cn = data['hostgroup_name']

                group.member.append(device.dn)
                group.commit()
            else:
                # open group
                group = ObjectProxy(res[0]['dn'])

                if device.dn not in group.member:
                    group.member.append(device.dn)
                    group.commit()

            # add to group
            device = ObjectProxy(device.dn)
            device.groupMembership = data['hostgroup_name']
            device.commit()

    def __get_host_object(self, hostname):
        query = and_(ObjectInfoIndex.uuid == KeyValueIndex.uuid,
                     KeyValueIndex.key == "cn",
                     KeyValueIndex.value == hostname,
                     ObjectInfoIndex._type == "Device")

        res = self.__session.query(ObjectInfoIndex).filter(query)

        if res.count() == 0:
            raise ForemanException(C.make_error("DEVICE_NOT_FOUND", hostname=hostname))
        elif res.count() > 1:
            raise ForemanException(C.make_error("MULTIPLE_DEVICES_FOUND", hostname=hostname, devices=res.count()))
        else:
            res_device = res.first()
            return ObjectProxy(res_device.uuid)


class ForemanWebhookReceiver(object):
    """ Webhook handler for foreman events (Content-Type: application/vnd.foreman.hostevent+json) """

    def __init__(self):
        self.type = N_("Foreman host event")

    def handle_request(self, request_handler):
        foreman = PluginRegistry.getInstance("Foreman")
        data = loads(request_handler.request.body)
        print("FOREMAN WEBHOOK: %s" % data)

        if data['action'] == "create":
            device = foreman.addHost(foreman, data['hostname'], data['parameters'])
            # send devices uuid as otp to foremans realm proxy
            request_handler.write(device.uuid)

        elif data['action'] == "delete":
            foreman.removeHost(foreman, data['hostname'], data['parameters'])


class ForemanException(Exception):
    pass
