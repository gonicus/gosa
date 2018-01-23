# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

"""
This class implements the Json-Backend which is capable of storing GOsa objects.
"""

# -*- coding: utf-8 -*-
import os
import re
import uuid
import datetime
import ldap
from json import loads, dumps
from logging import getLogger
from gosa.common import Environment
from gosa.common.utils import is_uuid
from gosa.common.error import GosaErrorHandler as C
from gosa.backend.objects.backend import ObjectBackend
from gosa.backend.exceptions import DNGeneratorError, RDNNotSpecified, BackendError


class JSON(ObjectBackend):

    data = None
    scope_map = None

    def __init__(self):

        # Initialize environment and logger
        self.env = Environment.getInstance()
        self.log = getLogger(__name__)

        # Create scope map
        self.scope_map = {ldap.SCOPE_SUBTREE: "sub", ldap.SCOPE_BASE: "base", ldap.SCOPE_ONELEVEL: "one"}

        # Read storage path from config
        self._file_path = self.env.config.get("backend-json.database-file", None)
        if not self._file_path:
            raise BackendError(C.make_error("DB_CONFIG_MISSING", target="backend-json.database-file"))

        # Create a json file on demand
        if not os.path.exists(self._file_path):
            open(self._file_path, "w").write(dumps({}))

    def __load(self):
        """
        Loads the json file and returns a object
        """
        return loads(open(self._file_path).read())

    def __save(self, json):
        """
        Saves back the given object to the json file.
        """
        open(self._file_path, "w").write(dumps(json, indent=2))

    def load(self, item_uuid, info, back_attrs=None, needed=None):
        """
        Load object properties for the given uuid
        """
        json = self.__load()
        data = {}
        if item_uuid in json:
            for obj in json[item_uuid]:
                data.update(json[item_uuid][obj].items())
        return data

    def identify(self, object_dn, params, fixed_rdn=None):
        """
        Identify an object by dn
        """
        item_uuid = self.dn2uuid(object_dn)
        if not item_uuid:
            return False

        res = self.identify_by_uuid(item_uuid, params)
        return res

    def identify_by_uuid(self, item_uuid, params):
        """
        Identify an object by uuid
        """

        json = self.__load()
        if item_uuid in json:
            for obj in json[item_uuid]:
                if json[item_uuid][obj]['type'] == params['type']:
                    return True

        return False

    def retract(self, item_uuid, data, params, needed=None, user=None):
        """
        Remove an object extension
        """
        json = self.__load()
        if item_uuid in json and params['type'] in json[item_uuid]:
            del(json[item_uuid][params['type']])
        self.__save(json)

    def extend(self, item_uuid, data, params, foreign_keys, dn=None, needed=None, user=None):
        """
        Create an object extension
        """
        json = self.__load()
        if not item_uuid in json:
            json[item_uuid] = {}
        json[item_uuid][params['type']] = {'type': params['type']}
        for item in data:
            json[item_uuid][params['type']][item] = data[item]['value']
        self.__save(json)

    def dn2uuid(self, object_dn):
        """
        Tries to identify the given dn in the json-database, if an
        entry with the given dn was found, its uuid is returned.
        """
        json = self.__load()
        for uuid in json:
            for obj in json[uuid]:
                if 'dn' in json[uuid][obj] and object_dn == json[uuid][obj]['dn']:
                    return uuid
        return None

    def uuid2dn(self, item_uuid):
        """
        Tries to find the given uuid in the backend and returnd the
        dn for the entry.
        """
        json = self.__load()
        if item_uuid in json:
            for obj in json[item_uuid]:
                if "dn" in json[item_uuid][obj]:
                    return json[item_uuid][obj]["dn"]
        return None

    def query(self, base, scope, params, fixed_rdn=None):
        """
        Queries the json-database for the given objects
        """

        # Load json database
        json = self.__load()

        # Search for the given criteria.
        # For one-level scope the parentDN must be equal with the reqeusted base.
        found = []
        if self.scope_map[scope] == "one":
            for uuid in json:
                for obj in json[uuid]:
                    if "parentDN" in json[uuid][obj] and json[uuid][obj]['parentDN'] == base:
                        found.append(json[uuid][obj]['dn'])

        # For base searches the base has the dn has to match the requested base
        if self.scope_map[scope] == "base":
            for uuid in json:
                for obj in json[uuid]:
                    if "dn" in json[uuid][obj] and json[uuid][obj]['dn'] == base:
                        found.append(json[uuid][obj]['dn'])

        # For sub-queries the requested-base has to be part parentDN
        if self.scope_map[scope] == "sub":
            for uuid in json:
                for obj in json[uuid]:
                    if "parentDN" in json[uuid][obj] and re.search(re.escape(base) + "$", json[uuid][obj]['parentDN']):
                        found.append(json[uuid][obj]['dn'])
        return found

    def create(self, base, data, params, foreign_keys=None, needed=None, user=None):
        """
        Creates a new database entry
        """

        # All entries require a naming attribute, if it's not available we cannot generate a dn for the entry
        if not 'rdn' in params:
            raise RDNNotSpecified(C.make_error("RDN_NOT_SPECIFIED"))

        # Split given rdn-attributes into a list.
        rdns = [d.strip() for d in params['rdn'].split(",")]

        # Get FixedRDN attribute
        FixedRDN = params['FixedRDN'] if 'FixedRDN' in params else None

        # Get a unique dn for this entry, if there was no free dn left (None) throw an error
        object_dn = self.get_uniq_dn(rdns, base, data, FixedRDN)
        if not object_dn:
            raise DNGeneratorError(C.make_error("NO_UNIQUE_DN", base=base, rdns=", ".join(rdns)))

        # Build the entry that will be written to the json-database
        json = self.__load()
        str_uuid = str(uuid.uuid1())
        obj = {'dn': object_dn, 'type': params['type'], 'parentDN': base,
               'modifyTimestamp': datetime.datetime.now().isoformat(),
               'createTimestamp': datetime.datetime.now().isoformat()}
        for attr in data:
            obj[attr] = data[attr]['value']

        # Append the entry to the databse and save the changes
        if not str_uuid in json:
            json[str_uuid] = {}
        json[str_uuid][params['type']] = obj
        self.__save(json)

        # Return the uuid of the generated entry
        return str_uuid

    def get_timestamps(self, object_dn):
        """
        Returns the create- and modify-timestamps for the given dn
        """
        ctime = mtime = 0
        json = self.__load()
        item_uuid = self.dn2uuid(object_dn)

        if item_uuid in json:
            for obj in json[item_uuid]:
                if 'createTimestamp' in json[item_uuid][obj]:
                    ctime = datetime.datetime.strptime(json[item_uuid][obj]['createTimestamp'], "%Y-%m-%dT%H:%M:%S.%f")
                if 'modifyTimestamp' in json[item_uuid][obj]:
                    mtime = datetime.datetime.strptime(json[item_uuid][obj]['modifyTimestamp'], "%Y-%m-%dT%H:%M:%S.%f")

        return ctime, mtime

    def get_uniq_dn(self, rdns, base, data, FixedRDN, needed=None):
        """
        Tries to find an unused dn for the given properties
        """

        # Get all DNs
        json = self.__load()
        dns = []
        for uuid in json:
            for obj in json[uuid]:
                if "dn" in json[uuid][obj]:
                    dns.append(json[uuid][obj]["dn"])

        # Check if there is still a free dn left
        for object_dn in self.build_dn_list(rdns, base, data, FixedRDN):
            if object_dn not in dns:
                return object_dn

        return None

    def remove(self, item_uuid, data, params, needed=None, user=None):
        """
        Removes the entry with the given uuid from the database
        """
        json = self.__load()
        if item_uuid in json:
            del(json[item_uuid])
            self.__save(json)
            return True
        return False

    def exists(self, misc, needed=None):
        """
        Check whether the given uuid or dn exists
        """
        json = self.__load()
        if is_uuid(misc):
            return misc in json['objects']
        else:
            for uuid in json:
                for obj in json[uuid]:
                    if "dn" in json[uuid][obj] and json[uuid][obj]["dn"] == misc:
                        return True

        return False

    def is_uniq(self, attr, value, at_type, needed=None):
        """
        Check whether the given attribute is not used yet.
        """

        #TODO: Include extensions!!
        json = self.__load()
        for uuid in json:
            for obj in json[uuid]:
                if attr in json[uuid][obj] and json[uuid][obj][attr] == value:
                    return False
        return True

    def update(self, item_uuid, data, params, dn=None, needed=None, user=None):
        """
        Update the given entry (by uuid) with a new set of values.
        """
        o_type = params['type']
        json = self.__load()
        if not item_uuid in json:
            json[item_uuid] = {}
        if not o_type in json[item_uuid]:
            json[item_uuid][o_type] = {}
            json[item_uuid][o_type]['type'] = o_type

        for item in data:
            json[item_uuid][o_type][item] = data[item]['value']

        self.__save(json)
        return True

    def move_extension(self, item_uuid, new_base):
        """
        Moves the extension to a new base
        """
        # Nothing to do here.
        return True

    def move(self, item_uuid, new_base, needed=None, user=None):
        """
        Moves an entry to another base
        """
        json = self.__load()
        if item_uuid in json:
            for obj in json[item_uuid]:
                if "dn" in json[item_uuid][obj]:

                    # Update the source entry
                    entry = json[item_uuid][obj]
                    entry['dn'] = re.sub(re.escape(entry['parentDN']) + "$", new_base, entry['dn'])
                    entry['parentDN'] = new_base

                    # Check if we can move the entry
                    if self.exists(entry['dn']):
                        raise BackendError(C.make_error("TARGET_EXISTS", target=entry['dn']))

                    # Save the changes
                    json[item_uuid][obj] = entry
                    self.__save(json)
                    return True
        return False
