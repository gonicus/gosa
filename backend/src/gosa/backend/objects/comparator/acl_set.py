# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

from gosa.common.utils import N_
from gosa.common.components import PluginRegistry
from gosa.backend.objects.comparator import ElementComparator


class IsAclSet(ElementComparator):
    """
    Checks whether the given value is a valid AclSet.
    """

    def process(self, all_props, key, value):

        # Check each property value
        entry_cnt = 0
        errors = []

        ares = PluginRegistry.getInstance("ACLResolver")
        rolenames = [n["name"] for n in ares.getACLRoles(None) if "name" in n]

        for entry in value:
            entry_cnt += 1

            if not "priority" in entry:
                errors.append(dict(
                    index=entry_cnt,
                    detail=N_("missing '%(attribute)s' attribute"),
                    attribute="priority"
                    ))
                return False, errors

            if not "members" in entry:
                errors.append(dict(
                    index=entry_cnt,
                    detail=N_("missing '%(attribute)s' attribute"),
                    attribute="members"
                    ))
                return False, errors

            if "rolename" in entry:

                if "actions" in entry and entry["actions"]:
                    errors.append(dict(
                        index=entry_cnt,
                        detail=N_("rolename and actions cannot be used at the same time")
                        ))
                    return False, errors

                # If a 'rolename' is we do not allow other dict, keys
                if type(entry["rolename"]) not in [str, bytes]:
                    errors.append(dict(
                        index=entry_cnt,
                        detail=N_("'%(attribute)' needs to be of type '%(ttype)s' ('%(stype)s' found)"),
                        attribute="rolename",
                        ttype=str.__name__,
                        stype=type(entry["rolename"]).__name__
                        ))
                    return False, errors

                # Ensure that the given role exists....
                if not entry["rolename"] in rolenames:
                    errors.append(dict(
                        index=entry_cnt,
                        detail=N_("unknown role '%(role)s'"),
                        role=entry["rolename"]
                        ))
                    return False, errors

            else:

                if not "scope" in entry:
                    errors.append(dict(
                        index=entry_cnt,
                        detail=N_("missing '%(attribute)s' attribute"),
                        attribute="scope"
                        ))
                    return False, errors

                if not "actions" in entry:
                    errors.append(dict(
                        index=entry_cnt,
                        detail=N_("missing '%(attribute)s' attribute"),
                        attribute="actions"
                        ))
                    return False, errors

                for item in entry['actions']:

                    # Check  if the required keys 'topic' and 'acl' are present
                    if not "topic" in item:
                        errors.append(dict(index=entry_cnt, detail=N_("missing '%(attribute)s' attribute"), attribute="topic"))
                        return False, errors
                    if not "acl" in item:
                        errors.append(dict(index=entry_cnt, detail=N_("missing '%(attribute)s' attribute"), attribute="acl"))
                        return False, errors

                    # Check for the correct attribute types
                    if not type(item["topic"]) in [str, bytes]:
                        errors.append(dict(
                            index=entry_cnt,
                            detail=N_("'%(attribute)' needs to be of type '%(ttype)s' ('%(stype)s' found)"),
                            attribute="topic",
                            ttype=str.__name__,
                            stype=type(item["topic"]).__name__
                            ))
                        return False, errors
                    if not type(item["acl"]) in [str, bytes]:
                        errors.append(dict(
                            index=entry_cnt,
                            detail=N_("'%(attribute)' needs to be of type '%(ttype)s' ('%(stype)s' found)"),
                            attribute="acl",
                            ttype=str.__name__,
                            stype=type(item["acl"]).__name__
                            ))
                        return False, errors

                    # Check for a correct value for acls
                    if not all(map(lambda x: x in 'crowdsexm', item['acl'])):
                        errors.append(dict(
                            index=entry_cnt,
                            detail=N_("please use a combination of the charaters c, r, o, w, d, s, e, x and m")
                            ))
                        return False, errors

                    # Check if there are unsupported keys given
                    keys = list(item.keys())
                    keys.remove("topic")
                    keys.remove("acl")
                    if "options" in item:
                        keys.remove("options")
                    if len(keys):
                        errors.append(dict(
                            index=entry_cnt,
                            detail=N_("unknown attributes %(attributes)s"),
                            attributes=", ".join(keys)
                            ))
                        return False, errors

                    if "options" in item and not type(item["options"]) in [dict]:
                        errors.append(dict(
                            index=entry_cnt,
                            detail=N_("'%(attribute)' needs to be of type '%(ttype)s' ('%(stype)s' found)"),
                            attribute="options",
                            ttype=dict.__name__,
                            stype=type(item["options"]).__name__
                            ))
                        return False, errors

        return True, errors
