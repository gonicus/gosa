# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

import re

import copy

from gosa.backend.objects import ObjectFactory
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
        factory = ObjectFactory.getInstance()
        query = {attribute: ""}
        if factory.isBaseType(objectType):
            query["_type"] = objectType
        else:
            query["extension"] = objectType

        for val in value:
            if val in all_props[key]['value']:
                # do not check existing values
                continue
            if attribute == "dn" and val in [x.dn for x in index.currently_in_creation]:
                # this object has been created but is not in the DB yet
                continue

            query[attribute] = val
            if not len(index.search(query, {'dn': 1})):
                errors.append(dict(index=value.index(val),
                                   detail=N_("no '%(type)s' object with '%(attribute)s' property matching '%(value)s' found"),
                                   type=objectType,
                                   attribute=attribute,
                                   value=val))

        return len(errors) == 0, errors


class MaxAllowedTypes(ElementComparator):
    """
    Validates the maximum number of allowed base types in a list if DNs.
    """

    def process(self, all_props, key, value, max_types):

        errors = []
        res = self.__get_types(value)

        if len(res) > int(max_types):
            errors.append(dict(index=0,
                               detail=N_("Too many types '%(types)s'. Only '%(allowed)s' types allowed."),
                               allowed=max_types,
                               types=res))

        return len(errors) == 0, errors

    def get_gui_information(self, all_props, key, value, max_types):
        return {"MaxAllowedTypes": {"key": "_type", "maximum": int(max_types)}}

    def __get_types(self, value):
        index = PluginRegistry.getInstance("ObjectIndex")
        res = set()
        for r in index.search({'dn': {'in_': value}}, {'_type': 1, 'dn': 1}):
            res.add(r["_type"])
        return res


class HasMemberOfType(ElementComparator):
    """
    Checks if a member of a certain ``type`` existing in the value list of attribute ``attribute``

    Can be used e.g. as extension condition to allow an extension only if a certain type is member of a *GroupOfNames*

    .. code-block::

            <ExtensionCondition extension="GroupOfNames">
                <Condition>
                    <Name>HasMemberOfType</Name>
                    <Param>PosixUser</Param>
                    <Param>member</Param>
                    <Param>dn</Param>
                </Condition>
            </ExtensionCondition>

    """

    def process(self, all_props, key, value, type, attribute, attribute_content):
        errors = []

        if key == "extension":
            # extension validation mode, use value from props
            value = all_props[attribute]["value"]
        if len(value) == 0:
            errors.append(dict(index=0,
                               detail=N_("Object has no member of type '%(type)s'."),
                               type=type))
        else:
            index = PluginRegistry.getInstance("ObjectIndex")
            query = {attribute_content: {"in_": value}}
            if ObjectFactory.getInstance().isBaseType(type):
                query["_type"] = type
            else:
                query["extension"] = type
            res = index.search(query, {"dn": 1})
            if len(res) > 0:
                return len(errors) == 0, errors

            if len(index.currently_in_creation) > 0:
                # check if the referenced object we are looking for is currently being created
                found_types = [x.__class__.__name__ for x in index.currently_in_creation if getattr(x, attribute_content) in value]
                if type in found_types:
                    return True, errors

            if self.traverse_groups(value, type, attribute, attribute_content):
                # found type in subgroup member
                return True, errors

            errors.append(dict(index=0,
                               detail=N_("Object has no member of type '%(type)s'."),
                               type=type))

        return len(errors) == 0, errors

    def get_gui_information(self, all_props, key, value, type, attribute, attribute_content):
        return {"HasMemberOfType": {"listenToProperty": attribute, "type": type, "propertyContent": attribute_content}}

    def traverse_groups(self, value, type, attribute, attribute_content, group_type="GroupOfNames"):
        """ do a BFS search in sub-groups for object type """
        index = PluginRegistry.getInstance("ObjectIndex")
        # check if the type can by found in a group
        res = index.search({"_type": group_type, attribute_content: {"in_": value}},
                           {attribute: 1})
        sub_values = [x[attribute] for x in res]
        res = []
        if len(sub_values):
            query = {attribute_content: {"in_": sub_values}}
            if ObjectFactory.getInstance().isBaseType(type):
                query["_type"] = type
            else:
                query["extension"] = type
            res = index.search(query, {"dn": 1})

        if len(res) == 0 and len(sub_values):
            return self.traverse_groups(sub_values, type, attribute, attribute_content, group_type)
        else:
            return True


class CheckExtensionConditions(ElementComparator):
    """ check if all conditions of active extensions of an object are still valid """

    def process(self, all_props, key, value, object):
        errors = []

        # special case for own dn in member -> skip validation
        if key == "member" and object.dn in value:
            return True, errors

        # collect all conditions that are related to this attribute key and whose extension is active
        conditions = [(name, x) for name, x in object.extension_conditions.items()
                      if key in x["properties"] and object.parent.is_extended_by(name)]

        props_copy = copy.deepcopy(object.myProperties)
        for extension_name, condition in conditions:
            res, errs = object.processValidator(condition, key, value, props_copy)
            if not res:
                errors.append(dict(code='OBJECT_EXTENSION_NOT_ALLOWED',
                                   detail=N_("Object is extended by '%(extension)s', which is not allowed. Reason: '%(error)s'"),
                                   extension=extension_name,
                                   error=", ".join([x["detail"] % x for x in errs])))

        return len(errors) == 0, errors
