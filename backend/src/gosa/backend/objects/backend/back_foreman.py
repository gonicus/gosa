# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.
from threading import Thread

import requests
from requests import HTTPError
from requests.auth import HTTPBasicAuth

from gosa.backend.objects.backend import ObjectBackend
from gosa.common import Environment
from logging import getLogger

from gosa.common.gjson import dumps


class Foreman(ObjectBackend):
    headers = {'Accept': 'version=2,application/json', 'Content-type': 'application/json'}
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
        self.foreman_host = self.env.config.get("foreman.host", "http://localhost/api")

    def __request(self, method_name, type, id=None, data=None):
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
            return data
        else:
            response.raise_for_status()

    def __get(self, type, id=None):
        return self.__request("get", type, id=id)

    def __delete(self, type, id):
        return self.__request("delete", type, id=id)

    def __put(self, type, id, data):
        return self.__request("put", type, id=id, data=data)

    def __post(self, type, id, data):
        return self.__request("post", type, id=id, data=data)

    def load(self, uuid, info, back_attrs=None):
        """
        Loading attribute values from foreman API

        :param uuid: Unique identifier in foreman (usually the id)
        :param info: dict of all object attributes that are related to foreman {<name>: <type>}
        :param back_attrs: backend configuration from object definition
        :return: results returned from foreman API
        """
        mapping = self.extract_mapping(back_attrs)
        try:
            data = self.__get(back_attrs['type'], id=uuid)
        except HTTPError as e:
            # something when wrong
            self.log.error("Error requesting foreman backend: %s" % e)
            data = {}

        res = {}
        # map attributes
        for source, target in mapping.items():
            if source in data and data[source] is not None:
                res[target] = [data[source]]

        # attach other requested attributes to result set
        for attr, type in info.items():
            if attr in data and data[attr] is not None:
                value = data[attr]
                if isinstance(value, int) and 'String' in type:
                    value = str(value)
                res[attr] = [value]

        return res

    def identify(self, dn, params, fixed_rdn=None):
        self.log.debug("FOREMAN### identify: %s, " % (dn, params, fixed_rdn))
        return False

    def identify_by_uuid(self, uuid, params):
        self.log.debug("FOREMAN### identify_by_uuid: %s, " % (uuid, params))
        return False

    def exists(self, misc):
        self.log.debug("FOREMAN### exists: %s" % misc)
        return False

    def remove(self, uuid, data, params):
        self.log.debug("FOREMAN### remove: %s, %s, %s" % (uuid, data, params))
        if Foreman.modifier != "foreman":
            self.__delete(params["type"], uuid)
        else:
            self.log.info("skipping deletion request as the change is coming from the foreman backend")
        return True

    def retract(self, uuid, data, params):
        self.log.debug("FOREMAN### retract: %s, %s, %s" % (uuid, data, params))
        pass

    def extend(self, uuid, data, params, foreign_keys):
        self.log.debug("FOREMAN### extend: %s, %s, %s, %s" % (uuid, data, params, foreign_keys))
        return None

    def move_extension(self, uuid, new_base):
        self.log.debug("FOREMAN### move_extension: %s, %s" % (uuid, new_base))
        pass

    def move(self, uuid, new_base):
        self.log.debug("FOREMAN### move: %s, %s" % (uuid, new_base))
        return True

    def create(self, base, data, params, foreign_keys=None):
        self.log.debug("FOREMAN### create: %s, %s, %s" % (base, data, params, foreign_keys))
        return None

    def update(self, uuid, data, params):
        self.log.debug("FOREMAN### update: '%s', '%s', '%s'" % (uuid, data, params))
        # collect data
        type = params["type"][:-1]
        payload = {
            type: {}
        }
        for name, settings in data.items():
            if len(settings["value"]):
                payload[type][name] = settings["value"][0]

        # finally send the update to foreman
        self.log.debug("sending update '%s' to foreman" % payload)

        def runner():
            result = self.__put(params["type"], uuid, data=payload)
            self.log.debug("Response: %s" % result)

        # some changes (e.g. changing the hostgroup) trigger requests from foreman to gosa
        # so we need to run this request in a non blocking thread
        thread = Thread(target=runner)
        thread.start()

    def is_uniq(self, attr, value):
        return False

    def query(self, base, scope, params, fixed_rdn=None):
        self.log.debug("FOREMAN### query: %s, %s, %s, %s" % (base, scope, params, fixed_rdn))
        return []

    def uuid2dn(self, uuid):  # pragma: nocover
        return None

    def dn2uuid(self, dn):  # pragma: nocover
        return None

    def extract_mapping(self, attrs):
        result = {}
        for key_value in attrs['mapping'].split(","):
            key, value = key_value.split(":")
            result[key] = value

        return result
