# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

import re
from gosa.common.components import PluginRegistry
from gosa.common.utils import N_
from gosa.backend.objects.comparator import ElementComparator


class IsValidHostName(ElementComparator):
    """
    Validates a given host name.
    """

    def process(self, all_props, key, value):

        errors = []

        for hostname in value:
            if not re.match("^(([a-zA-Z]|[a-zA-Z][a-zA-Z0-9\-]*[a-zA-Z0-9])\.)*([A-Za-z]|[A-Za-z][A-Za-z0-9\-]*[A-Za-z0-9])$", hostname):
                errors.append(dict(index=value.index(hostname),
                    detail=N_("invalid hostname '%(hostname)s'"),
                    hostname=hostname))

        return len(errors) == 0, errors


class IsExistingDN(ElementComparator):
    """
    Check if the given DN exists.
    """

    def process(self, all_props, key, value):

        errors = []
        index = PluginRegistry.getInstance("ObjectIndex")
        for dn in value:
            # do not check dn's that are currently being moved to
            if index.is_currently_moving(dn, move_target=True):
                continue

            if dn in all_props[key]['value']:
                # do not check existing values
                continue
            if not len(index.search({'dn': dn}, {'dn': 1})):
                errors.append(dict(index=value.index(dn),
                    detail=N_("DN '%(dn)s' does not exist"),
                    dn=dn))

        return len(errors) == 0, errors


class IsExistingDnOfType(ElementComparator):
    """
    Validates a given domain name.
    """

    def process(self, all_props, key, value, objectType):

        errors = []
        index = PluginRegistry.getInstance("ObjectIndex")
        for dn in value:
            if not len(index.search({'_type': objectType, 'dn': dn}, {'dn': 1})):
                errors.append(dict(index=value.index(dn),
                    detail=N_("DN '%(dn)s' does not exist"),
                    dn=dn))

        return len(errors) == 0, errors


class ObjectWithPropertyExists(ElementComparator):
    """
    Checks if an object with the given property exists.
    """

    def process(self, all_props, key, value, objectType, attribute, comp=None):
        errors = []
        index = PluginRegistry.getInstance("ObjectIndex")
        for val in value:
            if attribute == "dn" and val in index.currently_in_creation:
                # this object has been created but is not in the DB yet
                continue

            query = {'or_': {'_type': objectType, 'extension': objectType}, attribute: val}
            if not len(index.search(query, {'dn': 1})):
                query = {'_type': objectType, attribute: val}
                if not len(index.search(query, {'dn': 1})):
                    errors.append(dict(index=value.index(val),
                        detail=N_("no '%(type)s' object with '%(attribute)s' property matching '%(value)s' found"),
                        type=objectType,
                        attribute=attribute,
                        value=val))

        return len(errors) == 0, errors
