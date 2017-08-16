# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.
import json
from threading import Thread
import logging
import requests
from requests import HTTPError
from requests.auth import HTTPBasicAuth

from gosa.backend.objects.backend import ObjectBackend
from gosa.common import Environment
from logging import getLogger

from gosa.common.gjson import dumps
from gosa.backend.exceptions import ObjectException


"""
Backend Attributes:
-------------------

* `type`: object type in foreman (e.g. hosts, hostgroups) 
* `mapping`: maps foreman attribute names to GOsa attribute names

.. code-block: xml
    :caption: Example configuration for foreman host objects

    <Backend type="hosts" _uuidAttribute="cn" _uuidSourceAttribute="name" needs="status">Foreman</Backend>

The Foreman backend needs to now the object type and the id to identify an object.
``_uuidSourceAttribute`` is optional and specifies the attribute name where the ID value can be found
in the foreman API response. If not specified the backend assumes that ``_uuidSourceAttribute == _uuidAttribute``.
These two settings are used to generate the API URL to access the object in foreman.
In this example the URL for HTTP-requests would be <foreman-host>/api/hosts/<cn>.

``needs`` is optional and defines attribute names which values the backend needs to know to perform its task.

*Example:*

    The ForemanHost needs to know the value of the status attribute. If status="discovered" the backend needs to talk to the API
    endpoint "discovered_hosts" instead of "hosts". 
"""


class Foreman(ObjectBackend):
    modifier = None

    @classmethod
    def set_modifier(cls, val):
        cls.modifier = val

    @classmethod
    def get_modifier(cls):
        return cls.modifier

    def __init__(self):
        # Initialize environment and logger
        self.env = Environment.getInstance()
        self.log = getLogger(__name__)
        self.client = ForemanClient()

    def load(self, uuid, info, back_attrs=None, data=None, needed=None):
        """
        Loading attribute values from foreman API

        :param uuid: Unique identifier in foreman (usually the id)
        :param info: dict of all object attributes that are related to foreman {<name>: <type>}
        :param back_attrs: backend configuration from object definition
        :param data: use this data instead of querying the backend
        :param needed: optional dict with attribute_name: value needed by this backend
        :return: results returned from foreman API
        """
        self.log.debug("load: %s, %s, %s, %s" % (uuid, info, back_attrs, data))
        if data is None:
            try:
                data = self.client.get(self.get_foreman_type(needed, back_attrs), id=uuid)
            except HTTPError as e:
                # something when wrong
                self.log.error("Error requesting foreman backend: %s" % e)
                data = {}
        return self.process_data(data, info)

    def identify(self, dn, params, fixed_rdn=None):
        self.log.debug("identify: %s, %s, %s" % (dn, params, fixed_rdn))
        return False

    def identify_by_uuid(self, uuid, params):
        self.log.debug("identify_by_uuid: %s, %s" % (uuid, params))
        return False

    def exists(self, misc, needed=None):
        self.log.debug("exists: %s" % misc)
        return False

    def remove(self, uuid, data, params, needed=None):
        self.log.debug("remove: %s, %s, %s" % (uuid, data, params))
        if Foreman.modifier != "foreman":

            def runner():
                try:
                    self.client.delete(self.get_foreman_type(needed, params), uuid)
                except HTTPError as e:
                    if e.response.status_code == 404 and self.client.check_backend() is True:
                        # foreman is up and running but responded with 404 -> nothing to delete
                        self.log.debug("no foreman object found")
                    else:
                        raise e


            # some changes (e.g. creating a host) trigger requests from foreman to gosa
            # so we need to run this request in a non blocking thread
            thread = Thread(target=runner)
            thread.start()

        else:
            self.log.info("skipping deletion request as the change is coming from the foreman backend")
        return True

    def retract(self, uuid, data, params, needed=None):
        self.remove(uuid, data, params, needed=needed)

    def get_foreman_type(self, data, params):
        if data is not None and "status" in data and data["status"] == "discovered":
            return "discovered_hosts"
        else:
            return params["type"]

    def extend(self, uuid, data, params, foreign_keys, dn=None, needed=None):
        """ Called when a base object is extended with a foreman object (e.g. device->foremanHost)"""
        self.log.debug("extend: %s, %s, %s, %s" % (uuid, data, params, foreign_keys))
        if Foreman.modifier != "foreman":
            type = self.get_foreman_type(needed, params)
            payload = self.__collect_data(data, params, type=type[:-1])

            # finally send the update to foreman
            self.log.debug("creating '%s' with '%s' to foreman" % (params["type"], payload))

            def runner():
                result = self.client.post(type, data=payload)
                self.log.debug("Response: %s" % result)

            # some changes (e.g. creating a host) trigger requests from foreman to gosa
            # so we need to run this request in a non blocking thread
            thread = Thread(target=runner)
            thread.start()

        else:
            self.log.info("skipping extend request as the change is coming from the foreman backend")
        return None

    def move_extension(self, uuid, new_base):
        self.log.debug("move_extension: %s, %s" % (uuid, new_base))
        pass

    def move(self, uuid, new_base, needed=None):
        self.log.debug("move: %s, %s" % (uuid, new_base))
        return True

    def create(self, base, data, params, foreign_keys=None, needed=None):
        self.log.debug("create: %s, %s, %s, %s" % (base, data, params, foreign_keys))
        return None

    def update(self, uuid, data, params, needed=None):
        self.log.debug("update: '%s', '%s', '%s'" % (uuid, data, params))
        if Foreman.modifier != "foreman":
            type = self.get_foreman_type(needed, params)
            payload = self.__collect_data(data, params, type=type[:-1])

            # finally send the update to foreman
            self.log.debug("sending update '%s' to foreman" % payload)

            def runner():
                result = self.client.put(type, uuid, data=payload)
                self.log.debug("Response: %s" % result)

            # some changes (e.g. changing the hostgroup) trigger requests from foreman to gosa
            # so we need to run this request in a non blocking thread
            thread = Thread(target=runner)
            thread.start()
        else:
            self.log.info("skipping update request as the change is coming from the foreman backend")

    def is_uniq(self, attr, value, at_type):
        self.log.debug("is_uniq: %s, %s, %s" % (attr, value, at_type))
        return False

    def query(self, base, scope, params, fixed_rdn=None):
        self.log.debug("query: %s, %s, %s, %s" % (base, scope, params, fixed_rdn))
        return []

    def uuid2dn(self, uuid):  # pragma: nocover
        return None

    def dn2uuid(self, dn):  # pragma: nocover
        return None

    @staticmethod
    def extract_mapping(attrs):
        result = {}
        if 'mapping' in attrs:
            for key_value in attrs['mapping'].split(","):
                key, value = key_value.split(":")
                result[key] = value

        return result

    def __collect_data(self, data, params, type=None):
        # collect data
        if type is None:
            type = params["type"][:-1]
        payload = {
            type: {}
        }
        for name, settings in data.items():
            if len(settings["value"]):
                payload[type][name] = settings["value"][0]

        return payload


