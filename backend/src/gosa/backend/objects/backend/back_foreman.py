# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.
import requests
from requests import HTTPError
from requests.auth import HTTPBasicAuth

from gosa.backend.objects.backend import ObjectBackend
from gosa.backend.plugins.foreman.main import ForemanException
from gosa.common.error import GosaErrorHandler as C
from gosa.common import Environment
from logging import getLogger


class Foreman(ObjectBackend):
    headers = {'Accept': 'version=2,application/json'}

    def __init__(self):
        # Initialize environment and logger
        self.env = Environment.getInstance()
        self.log = getLogger(__name__)
        self.foreman_host = self.env.config.get("foreman.host", "http://localhost/api")

    def __get(self, type, id=None):

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
        print("FOREMAN### identify: %s, " % (dn, params, fixed_rdn))
        return False

    def identify_by_uuid(self, uuid, params):
        print("FOREMAN### identify_by_uuid: %s, " % (uuid, params))
        return False

    def exists(self, misc):
        print("FOREMAN### exists: %s" % misc)
        return False

    def remove(self, uuid, data, params):
        return True

    def retract(self, uuid, data, params):
        pass

    def extend(self, uuid, data, params, foreign_keys):
        return None

    def move_extension(self, uuid, new_base):
        pass

    def move(self, uuid, new_base):
        return True

    def create(self, base, data, params, foreign_keys=None):
        return None

    def update(self, uuid, data, params):
        print("FOREMAN### update: '%s', '%s', '%s'" % (uuid, data, params))
        return True

    def is_uniq(self, attr, value):
        return False

    def query(self, base, scope, params, fixed_rdn=None):
        print("FOREMAN### query: %s, " % (base, scope, params, fixed_rdn))
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