class ForemanClient(object):
    """Client for the Foreman REST-API v2"""
    headers = {'Accept': 'version=2,application/json', 'Content-type': 'application/json'}

    def __init__(self):
        self.env = Environment.getInstance()
        self.log = logging.getLogger(__name__)
        self.foreman_host = self.env.config.get("foreman.host")

    def __request(self, method_name, type, id=None, data=None):
        if self.foreman_host is None:
            return {}

        url = "%s/%s" % (self.foreman_host, type)
        if id is not None:
            url += "/%s" % id

        method = getattr(requests, method_name)
        data = dumps(data) if data is not None else None
        self.log.debug("sending %s request with %s to %s" % (method_name, data, url))
        response = method(url,
                          headers=self.headers,
                          verify=self.env.config.get("foreman.verify", "true") == "true",
                          auth=HTTPBasicAuth(self.env.config.get("foreman.user"), self.env.config.get("foreman.password")),
                          data=data)
        if response.ok:
            data = response.json()
            self.log.debug("response %s" % data)
            # check for error
            if "error" in data:
                raise ForemanObjectException(", ".join(data["error"]["errors"]))
            return data
        else:
            try:
                data = response.json()
            except json.decoder.JSONDecodeError as e:
                self.log.error("Error parsing json error response: %s (%s)" % (response.text, e))
                response.raise_for_status()
            else:
                # check for error
                if "error" in data and response.status_code != 404:
                    self.log.debug("Received response with error: %s" % data["error"])
                    raise ForemanObjectException(", ".join(data["error"]["errors"]) if "errors" in data["error"] else str(data["error"]))
                else:
                    response.raise_for_status()

    def check_backend(self):
        """ check if foreman backend is reachable """
        try:
            response = self.__request("get", "status")
            return response["result"] == "ok"
        except:
            return False

    def get(self, type, id=None):
        return self.__request("get", type, id=id)

    def delete(self, type, id):
        return self.__request("delete", type, id=id)

    def put(self, type, id, data):
        return self.__request("put", type, id=id, data=data)

    def post(self, type, id=None, data=None):
        return self.__request("post", type, id=id, data=data)


class ForemanObjectException(ObjectException):
    pass