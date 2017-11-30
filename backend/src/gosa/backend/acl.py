# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

"""
.. _gosa-acl:

ACL management
==============

This chapter details the way access control is handled within the GOsa core
engine.

How an ACL assignment could look like
-------------------------------------

::

    ACLRole (test1)
     |-> ACLRoleEntry
     |-> ACLRoleEntry
    
    ACLSet
     |-> ACL
     |-> ACL
     |-> ACL -> ACLRole (test1)
     |-> ACL

--------

@startuml
namespace gosa.backend.acl #DDDDDD {
    class ACLSet <<list>>
    class ACLRole <<list>>
    class ACL <<object>>
    class ACLRoleEntry <<ACL>>

    ACLSet "1" -- "0..n" ACL : contains
    ACL "1" -- "0..1" ACLRole : contains
    ACL  <|-- ACLRoleEntry
    ACLRole "1" -- "0..n" ACLRoleEntry : contains

    gosa.common.components.Plugin <|-- ACLResolver
    gosa.common.handler.IInterfaceHandler <|-- ACLResolver

    ACLResolver "1" o-- "0..n" ACLSet
    ACLResolver "1" o-- "0..n" ACLRole
}

namespace gosa.common.components {
    class Plugin
}

namespace gosa.common.handler {
    interface IInterfaceHandler
}
@enduml
"""
import re
import ldap
import logging
import zope.event

from zope.interface import implementer

from gosa.common.env import SessionMixin
from gosa.common.handler import IInterfaceHandler
from gosa.common import Environment
from gosa.common.components import Command, Plugin
from gosa.common.utils import N_
from gosa.common.error import GosaErrorHandler as C
from gosa.common.components import PluginRegistry
from gosa.backend.objects.object import ObjectChanged
from gosa.backend.objects.proxy import ObjectProxy
from gosa.backend.objects.index import ObjectInfoIndex, KeyValueIndex
from gosa.backend.exceptions import ACLException
from sqlalchemy import and_, or_


#TODO: Think about ldap relations, how to store and load objects.
#TODO: What about object groups, to be able to inlcude clients?
#TODO: Groups are not supported yet


C.register_codes(dict(
    ACL_NOT_FOUND=N_("ACL not found"),
    ACL_ITEM_INVALID_TYPE=N_("Item is not of type '%(type)s'"),
    ACL_INVALID_SCOPE=N_("Invalid ACL scope '%(scope)s'"),
    ROLE_NOT_FOUND=N_("Role '%(role)s' not found"),
    ACL_INVALID_SCOPE_TARGET=N_("Cannot set scope for role ACLs"),
    ACL_TYPE_MISMATCH=N_("ACL and Role objects are not combinable"),
    ACL_STRING_INVALID=N_("Invalid permission map - combination of the characters c, r, o, w, d, s, e, x and m expected"),
    ENTRY_NOT_UNIQUE=N_("Entry %(dn)s is not unique"),
    ACL_LOOP=N_("Recursion in ACL resolution for role '%(role)s'"),
    ROLE_DIRECT_MEMBER=N_("Role ACLs do not support members"),
    ROLE_UNRESOLVED_REFERENCES=N_("Unresolved role references: %(references)s"),
    ACL_NO_BASE_ACL=N_("No base ACL definition for '%(base)s' found"),
    ACL_NOT_FOUND_ON_BASE=N_("No ACL definition for '%(base)s' found"),
    ROLE_IN_USE=N_("Role '%(role)s' is still in use"),
    ACL_PRIORITY_INVALID=N_("Priority needs to be above -100 and below 100"),
    ACL_MISSING_KEY=N_("Action '%(action)s' lacks a '%(key)s' key"),
    ACL_PARAMETER_MISMATCH=N_("Action and role name parameter cannot be used at the same time"),
    PERMISSION_UPDATE=N_("No permission to modify '%(target)s'"),
    ROLE_EXISTS=N_("Role '%(name)s' already exists"),
    ROLE_CANNOT_POINT_TO_ITSELF=N_("Roles cannot point to themselves"),
    ACL_EVENT_BLOCKED=N_("No permission to send event '%(target)s'"),
    ACL_BASE_ERROR=N_("No way to find a matching base"),
    ))


class ACLSet(list):
    """
    The base class of all ACL assignments is the 'ACLSet' class which
    combines a list of ``ACL`` entries into a set of effective ACLs.

    The ACLSet has a base property which specifies the base, this set of
    acls, is valid for. E.g. dc=example,dc=net

    ============== =============
    Key            Description
    ============== =============
    base           The base this ACLSet is created for.
    ============== =============

    >>> # Create an ACLSet for base 'dc=example,dc=net'
    >>> # (if you do not pass the base, the default of your ldap setup will be used)
    >>> aclset = ACLSet('dc=example,dc=net')
    >>> resolver = ACLResolver()
    >>> resolver.add_acl_set(aclset)
    """
    base = None

    def __init__(self, base=None):
        super(ACLSet, self).__init__()
        self.env = Environment.getInstance()
        self.log = logging.getLogger(__name__)

        # If no base is given use the default one.
        self.base = base or self.env.base

    def get_base(self):
        """
        Returns the base for this ACLSet.
        """
        return self.base

    def remove_acls_for_user(self, user):
        """
        Removes all permission for the given user form this ACLSet.

        ============== =============
        Key            Description
        ============== =============
        user           The username to remove acls for.
        ============== =============

        Example::

            aclset = ACLSet()
            acl = ACL(scope=ACL.ONE)
            acl.set_members([u'tester1', u'tester2'])

            # "[^\.]*" means everything one level
            acl.add_action('^org\.gosa\.event\.[^\.]*$', 'rwx')
            acl.set_priority(100)
            aclset.add(acl)

            aclset.remove_acls_for_user('tester1')

            ...

        """
        for acl in self:
            if user in acl.members:
                acl.members.remove(user)

    def remove_acl(self, acl):
        """
        Removes an acl entry fromt this ACLSet.

        ============== =============
        Key            Description
        ============== =============
        acl            The ACL object to remove.
        ============== =============

        Example::

            aclset = ACLSet()
            acl = ACL(scope=ACL.ONE)
            acl.set_members([u'tester1', u'tester2'])
            acl.add_action('^org\.gosa\.event\.ClientLeave$', 'rwx')
            acl.set_priority(100)
            aclset.add(acl)

            aclset.remove_acl(acl)

        """
        for cur_acl in self:
            if cur_acl == acl:
                self.remove(acl)
                return

        # Raise an exception about the unknown ID
        raise ACLException(C.make_error("ACL_NOT_FOUND"))

    def add(self, item):
        """
        Adds a new ``ACL`` object to this ``ACLSet``.

        ============== =============
        Key            Description
        ============== =============
        acl            The ACL object to add.
        ============== =============

        Example::

            aclset = ACLSet()
            acl = ACL(scope=ACL.ONE)
            acl.set_members([u'tester1', u'tester2'])
            acl.add_action('^org\.gosa\.event\.ClientLeave$', 'rwx')
            acl.set_priority(100)

            aclset.add(acl)

        """
        if type(item) != ACL:
            raise TypeError(C.make_error('ACL_ITEM_INVALID_TYPE', type=ACL.__name__))

        if item.priority is None:
            item.priority = len(self)

        self.append(item)

        # Sort Acl items by id
        self.sort(key=lambda item: (item.priority * 1))
        PluginRegistry.getInstance("ACLResolver").check.cache_clear()

    def __str__(self):
        return self.repr_self()

    def repr_self(self, indent=0):
        """
        Create a human readable representation of this ACLSet object.
        """

        # Only draw to a maximum level of 20 sub entries
        if indent > 20:
            return " " * indent + "...\n"

        # Build a human readable representation of this aclset and its children.
        rstr = "%s<ACLSet: %s>" % (" " * indent, self.base)
        for entry in self:
            rstr += entry.repr_self(indent + 1)

        return rstr


class ACLRole(list):
    """
    This is a container for ``ACLRoleEntries`` entries that should act like a role.
    An ``ACLRole`` has a name which can be used in ``ACL`` objects to use the role.

    ============== =============
    Key            Description
    ============== =============
    name           The name of the role we want to create.
    ============== =============

    This class equals the ``ACLSet`` class, but in details it does not have a base, instead
    it has name. This name can be used later in 'ACL' classes to refer to
    this acl role.

    And instead of ``ACL-objects`` it uses ``ACLRoleEntry-objects`` to assemble
    a set of acls::

        >>> # Create an ACLRole object
        >>> aclrole = ACLRole('role1')
        >>> acl = ACLRoleEntry(scope=ACL.SUB)
        >>> acl.add_action(...)
        >>> aclrole.add(acl)

        >>> # Now add the role to the resolver
        >>> resolver = ACLResolver()
        >>> resolver.add_acl_set(aclrole)

        >>> # You can use this role like this in ACL entries of an ACLset:
        >>> aclset = ACLSet()
        >>> acl = ACL(role=aclrole)
        >>> aclset.add(acl)
        >>> resolver.add_acl_set(aclset)

    Or you can use this role within another role like this::

        >>> # Create an ACLRole object
        >>> aclrole1 = ACLRole('role1')
        >>> acl = ACLRoleEntry(scope=ACL.SUB)
        >>> acl.add_action(...)
        >>> aclrole1.add(acl)

        >>> # Now add the role to the resolver
        >>> resolver = ACLResolver()
        >>> resolver.add_acl_set(aclrole1)

        >>> # Create antoher role which refers to role1
        >>> aclrole2 = ACLRole('role2')
        >>> acl = ACLRoleEntry(role=role1)
        >>> aclrole2.add(acl)
        >>> resolver = ACLResolver()
        >>> resolver.add_acl_set(aclrole2)

        >>> # Now use the role2 in an ACL definition. (Role2 point to Role1 now.)
        >>> aclset = ACLSet()
        >>> acl = ACL(role=aclrole2)
        >>> aclset.add(acl)
        >>> resolver.add_acl_set(aclset)
    """
    name = None
    dn = None
    priority = None

    def __init__(self, name, dn=None):
        super(ACLRole, self).__init__()
        self.log = logging.getLogger(__name__)
        self.name = name
        self.dn = dn

    def add(self, item):
        """
        Add a new ``ACLRoleEntry`` object to this ``ACLRole``.

        ============== =============
        Key            Description
        ============== =============
        item           The ``ACLRoleEntry`` item to add to this role.
        ============== =============

        Example::

            # Create an ACLRole
            role = ACLRole('role1')
            acl = ACLRoleEntry(scope=ACL.ONE)
            acl.add_action('^org\.gosa\.event\.ClientLeave$', 'rwx')

            role.add(acl)

        """
        if type(item) != ACLRoleEntry:
            raise TypeError(C.make_error('ACL_ITEM_INVALID_TYPE', type=ACLRoleEntry.__name__))

        # Create an item priority if it does not exists.
        if item.priority is None:
            item.priority = len(self)

        self.append(item)

        # Sort Acl items by id
        self.sort(key=lambda item: (item.priority * -1))

    def get_name(self):
        """
        Returns the name of the role.
        """
        return self.name

    def __str__(self):
        return self.repr_self()

    def repr_self(self, indent=0):
        """
        Create a human readable reprentation of this ACLRole object.
        """

        # Only draw to a maximum level of 20 sub entries
        if indent > 20:
            return " " * indent + "...\n"

        # Build a human readable representation of this role and its children.
        rstr = "%s<ACLRole: %s>" % (" " * indent, self.name)
        for entry in self:
            rstr += entry.repr_self(indent + 1)

        return rstr


class ACL(object):
    """
    The ``ACL`` object describes a set of actions that can be accessed in a given scope.
    ``ACL`` classes can then be bundled in ``ACLSet`` objects and attached to base.

    ============== =============
    Key            Description
    ============== =============
    scope          The scope this acl is valid for.
    role           You can either define permission actions directly or you can use an ``ACLRole`` instead
    ============== =============

    .. _scope_description:

    Scope values - internal use:

        * ``ACL.ONE`` for one level.
        * ``ACL.SUB`` for all sub-level. This can be revoked using ``ACL.RESET``
        * ``ACL.RESET`` revokes the actions described in this ``ACL`` object for all sub-levels of the tree.
        * ``ACL.PSUB`` for all sub-level, cannot be revoked using ``ACL.RESET``

    Scope values - external use, e.g. when executing commands using the gosa-cli:

        * ``"one"`` for one level.
        * ``"sub"`` for all sub-level. This can be revoked using ``ACL.RESET``
        * ``"reset"`` revokes the actions described in this ``ACL`` object for all sub-levels of the tree.
        * ``"psub"`` for all sub-level, cannot be revoked using ``ACL.RESET``

    The ACL class contains list of actions for a set of members.
    These ACL classes can then be bundled and attached to a base base using
    the ``ACLSet`` class.

    ======== ================
    Type     Description
    ======== ================
    Scope    The scope specifies where the ACL is valid for, e.g. ONE-level, all SUB-levels or RESET previous ACLs
    Members  A list of users this acl is valid for.
    Role     Instead of actions you can also refer to a ACLRole object.
    Actions  You can have multiple actions, where one action is described by ``a topic``, a ``set of acls`` and additional ``options`` that have to be checked while ACLs are resolved.
    ======== ================

        >>> # Create an ACLSet object
        >>> aclset = ACLSet()

        >>> # Create an ACL object and attach it to the ACLSet
        >>> acl = ACL()
        >>> acl.set_priority(0)
        >>> acl.set_members([u"user1", u"user2"])
        >>> acl.add_action('^org\.gosa\.event\.ClientLeave$', 'rwx')
        >>> aclset.add(acl)

        >>> # Now add the set to the resolver
        >>> resolver = ACLResolver()
        >>> resolver.add_acl_set(aclset)

        >>> # You can now check for acls, both should return True now.
        >>> resolver.check('user1', 'org.gosa.event.ClientLeave', 'r')
        >>> resolver.check('user1', 'org.gosa.event.ClientLeave', 'rwx')

    ACL members can also contain regular expressions, like this:

        >>> acl.set_members([u"user1", u"^user[0-9]*$"])
        >>> ...
        >>> resolver.check('user45', 'org.gosa.event.ClientLeave', 'r')

    """
    priority = None

    ONE = 1
    SUB = 2
    PSUB = 3
    RESET = 4

    members = None
    actions = None
    scope = None
    uses_role = False
    role = None

    id = None

    def __init__(self, scope=SUB, role=None):
        self.env = Environment.getInstance()
        self.log = logging.getLogger(__name__)

        self.actions = []
        self.members = []

        r = PluginRegistry.getInstance("ACLResolver")
        self.id = r.get_next_acl_id()

        # Is this a role base or manually configured ACL object.
        if role:
            self.use_role(role)
        else:

            if scope not in (ACL.ONE, ACL.SUB, ACL.PSUB, ACL.RESET):
                raise TypeError(C.make_error("ACL_INVALID_SCOPE", scope=scope))

            self.set_scope(scope)

    def use_role(self, rolename):
        """
        Mark this ACL to use a role instead of direct permission settings.

        ============== =============
        Key            Description
        ============== =============
        rolename       The name of the role to use.
        ============== =============

        """
        if not isinstance(rolename, str):
            raise ACLException(C.make_error("ATTRIBUTE_INVALID", "rolename", type=str.__name__))

        r = PluginRegistry.getInstance("ACLResolver")
        if rolename in r.acl_roles:
            self.uses_role = True
            self.role = rolename
        else:
            raise ACLException(C.make_error("ROLE_NOT_FOUND", role=rolename))

    def set_scope(self, scope):
        """
        This methods updates the ACLs scope level.

        See :class:`gosa.backend.acl.ACL` for details on the scope-levels.

        ============== =============
        Key            Description
        ============== =============
        scope          The new scope value for this ACl.
        ============== =============
        """

        if scope not in [ACL.ONE, ACL.SUB, ACL.PSUB, ACL.RESET]:
            raise TypeError(C.make_error("ACL_INVALID_SCOPE", scope=scope))

        if self.uses_role:
            raise ACLException(C.make_error("ACL_INVALID_SCOPE_TARGET"))

        self.scope = scope

    def set_priority(self, priority):
        """
        Sets the priority of this ACL object. Lower values mean higher priority.

        If no priority is given, a priority of 0 will be used when this ACL gets added to an ACLSet, the next will get 1, then 2 aso.

        ============== =============
        Key            Description
        ============== =============
        priority       The new priority value for this ACl.
        ============== =============

        Example::

            aclset = ACLSet()
            acl = ACL(scope=ACL.ONE)
            acl.set_members([u'tester1', u'tester2'])
            acl.add_action('^org\.gosa\.event\.ClientLeave$', 'rwx')

            acl.set_priority(100)

        """
        self.priority = priority

    def set_members(self, members):
        """
        Set the members for this acl

        ============== =============
        Key            Description
        ============== =============
        members        A list of user names
        ============== =============

        Example::

            aclset = ACLSet()
            acl = ACL(scope=ACL.ONE)

            acl.set_members([u'peter', u'klaus'])

        """
        if type(members) != list:
            raise ACLException(C.make_error("ATTRIBUTE_INVALID", "members", type=list.__name__))

        self.members = members

    def clear_actions(self):
        """
        This method removes all defined actions from this acl.
        """
        self.role = None
        self.uses_role = False
        self.actions = []

    def add_action(self, topic, acls, options=None):
        """
        Adds a new action to this ACL object.

        ============== =============
        Key            Description
        ============== =============
        topic          The topic action we want to create ACLs for. E.g. 'org.gosa.factory.Person'
        acls           The acls this action contain. E.g. 'rwcdm'.
        options        Special additional options that have to be checked.
        ============== =============

        .. _topic_description:

        **Topic**

        Topics are defined as regular expressions, which gives a huge flexibility.

        For example ``^gosa\.[^\.]*\.factory$`` would match for:
         * gosa.test.factory
         * gosa.hallo.factory
        but not for:
         * gosa.factory
         * gosa.level1.level2.factory

        Where ``^gosa\..*\.factory$`` matches for:
         * gosa.factory
         * gosa.level1.factory
         * gosa.level1.level2.factory

        .. _acls_description:

        **Acls**

        The acls paramter describes the action we can perform on a given ``topic``.
        Possible actions are:

         * r - Read
         * w - Write
         * c - Create
         * d - Delete
         * o - Owner only, this acl affects only logged in user itself.
         * m - Manager, this acl applies for the manager of on object.
         * s - Search - or being found
         * x - Execute
         * e - Receive event

        The actions have to passed as a string, which contains all actions at once::
            >>> add_action(repr('topic'), "rwcdm", repr('options'))

        .. _options_description:

        **Options**

        Options are additional check parameters that have to be fulfilled to get this acl to match.

        The ``options`` parameter is a dictionary which contains a key and a value for each additional option we want to check for, e.g. ::
            >>> add_action('topic', 'acls', {'uid': 'hanspeter', 'ou': 'technik'})

        If you've got a user object (``user1``) as dictionary, then you can check permissions like this::
            >>> resolver.check('some.topic', 'rwcdm', user1)

        The resolver will then check if the keys ``uid`` and ``ou`` are present in the user1 dictionary and then check if the values match.
        If not all options match, the ACL will not match.

        """

        if options and type(options) != dict:
            raise ACLException(C.make_error("ATTRIBUTE_INVALID", "options", type=dict.__name__))

        if self.uses_role and self.role:
            raise ACLException(C.make_error("ACL_TYPE_MISMATCH"))

        # Check given acls allowed are 'rwcdsexom'
        if not all(map(lambda x: x in 'rwcdsexom', acls)):
            raise ACLException(C.make_error("ACL_STRING_INVALID"))

        acl = {
                'topic': topic,
                'acls': acls,
                'options': options if options else {}}
        self.actions.append(acl)

    def get_members(self):
        """
        Returns the list of members this ACL is valid for.
        """
        return self.members

    def __str__(self):
        return self.repr_self()

    def repr_self(self, indent=0):
        """
        Generates a human readable representation of the ACL-object.
        """
        if self.uses_role:
            r = PluginRegistry.getInstance("ACLResolver")
            rstr = "\n%s<ACL> %s" % (" " * indent, str(self.members))
            rstr += "\n%s" % r.acl_roles[self.role].repr_self(indent + 1)
        else:
            rstr = "\n%s<ACL scope(%s)> %s: " % ((" " * indent), self.scope, str(self.members))
            for entry in self.actions:
                rstr += "\n%s%s:%s %s" % ((" " * (indent + 1)), entry['topic'], str(entry['acls']), str(entry['options']))
        return rstr

    def __getManagerUids(self, dn):
        """
        Returns a list with all uids that can manage the given dn.
        """
        index = PluginRegistry.getInstance("ObjectIndex")
        res = index.search({'dn': dn, 'manager': "%"}, {'manager': 1})
        if len(res):
            uids = []
            for item in res:
                for manager_dn in item['manager']:
                    p_uid = self.__getUidByDn(manager_dn)
                    if p_uid:
                        uids.append(p_uid)
            return uids
        else:
            return None

    def __getUidByDn(self, dn):
        """
        Returns the uid for a given dn.
        """
        index = PluginRegistry.getInstance("ObjectIndex")
        res = index.search({'dn': dn, '_type': 'User'}, {'uid': 1})
        if len(res) == 1:
            return res[0]['uid'][0]
        elif len(res) > 1:
            raise ValueError(C.make_error("ENTRY_NOT_UNIQUE", dn=dn))
        else:
            return None

    def match(self, user, topic, acls, targetBase, options=None, skip_user_check=False, used_roles=None, override_users=None):
        """
        Check if this ``ACL`` object matches the given criteria.

        .. warning::
            Do NOT use this to validate permissions. Use  ACLResolver->check() instead

        =============== =============
        Key             Description
        =============== =============
        user            The user we want to check for. E.g. 'hans'
        topic           The topic action we want to check for. E.g. 'org.gosa.factory'
        acls            A string containing the acls we want to check for.
        options         Special additional options that have to be checked.
        skip_user_check Skips checks for users, this is required to resolve roles.
        used_roles      A list of roles used in this recursion, to be able to check for endless-recursions.
        override_users  If an acl uses a role, then the original user list will be passed to the roles-match method
                        to ensure that we can match for the correct list of users.
        targetBase      To object that was initially checked for (DN)
        =============== =============
        """

        # Initialize list of already used roles, to avoid recursions
        if not used_roles:
            used_roles = []

        if self.uses_role:

            # Roles do not have users themselves, so we need to check
            # for the original set of users.
            override_users = override_users + self.members if override_users else self.members

            # Check for recursions while resolving the acls.
            if self.role in used_roles:
                raise ACLException(C.make_error("ACL_LOOP", role=self.role))

            # Resolve acls used in the role.
            used_roles.append(self.role)
            r = PluginRegistry.getInstance("ACLResolver")

            self.log.debug("checking ACL role entries for role: %s" % self.role)
            for acl in r.acl_roles[self.role]:
                (match, scope) = acl.match(user, topic, acls, targetBase, options if options else {}, False, used_roles, override_users)
                if match:
                    self.log.debug("ACL role entry matched for role '%s'" % self.role)
                    return match, scope

        else:
            for act in self.actions:

                users = override_users
                if not users:
                    users = self.members

                # Check if the given user string matches one of the defined users
                if skip_user_check:
                    user_match = True
                else:

                    # This acl applies to the owner/manager only!
                    if "o" in act['acls'] or "m" in act['acls']:

                        # Collect manager and owner uids and replace
                        # the original user list, to check only against
                        # owner and manager uids.
                        users = []
                        if "m" in act['acls']:
                            manager_uid = self.__getManagerUids(targetBase)
                            if manager_uid:
                                users = manager_uid

                        if "o" in act['acls']:
                            dn_uid = self.__getUidByDn(targetBase)
                            if dn_uid:
                                users.append(dn_uid)

                    user_match = False
                    for suser in users:
                        if re.match(suser, user):
                            user_match = True
                            break

                if not user_match:
                    continue

                # Check if the requested-action matches the acl-action.
                if not re.match(act['topic'], topic):
                    continue

                # Check if the required permission are allowed.
                if (set(acls) & set(act['acls'])) != set(acls):
                    continue

                # Check if all required options are given
                for entry in act['options']:

                    # Check for missing options
                    if entry not in options:
                        self.log.debug("ACL option '%s' is missing" % entry)
                        continue

                    # Simply match string options.
                    if isinstance(act['options'][entry], str) and not re.match(act['options'][entry], options[entry]):
                        self.log.debug("ACL option '%s' with value '%s' does not match with '%s'" % (entry,
                                    act['options'][entry], options[entry]))
                        continue

                    # Simply match string options.
                    elif act['options'][entry] != options[entry]:
                        self.log.debug("ACL option '%s' with value '%s' does not match with '%s'" % (entry,
                                    act['options'][entry], options[entry]))
                        continue

                # The acl rule matched!
                return True, self.scope

        # Nothing matched!
        return False, None

    def get_scope(self):
        """
        Returns the scope of an ACL.
        SUB, PSUB, RESET, ...
        """
        return self.scope


class ACLRoleEntry(ACL):
    """
    The ``ACLRoleEntry`` object describes a set of actions that can be accessed in a given scope.
    ``ACLRoleEntry`` classes can then be bundled in ``ACLRole`` objects, to build up roles.

    This class inherits most methods from :class:`gosa.backend.acl.ACL`, except for methods that manage members,
    due to the fact that ACLRoleEntries do not have members!

    Take a look at :class:`gosa.backend.acl.ACLRole` to get an idea about how roles are created.

    """

    def __init__(self, scope=ACL.SUB, role=None):
        super(ACLRoleEntry, self).__init__(scope=scope, role=role)
        self.log = logging.getLogger(__name__)

    def set_members(self, member):
        """
        An overloaded method from ACL which disallows to add users.
        """
        raise ACLException(C.make_error("ROLE_DIRECT_MEMBER"))


class CacheCheck:

    def __init__(self, function):
        self.function = function
        self.memoized = {}
        self.kwd_mark = object()     # sentinel for separating args from kwargs
        self.log = logging.getLogger(__name__)

    def __get__(self, instance, cls=None):
        self._instance = instance
        return self

    def __call__(self, user, topic, acls, options=None, base=None):
        try:
            key = "%s.%s.%s" % (user, topic, acls)
            if options is not None and len(options):
                key += "."+str(tuple(sorted(options.items())))
            if base is not None:
                key += "."+base
            res = self.memoized[key]
            self.log.debug("cache HIT %s" % key)
            return res
        except KeyError:
            self.log.debug("cache MISS %s" % key)
            self.memoized[key] = self.function(self._instance, user, topic, acls, options, base)
            return self.memoized[key]

    def cache_clear(self):
        self.memoized = {}


@implementer(IInterfaceHandler)
class ACLResolver(Plugin, SessionMixin):
    """
    The ACLResolver is responsible for loading, saving and resolving
    permission::

        >>> resolver = ACLResolver()
        >>> self.resolver.check('user1','org.gosa.factory','r')
        >>> self.resolver.check('user1','org.gosa.factory','rwx', 'dc=example,dc=net')

    If no base is given (last parameter of check), the default base will be used. (The default base is the configured LDAP base).

    To list all defined roles and acls you can use::

        >>> resolver = ACLResolver()
        >>> resolver.list_roles()
        >>> resolver.list_acls()

    To print a human readable output of an ACLSet just use the string
    representation::

        >>> acls = ACLSet('...')
        >>> acl = ACL(scope=ACL.ONE)
        >>> acls.add(acl)
        >>> acls
    """
    acl_sets = None
    acl_roles = None
    admins = []

    next_acl_id = 0

    _priority_ = 99
    _target_ = 'core'

    def __init__(self):
        self.env = Environment.getInstance()
        self.log = logging.getLogger(__name__)
        self.log.debug("initializing ACL resolver")

        # Listen for object events
        zope.event.subscribers.append(self.__handle_events)

        # Load default LDAP base
        self.base = self.env.base

    def __check_actions(self, actions):
        for action in actions:
            if 'acls' not in action:
                raise ACLException(C.make_error('ACL_MISSING_KEY', key="acls", action=action))
            if 'topic' not in action:
                raise ACLException(C.make_error('ACL_MISSING_KEY', key="topic", action=action))
            if 'options' not in action:
                action['options'] = {}
            if type(action['options']) != dict:
                raise ACLException(C.make_error("ATTRIBUTE_INVALID", "options", type=dict.__name__))
            if len(set(action['acls']) - set("rwcdmxose")) != 0:
                raise ACLException(C.make_error("ACL_STRING_INVALID"))

    def __handle_events(self, event):
        """
        React on object modifications to keep active ACLs up to date.
        """

        if event.__class__.__name__ == "IndexScanFinished":
            self.log.info("index scan finished, triggered acl-reload")
            self.load_acls()

        if isinstance(event, ObjectChanged):

            # Only act on these events
            if not event.reason in ["post object create", "post object update", "post object remove", "post remove"]:
                return

            reload = False
            index = PluginRegistry.getInstance("ObjectIndex")
            res = index.search({"dn": event.dn},  {'AclSets': 1, '_type': 1})
            if res:
                for item in res:
                    if '_type' in item and item['_type'] == "AclRole":
                        reload = True
                    elif 'AclSets' in item:
                        reload = True

                if reload:
                    self.log.info("object change for %s triggered acl-reload" % event.dn)
                    self.load_acls()

    def load_acls(self):
        """
        Load acls definitions from backend
        """
        self.clear()

        # Load override admins from configuration
        admins = self.env.config.get("backend.admins", default=None)
        if admins:
            admins = re.sub(r'\s', '', admins)
            self.log.warning("adding users to the ACL override: %s" % admins)
            self.admins = admins.split(",")

        # Load Acls from the object DB
        self.load_from_object_database()

    def list_admin_accounts(self):
        """
        Returns the list of admins accounts. Those hardcoded in the GOsa config.
        """
        return self.admins

    def get_next_acl_id(self):
        """
        Generate a unique ID for each AclEntry used in Sets or Roles.
        """
        used_ids = []
        if self.acl_sets is not None:
            for aclset in self.acl_sets:
                for acl in aclset:
                    used_ids.append(acl.id)

        if self.acl_roles is not None:
            for aclrole in self.acl_roles:
                for acl in self.acl_roles[aclrole]:
                    used_ids.append(acl.id)

        self.next_acl_id += 1
        while self.next_acl_id in used_ids:
            self.next_acl_id += 1

        return self.next_acl_id

    def clear(self):
        """
        Clears all information abouts roles and acls.
        This is called during initialization of the ACLResolver class.
        """
        self.acl_sets = []
        self.acl_roles = {}
        self.next_acl_id = 0

    def serve(self):
        """
        Load ACL definitions once all plugins are loaded.
        """
        self.load_acls()

    def load_from_object_database(self):
        """
        Loads acl definitions from the object databases
        """

        # A map for scope-strings to konstants
        acl_scope_map = {'one': ACL.ONE, 'sub': ACL.SUB, 'psub': ACL.PSUB, 'reset': ACL.RESET}

        roles = {}
        unresolved = []

        # Read all AclRole objects.
        dns = []
        index = PluginRegistry.getInstance("ObjectIndex")
        res = index.search({'_type': 'AclRole'}, {'dn': 1})
        if len(res):
            dns = [x['dn'] for x in res]

        for entry_dn in set(dns):

            self.log.info("found acl-role %s" % entry_dn)

            # Try to open the object
            try:
                o = ObjectProxy(entry_dn)
            except:
                self.log.warning("failed to load acl-role information for '%s'" % entry_dn)
                continue

            # Create a new role object with the given name on demand.
            if o.name not in roles:
                roles[o.name] = ACLRole(o.name, entry_dn)

            # Check if this role was referenced before but not initialized
            if o.name in unresolved:
                unresolved.remove(o.name)

            # Append the role acls to the ACLRole object
            for acl_entry in o.AclRoles:

                # The acl entry refers to another role entry.
                if 'rolename' in acl_entry and acl_entry['rolename']:

                    # If the role wasn't loaded yet, then create and attach the requested role
                    # to the list of roles, but mark it as unresolved
                    rn = acl_entry['rolename']
                    if rn not in roles:
                        unresolved.append(rn)
                        roles[rn] = ACLRole(rn)
                        self.add_acl_role(roles[rn])

                    # Add the acl entry entry which refers to the role.
                    acl = ACLRoleEntry()
                    acl.uses_role = True
                    acl.scope = None
                    acl.role = rn
                    acl.set_priority(int(acl_entry["priority"]))
                    roles[o.name].add(acl)
                    self.add_acl_role(roles[o.name])
                else:

                    # Add a normal (non-role) base acl entry
                    acl = ACLRoleEntry(acl_scope_map[acl_entry["scope"]])
                    acl.set_priority(int(acl_entry["priority"]))
                    for action in acl_entry["actions"]:
                        acl.add_action(action["topic"], action['acl'], action['options'])
                    roles[o.name].add(acl)

        # Check if we've got unresolved roles!
        if len(unresolved):
            raise ACLException(C.make_error("ROLE_UNRESOLVED_REFERENCES", references=", ".join(unresolved)))

        # Add the recently created roles.
        for role_name in roles:
            self.add_acl_role(roles[role_name])

        # Load all objects that have the Acl extension enabled
        dns = []
        index = PluginRegistry.getInstance("ObjectIndex")

        res = index.search({'AclSets': '%'}, {'dn': 1})
        if len(res):
            dns = [x['dn'] for x in res]

        for entry_dn in set(dns):
            self.log.info("found acl for object %s" % entry_dn)

            # Try to load the object to read the AclSets parameter from it.
            try:
                o = ObjectProxy(entry_dn)
            except:
                self.log.warning("failed to load acl information for '%s'" % entry_dn)
                continue

            # No definitions in this Acl
            if not o.AclSets:
                continue

            # The ACL definition is based on an acl role.
            base = o.dn
            acls = ACLSet(base)
            for acls_data in o.AclSets:
                try:
                    if 'rolename' in acls_data and acls_data['rolename']:
                        acl = ACL(role=str(acls_data['rolename']))
                        acl.set_members(acls_data["members"])
                        acl.set_priority(int(acls_data["priority"]))
                    else:
                        acl = ACL(acl_scope_map[acls_data["scope"]])
                        acl.set_members(acls_data["members"])
                        acl.set_priority(int(acls_data["priority"]))
                        for action in acls_data["actions"]:
                            acl.add_action(action['topic'], action['acl'], action['options'])
                    acls.add(acl)
                except Exception as e:
                    self.log.warning("failed to load acl information for '%s': %s" % (entry_dn, str(e)))
                    continue

            self.add_acl_set(acls)

    def add_acl_set(self, acl):
        """
        Adds an ACLSet object to the list of active-acl rules.
        """
        if not self.aclset_exists_by_base(acl.base):
            self.acl_sets.append(acl)
            self.check.cache_clear()
        else:
            for item in acl:
                self.add_acl_to_set(acl.base, item)

    def add_acl_to_set(self, base, acl):
        """
        Adds an ACL-object to an existing ACLSet.

        ============== =============
        Key            Description
        ============== =============
        base           The base we want to add an ACL object to.
        acl            The ACL object we want to add.
        ============== =============
        """
        if not self.aclset_exists_by_base(base):
            raise ACLException(C.make_error("ACL_NO_BASE_ACL", base=base))
        else:
            aclset = self.get_aclset_by_base(base)
            aclset.add(acl)
            self.check.cache_clear()
        return True

    def add_acl_to_role(self, rolename, acl):
        """
        Adds an ACLRoleEntry-object to an existing ACLRole.

        ============== =============
        Key            Description
        ============== =============
        rolename       The name of the role we want to add this ACLRoleEntry to.
        acl            The ACLRoleEntry object we want to add.
        ============== =============
        """

        if type(acl) != ACLRoleEntry:
            raise ACLException(C.make_error("ATTRIBUTE_INVALID", "acl", type=type(acl).__name__))

        if rolename not in self.acl_roles:
            raise ACLException(C.make_error("ROLE_NOT_FOUND", role=rolename))
        else:
            self.acl_roles[rolename].add(acl)
            self.check.cache_clear()
        return True

    def add_acl_role(self, role):
        """
        Adds a new ACLRole-object to the ACLResolver class.

        ============== =============
        Key            Description
        ============== =============
        role           The ACLRole object we want to add.
        ============== =============
        """
        self.acl_roles[role.name] = role
        self.check.cache_clear()

    @CacheCheck
    def check(self, user, topic, acls, options=None, base=None):
        """
        Check permission for a given user and a base.

        ============== =============
        Key            Description
        ============== =============
        user           The user we want to check for.
        topic          The topic string, e.g. 'org.gosa.factory'
        acls           The list of acls, we want to check for, e.g. 'rcwdm'
        options        A dictionary containing extra options to check for.
        base           The base we want to check acls in.
        ============== =============

        For details about ``topic``, ``options`` and ``acls``, click here: :ref:`Scope values <scope_description>`, :ref:`Topic <topic_description>`, :ref:`ACLs <acls_description>` and :ref:`Options <options_description>`

        Example::
            >>> resolver = ACLResolver()
            >>> self.resolver.check('user1','org.gosa.factory','r')
            >>> self.resolver.check('user1','org.gosa.factory','rwx', 'dc=example,dc=net')

        """

        # Admin users are allowed to do anything.
        if user in self.admins or user is None:
            self.log.debug("ACL check override active for %s/%s/%s" % (user, base, str(topic)))
            return True

        # Load default base if needed
        if not base:
            base = self.base

        # Collect all acls matching the where statement
        allowed = False
        reset = False

        self.log.debug("checking ACL for %s/%s/%s" % (user, base, str(topic)))

        # Remove the first part of the dn, until we reach the ldap base.
        orig_loc = base
        while self.base in base and len(base):

            # Check acls for each acl set.
            if not self.acl_sets:
                base = ','.join(ldap.dn.explode_dn(base)[1::])
                continue

            for acl_set in self.acl_sets:

                # Skip acls that do not match the current ldap base.
                if base != acl_set.base:
                    continue

                # Check ACls
                for acl in acl_set:

                    (match, scope) = acl.match(user, topic, acls, orig_loc, options)
                    if match:

                        self.log.debug("found matching ACL in '%s'" % base)
                        if scope == ACL.RESET:
                            self.log.debug("found ACL reset for topic '%s'" % topic)
                            reset = True
                        else:

                            if scope == ACL.PSUB:
                                self.log.debug("found permanent ACL for topic '%s'" % topic)
                                return True

                            elif scope == ACL.SUB:
                                if not reset:
                                    self.log.debug("found ACL for topic '%s' (SUB)" % topic)
                                    return True
                                else:
                                    self.log.debug("ACL DO NOT match due to reset. (SUB)")

                            elif scope == ACL.ONE and orig_loc == acl_set.base:
                                if not reset:
                                    self.log.debug("found ACL for topic '%s' (ONE)" % topic)
                                    return True
                                else:
                                    self.log.debug("ACL DO NOT match due to reset. (ONE)")

            # Remove the first part of the dn
            base = ','.join([d for d in ldap.dn.explode_dn(base.encode('utf-8'), flags=ldap.DN_FORMAT_LDAPV3)[1::]])

        return allowed

    def list_acls(self):
        """
        Returns all ACLSets attached to the resolver
        """
        return self.acl_sets

    def list_acl_bases(self):
        """
        Returns all bases we've acls attached to
        """
        return [entry.base for entry in self.acl_sets]

    def list_role_names(self):
        return self.acl_roles.keys()

    def list_roles(self):
        """
        Returns all ACLRoles attached to the resolver
        """
        return self.acl_roles

    def is_role_used(self, rolename):
        """
        Checks whether the given ACLRole object is used or not.

        ============== =============
        Key            Description
        ============== =============
        rolename       The name of the role we want to check for.
        ============== =============
        """

        if not isinstance(rolename, str):
            raise ACLException(C.make_error("ATTRIBUTE_INVALID", "rolename", type=str.__name__))

        for aclset in self.acl_sets:
            if self.__is_role_used(aclset, rolename):
                return True
        return False

    def __is_role_used(self, aclset, rolename):
        for acl in aclset:
            if acl.uses_role:
                if acl.role == rolename:
                    return True
                else:
                    role_acl_sets = self.acl_roles[acl.role]
                    if self.__is_role_used(role_acl_sets, rolename):
                        return True

        return False

    def get_aclset_by_base(self, base):
        """
        Returns an acl set by base.

        ============== =============
        Key            Description
        ============== =============
        base           The base we want to return the ACLSets for.
        ============== =============
        """
        if self.aclset_exists_by_base(base):
            for aclset in self.acl_sets:
                if aclset.base == base:
                    return aclset
        else:
            raise ACLException(C.make_error("ACL_NOT_FOUND_ON_BASE", base=base))

    def aclset_exists_by_base(self, base):
        """
        Checks if a ACLSet for the given base exists or not.

        ============== =============
        Key            Description
        ============== =============
        base           The base we want to check for.
        ============== =============
        """
        for aclset in self.acl_sets:
            if aclset.base == base:
                return True
        return False

    def remove_aclset_by_base(self, base):
        """
        Removes a given ACLSet by base.

        ============== =============
        Key            Description
        ============== =============
        base           The base we want to delete ACLSets for.
        ============== =============
        """

        # Remove all aclsets for the given base
        found = 0
        for aclset in self.acl_sets:
            if aclset.base == base:
                self.acl_sets.remove(aclset)
                found += 1

        # Send a message if there were no ACLSets for the given base
        if  not found:
            raise ACLException(C.make_error("ACL_NOT_FOUND_ON_BASE", base=base))
        self.check.cache_clear()

    def remove_role(self, name):
        """
        Removes an acl role by name.

        ============== =============
        Key            Description
        ============== =============
        name           The name of the role that have to be removed.
        ============== =============
        """

        # Allow to remove roles by passing ACLRole-objects.
        if type(name) == ACLRole:
            name = name.name

        # Check if we've got a valid name type.
        if not isinstance(name, str):
            raise ACLException(C.make_error("ATTRIBUTE_INVALID", "name", type=str.__name__))

        # Check if such a role-name exists and then try to remove it.
        if name in self.acl_roles:
            if self.is_role_used(self.acl_roles[name].name):
                raise ACLException(C.make_error("ROLE_IN_USE", role=name))
            else:
                del(self.acl_roles[name])
                self.check.cache_clear()
                return True
        else:
            raise ACLException(C.make_error("ROLE_NOT_FOUND", role=name))

    def add_acl_to_base(self, base, acl):
        """
        Adds an ACL object to an existing ACLSet which is identified by its base.

        ============== =============
        Key            Description
        ============== =============
        base           The base we want to add an acl to.
        acl            The 'ACL' object we want to add.
        ============== =============
        """
        if type(acl) != ACL:
            raise ACLException(C.make_error("ATTRIBUTE_INVALID", "acl", type=ACL.__name__))

        for aclset in self.acl_sets:
            if aclset.base == base:
                aclset.add(acl)
                self.check.cache_clear()

    def remove_acls_for_user(self, user):
        """
        Removes all permission for the given user!

        ============== =============
        Key            Description
        ============== =============
        user           The username to remove acls for.
        ============== =============

        Example::

            aclset = ACLSet()
            acl = ACL(scope=ACL.ONE)
            acl.set_members([u'tester1', u'tester2'])
            acl.add_action('...', 'rwx')
            acl.set_priority(100)
            aclset.add(acl)
            resolver.add(aclset)

            resolver.remove_acls_for_user('tester1')

            ...

        """
        for aclset in self.acl_sets:
            aclset.remove_acls_for_user(user)
            self.check.cache_clear()

    def _get_base(self, base, bases):
        c = []

        for b in bases:
            if base.endswith(b):
                c.append(b)

        if not c:
            return None

        return sorted(c, key=len, reverse=True)[0]

    @Command(needsUser=True, __help__=N_("Get entry points for browsing the object tree."))
    def getEntryPoints(self, user):

        # Check if we've an admin override first
        if user in self.admins:
            return [self.env.base]

        sub_bases = {}
        bases = {}

        with self.make_session() as session:
            print(session)
            # Walk thru all ACL definitions and check if the current user
            # can read the base entry
            for aclset in self.acl_sets:
                res = session.query(ObjectInfoIndex).filter(ObjectInfoIndex.dn == aclset.base).one_or_none()
                if not res:
                    raise ACLException(C.make_error("ACL_BASE_ERROR"))
                base_type = res._type

                # Check if this ACL is eventually already covered by a previous sub ACL
                for acl in aclset:
                    if user in acl.members:

                        # Collect ACL
                        d_acls = []
                        if acl.uses_role:
                            for entry in self.acl_roles[acl.role]:
                                d_acls.append((entry.actions, entry.scope))

                        else:
                            d_acls.append((acl.actions, acl.scope))

                        # Walk thru the collected d_acls and check: their actions,
                        # their options and their scope
                        for actions, scope in d_acls:

                            # Check for ACL resets. If this is a reset rule, the remaining
                            # results can be ignored
                            if scope == ACL.RESET:
                                sub_bases[aclset.base] = scope
                                break

                            # Options?
                            for action in actions:
                                if not action['options']:

                                    # Does this ACL affect 'domain'.objects?
                                    if re.match(action['topic'], "%s.objects.%s" % (self.env.domain, base_type)):

                                        # Check for read and search access
                                        if "r" in action['acls'] and "s" in action['acls']:

                                            # Ok. Seems to be a candidate. Check for [P]?SUB/RESET
                                            s_base = self._get_base(aclset.base, sub_bases.keys())
                                            if s_base:

                                                # If the preceding base was "RESET, we've a new base
                                                if sub_bases[s_base] == ACL.RESET:
                                                    bases[aclset.base] = True

                                                # Elseways - we do not care, because it does not change our
                                                # permissions

                                            else:
                                                bases[aclset.base] = True

                                            # Depending on the scope, feed different base stores
                                            if scope in [ACL.SUB, ACL.PSUB]:
                                                sub_bases[aclset.base] = scope

                                # Options! Search for all potentially affected entries and check the permissions
                                else:
                                    for attr, val in action['options'].items():
                                        entries = []

                                        match_attr = None
                                        if attr in ObjectInfoIndex:
                                            entries = session.query(ObjectInfoIndex).filter(and_(
                                                or_(ObjectInfoIndex.dn == aclset.base, ObjectInfoIndex.dn.like("%," + aclset.base)),
                                                getattr(ObjectInfoIndex, attr) == val
                                                ))
                                        else:
                                            entries = session.query(ObjectInfoIndex).filter(and_(
                                                ObjectInfoIndex.uuid == KeyValueIndex.uuid,
                                                or_(ObjectInfoIndex.dn == aclset.base, ObjectInfoIndex.dn.like("%," + aclset.base)),
                                                KeyValueIndex.key == attr,
                                                KeyValueIndex.value == val,
                                                ))

                                        for entry in entries:
                                            if self.check(user, "%s.objects.%s" % (self.env.base, entries['_type']), "rs", None, entry['dn']):
                                                # Ok. Seems to be a candidate. Check for [P]?SUB/RESET
                                                s_base = self._get_base(entry['dn'], sub_bases.keys())
                                                if s_base:
                                                    if sub_bases[s_base] == ACL.RESET:
                                                        bases[entry['dn']] = True
                                                else:
                                                    bases[entry['dn']] = True

        return list(bases.keys())

    @Command(needsUser=True, __help__=N_("List allowed Actions by topic."))
    def getAllowedActions(self, user, topic, base=None):
        # Actions we are interested in
        check = ['c', 'w', 'r', 'd']

        # Admin users are allowed to do anything.
        if user in self.admins:
            return check

        result = [x for x in check if self.check(user, topic, x, None, base=base)]
        return result

    @Command(needsUser=True, __help__=N_("List allowed Actions for the given object type."))
    def getAllowedActionsByType(self, user, type):
        return self.getAllowedActions(user, "%s.objects.%s" % (self.env.domain, type))

    @Command(needsUser=True, __help__=N_("List defined ACLs by base or topic."))
    def getACLs(self, user, base=None, topic=None):
        """
        This command returns a lists of defined ACLs, including hard coded
        system-admins (configuration file).

        You can filter the result by using the ``topic`` and ``base`` parameters.
        The ``base`` parameter will only list permissions defined for the given base,
        where the ``topic`` parameter will list all acls that match the given topic value.

        Example::

            >>> getACLs(base='dc=gonicus,dc=de')
            >>> getACLs(topic=r'^com\.gonicus\.factory$')

        ============== =============
        Key            Description
        ============== =============
        base           (optional) The base we want to list the permissions for.
        topic          (optional) The topic we want to list acls for.
        ============== =============

        """
        acl_scope_map = {ACL.ONE: 'one', ACL.SUB: 'sub', ACL.PSUB: 'psub', ACL.RESET: 'reset'}

        # Collect all acls
        result = {}
        for aclset in self.acl_sets:
            if base == aclset.base or base is None:

                # Check permissions
                if not self.check(user, '%s.acl' % self.env.domain, 'r', None, aclset.base):
                    print("ACCESS DENIED: User: %s, topic: %s.acl, base: %s" % (user, self.env.domain, aclset.base))
                    continue

                for acl in aclset:

                    # Check if this acl matches the requested topic
                    match = True
                    if topic is not None:
                        match = False

                        # Walk through defined topics of the current acl and check if one
                        # matches the required topic.
                        for action in acl.actions:
                            if re.match(action['topic'], topic):
                                match = True
                                break

                    # The current ACL matches the requested topic add it to the result.
                    if match:

                        if not aclset.base in result:
                            result[aclset.base] = []

                        if acl.uses_role:
                            result[aclset.base].append({'id': acl.id,
                                'members': acl.members,
                                'priority': acl.priority,
                                'rolename': acl.role})
                        else:
                            result[aclset.base].append({'id': acl.id,
                                'members': acl.members,
                                'scope': acl_scope_map[acl.scope],
                                'priority': acl.priority,
                                'actions': acl.actions})

        # Append configured admin accounts
        admins = self.list_admin_accounts()
        if len(admins) and self.check(user, '%s.acl' % self.env.domain, 'r'):
            if topic is None or re.match(topic, '*'):
                if not self.base in result:
                    result[self.base] = []
                result[self.base].append(
                        {'id': None,
                    'priority': 100,
                    'members': admins,
                    'scope': acl_scope_map[ACL.PSUB],
                    'actions': [{'topic': '*', 'acls':'rwcdsxe', 'options': {}}]})

        return result

    @Command(needsUser=True, __help__=N_("Remove defined ACL by ID."))
    def removeACL(self, user, acl_id):
        """
        This command removes an acl definition by its id.

        ============== =============
        Key            Description
        ============== =============
        acl_id         The id of the acl to remove.
        ============== =============

        ``Return``: Boolean True on success else False

        Example:
            >>> getACls(base='dc=gonicus,dc=de')
            >>> getACls(topic=r'com\.gonicus\.factory')

        """

        # Now walk through aclsets and remove the acl with the given ID.
        for aclset in self.acl_sets:
            for acl in aclset:
                if acl.id == acl_id:

                    # Check permissions
                    if not self.check(user, '%s.acl' % self.env.domain, 'w', None, aclset.base):
                        raise ACLException(C.make_error('PERMISSION_REMOVE', target=acl_id))

                    # Remove the acl from the set.
                    aclset.remove(acl)

                    # We've removed the last acl for this base,  remove the aclset.
                    if len(aclset) == 0:
                        self.remove_aclset_by_base(aclset.base)
                    self.check.cache_clear()
                    return True

        # Nothing removed
        raise ACLException(C.make_error("ACL_NOT_FOUND"))

    @Command(needsUser=True, __help__=N_("Add a new ACL."))
    def addACL(self, user, base, priority, members, actions=None, scope=None, rolename=None):
        """
        Adds a new acl-rule to the active acls.

        ============== =============
        Key            Description
        ============== =============
        base           The base this acl works on. E.g. 'dc=example,dc=de'
        priority       An integer value to prioritize this acl-rule. (Lower values mean higher priority)
        members        A list of members this acl affects. E.g. [u'Herbert', u'klaus']
        actions        A dictionary which includes the topic and the acls this rule includes.
        scope          The 'scope' defines how an acl is inherited by sub-bases. See :ref:`Scope values <scope_description>` for details.
        rolename       The name of the role to use.
        ============== =============

        The **actions** parameter is dictionary with three items ``topic``, ``acls`` and ``options``.

        For details about ``scope``, ``topic``, ``options`` and ``acls``, click here:
            :ref:`Scope values <scope_description>`, :ref:`Topic <topic_description>`, :ref:`ACLs <acls_description>` and :ref:`Options <options_description>`

        Example:

            >>> resolver.addACL('dc=gonicus,dc=de', 'sub', 0, [u'tester1'], [{'topic': r'^some\.topic.*$', 'acls': 'rwcdm'}])

        or with some options:

            >>> resolver.addACL('dc=gonicus,dc=de', 'sub', 0, [u'tester1'], [{'topic': r'^some\.topic.*$', 'acls': 'rwcdm', 'options': {'uid': '^u[0-9]'}}])

        """

        # Check permissions
        if not self.check(user, '%s.acl' % self.env.domain, 'w', None, base):
            raise ACLException(C.make_error('PERMISSION_CREATE', target=base))

        # Validate the given scope
        scope_int = ACL.SUB
        if scope:
            acl_scope_map = {'one': ACL.ONE, 'sub': ACL.SUB, 'psub': ACL.PSUB, 'reset': ACL.RESET}

            if scope not in acl_scope_map:
                raise ACLException(C.make_error("ACL_INVALID_SCOPE", scope=scope))

            scope_int = acl_scope_map[scope]

        # Validate the priority
        if type(priority) != int:
            raise ACLException(C.make_error("ATTRIBUTE_INVALID", "priority", type=int.__name__))

        if priority < -100 or priority > 100:
            raise ACLException(C.make_error('ACL_PRIORITY_INVALID'))

        # Validate given actions
        if actions:
            if type(actions) != list:
                raise ACLException(C.make_error("ATTRIBUTE_INVALID", "actions", type=list.__name__))
            else:
                self.__check_actions(actions)

        # We can either set actions or a role, but not both.
        if actions and rolename:
            raise ACLException(C.make_error("ACL_PARAMETER_MISMATCH"))

        # All checks passed now add the new ACL.

        # Do we have an ACLSet for the given base, No?
        if not self.aclset_exists_by_base(base):
            self.add_acl_set(ACLSet(base))

        # Create a new acl with the given parameters
        if actions:
            acl = ACL(scope_int)
            acl.set_members(members)
            acl.set_priority(priority)
            for action in actions:
                acl.add_action(action['topic'], action['acls'], action['options'])
            self.add_acl_to_base(base, acl)
            return acl.id

        if rolename:
            acl = ACL(role=rolename)
            acl.set_members(members)
            acl.set_priority(priority)
            self.add_acl_to_base(base, acl)
            return acl.id

    @Command(needsUser=True, __help__=N_("Refresh existing ACL by ID."))
    def updateACL(self, user, acl_id, scope=None, priority=None, members=None, actions=None, rolename=None):
        """
        Updates an acl by ID.

        ============== =============
        Key            Description
        ============== =============
        id             The ID of the acl we want to update.
        scope          The 'scope' defines how an acl is inherited by sub-bases. See :ref:`Scope values <scope_description>` for details.
        priority       An integer value to prioritize this acl-rule. (Lower values mean higher priority)
        members        A new list of members.
        actions        A dictionary which includes the topic and the acls this rule includes.
        rolename       The name of the role to use.
        ============== =============

        For details about ``scope``, ``topic``, ``options`` and ``acls``, click here:
            :ref:`Scope values <scope_description>`, :ref:`Topic <topic_description>`, :ref:`ACLs <acls_description>` and :ref:`Options <options_description>`

        Example:

            >>> resolver.addACLtoRole('rolle1', 'sub', 0, ['peter'], [{'topic': '^some\.topic.*$', 'acls': 'rwcdm'}])

        or with some options:

            >>> resolver.addACLtoRole('rolle1', 'sub', 0, ['peter'], [{'topic': '^some\.topic.*$', 'acls': 'rwcdm', 'options': {'uid': '^u[0-9]'}}])

        """
        # Validate the given scope
        scope_int = ACL.SUB
        if scope:
            acl_scope_map = {'one': ACL.ONE, 'sub': ACL.SUB, 'psub': ACL.PSUB, 'reset': ACL.RESET}

            if scope not in acl_scope_map:
                raise ACLException(C.make_error("ACL_INVALID_SCOPE", scope=scope))

            scope_int = acl_scope_map[scope]

        # Validate given actions
        new_actions = []

        if actions:
            if type(actions) != list:
                raise ACLException(C.make_error("ATTRIBUTE_INVALID", "actions", type=list.__name__))
            else:
                self.__check_actions(actions)

                for action in actions:
                    # Create a new action entry
                    entry = {'acls': action['acls'],
                             'topic': action['topic'],
                             'options': action['options']}
                    new_actions.append(entry)

        # Check if there is a with the given and and whether we've write permissions to it or not.
        acl = None
        for _aclset in self.acl_sets:
            for _acl in _aclset:
                if _acl.id == acl_id:

                    # Check permissions
                    if not self.check(user, '%s.acl' % self.env.domain, 'w', None, _aclset.base):
                        raise ACLException(C.make_error("PERMISSION_UPDATE", target=_aclset.base))

                    acl = _acl

        # Check if we've found a valid acl object with the given id.
        if not acl:
            raise ACLException(C.make_error("ACL_NOT_FOUND"))

        if actions and rolename:
            raise ACLException(C.make_error("ACL_PARAMETER_MISMATCH"))

        # Update properties
        if members:
            acl.set_members(members)

        if priority:
            acl.set_priority(priority)

        if actions:
            acl.clear_actions()
            for action in new_actions:
                acl.add_action(action['topic'], action['acls'], action['options'])

        if rolename:
            acl.clear_actions()
            acl.use_role(rolename)

        if scope:
            acl.set_scope(scope_int)
        self.check.cache_clear()

    @Command(needsUser=True, __help__=N_("List defined roles."))
    def getACLRoles(self, user):
        """
        This command returns a lists of all defined ACLRoles.

        Example::

            >>> getAClRoles()

        """

        # Check permissions
        if not self.check(user, '%s.acl' % self.env.domain, 'r', None, self.base):
            raise ACLException(C.make_error("PERMISSION_ACCESS", target=self.base))

        acl_scope_map = {ACL.ONE: 'one', ACL.SUB: 'sub', ACL.PSUB: 'psub', ACL.RESET: 'reset'}

        # Collect all acls
        result = []
        for aclrole in self.acl_roles:
            entry = {'name': self.acl_roles[aclrole].name,
                     'dn': self.acl_roles[aclrole].dn,
                     'acls': []}

            for acl in self.acl_roles[aclrole]:
                acl_entry = {'id': acl.id}
                if acl.uses_role:
                    acl_entry['priority'] = acl.priority
                    acl_entry['rolename'] = acl.role
                else:
                    acl_entry['priority'] = acl.priority
                    acl_entry['scope'] = acl_scope_map[acl.scope]
                    acl_entry['actions'] = acl.actions
                entry['acls'].append(acl_entry)
            result.append(entry)

        return result

    @Command(needsUser=True, __help__=N_("Add new role."))
    def addACLRole(self, user, rolename):
        """
        Creates a new acl-role.

        ============== =============
        Key            Description
        ============== =============
        rolename       The name of the new role.
        ============== =============

        Example:

        >>> addACLRole('role1')
        >>> addACLtoRole('role1', 0, {...}, scope='sub')

        """

        # Check permissions
        if not self.check(user, '%s.acl' % self.env.domain, 'w', None, self.base):
            raise ACLException(C.make_error('PERMISSION_CREATE', target=self.base))

        # Validate the rolename
        if not isinstance(rolename, str) or len(rolename) <= 0:
            raise ACLException(C.make_error("ATTRIBUTE_INVALID", "rolename", type=str.__name__))

        # Check if rolename exists
        if rolename in self.acl_roles:
            raise ACLException(C.make_error("ROLE_EXISTS", name=rolename))

        # Create and add the new role
        role = ACLRole(rolename)
        self.add_acl_role(role)

    @Command(needsUser=True, __help__=N_("Add new acl to an existing role."))
    def addACLToRole(self, user, rolename, priority, actions=None, scope=None, use_role=None):
        """
        Adds a new acl to an existing role.

        ============== =============
        Key            Description
        ============== =============
        rolename       The name of the acl-role we want to add to.
        priority       An integer value to prioritize this acl-rule. (Lower values mean higher priority)
        actions        A dictionary which includes the topic and the acls this rule includes.
        scope          The 'scope' defines how an acl is inherited by sub-bases. See :ref:`Scope values <scope_description>` for details.
        use_role       The role-name to use if we do not assign actions directly using the actions parameter.
        ============== =============

        For details about ``scope``, ``topic``, ``options`` and ``acls``, click here:
            :ref:`Scope values <scope_description>`, :ref:`Topic <topic_description>`, :ref:`ACLs <acls_description>` and :ref:`Options <options_description>`

        Example:

            >>> resolver.addACLtoRole('rolle1', 0, [{'topic': r'^some\.topic.*$', 'acls': 'rwcdm'}], 'sub')

        or with some options:

            >>> resolver.addACLtoRole('rolle1', 0, [{'topic': r'^some\.topic.*$', 'acls': 'rwcdm', 'options': {'uid': '^u[0-9]'}}], 'sub')

        """

        # Check permissions
        if not self.check(user, '%s.acl' % self.env.domain, 'w', None, self.base):
            raise ACLException(C.make_error("PERMISSION_CREATE", target=self.base))

        # Check if the given rolename exists
        if rolename not in self.acl_roles:
            raise ACLException(C.make_error("ROLE_NOT_FOUND", role=rolename))

        # Validate the priority
        if type(priority) != int:
            raise ACLException(C.make_error("ATTRIBUTE_INVALID", "priority", type=int.__name__))

        if priority < -100 or priority > 100:
            raise ACLException(C.make_error("ACL_PRIORITY_INVALID"))

        # Validate the given scope and actions
        scope_int = ACL.SUB
        if actions:
            acl_scope_map = {'one': ACL.ONE, 'sub': ACL.SUB, 'psub': ACL.PSUB, 'reset': ACL.RESET}

            if scope not in acl_scope_map:
                raise TypeError(C.make_error("ACL_INVALID_SCOPE", scope=scope))

            scope_int = acl_scope_map[scope]

            if type(actions) != list:
                raise ACLException(C.make_error("ATTRIBUTE_INVALID", "actions", type=list.__name__))
            else:
                self.__check_actions(actions)

        # We can either set actions or a role, but not both.
        if actions and use_role:
            raise ACLException(C.make_error("ACL_PARAMETER_MISMATCH"))

        if use_role and use_role == rolename:
            raise ACLException(C.make_error("ROLE_CANNOT_POINT_TO_ITSELF"))

        # All checks passed now add the new ACL.

        # Create a new acl with the given parameters
        if actions:
            acl = ACLRoleEntry(scope_int)
            acl.set_priority(priority)
            for action in actions:
                acl.add_action(action['topic'], action['acls'], action['options'])
            self.add_acl_to_role(rolename, acl)
            return acl.id

        elif use_role:
            acl = ACLRoleEntry(role=use_role)
            acl.set_priority(priority)
            self.add_acl_to_role(rolename, acl)
            return acl.id

    @Command(needsUser=True, __help__=N_("Refresh existing role by ID."))
    def updateACLRole(self, user, acl_id, scope=None, priority=None, actions=None, use_role=None):
        """
        Updates an role-acl by ID.

        ============== =============
        Key            Description
        ============== =============
        id             The ID of the role-acl we want to update.
        scope          The 'scope' defines how an acl is inherited by sub-bases. See :ref:`Scope values <scope_description>` for details.
        priority       An integer value to prioritize this acl-rule. (Lower values mean higher priority)
        actions        A dictionary which includes the topic and the acls this rule includes.
        use_role       The role-name to use if we do not assign actions directly using the actions parameter.
        ============== =============

        For details about ``scope``, ``topic``, ``options`` and ``acls``, click here:
            :ref:`Scope values <scope_description>`, :ref:`Topic <topic_description>`, :ref:`ACLs <acls_description>` and :ref:`Options <options_description>`

        Example:

            >>> resolver.updateACLRole(1, 'sub', 0, ['peter'], [{'topic': '^some\.topic.*$', 'acls': 'rwcdm'}])

        or with some options:

            >>> resolver.updateACLRole(1, 'sub', 0, ['peter'], [{'topic': '^some\.topic.*$', 'acls': 'rwcdm', 'options': {'uid': '^u[0-9]'}}])

        """

        # Check permissions
        if not self.check(user, '%s.acl' % self.env.domain, 'w', None, self.base):
            raise ACLException(C.make_error("PERMISSION_UPDATE", target=self.base))

        # Validate the priority
        if priority is not None and type(priority) != int:
            raise ACLException(C.make_error("ATTRIBUTE_INVALID", "priority", type=int.__name__))

        # Check for priority
        if priority is not None and (priority < -100 or priority > 100):
            raise ACLException(C.make_error('ACL_PRIORITY_INVALID'))

        # We cannot set a role and actions.
        if actions and use_role:
            raise ACLException(C.make_error("ACL_PARAMETER_MISMATCH"))

        # Validate the scope value
        scope_int = ACL.SUB
        if scope:
            acl_scope_map = {'one': ACL.ONE, 'sub': ACL.SUB, 'psub': ACL.PSUB, 'reset': ACL.RESET}

            if scope not in acl_scope_map:
                raise TypeError(C.make_error("ACL_INVALID_SCOPE", scope=scope))

            scope_int = acl_scope_map[scope]

        # Validate the given actions
        if actions:
            if type(actions) != list:
                raise ACLException(C.make_error("ATTRIBUTE_INVALID", "actions", type=list.__name__))
            else:
                self.__check_actions(actions)

        # Try to find role-acl with the given ID.
        acl = None
        role = None
        for _aclrole in self.acl_roles:
            for _acl in self.acl_roles[_aclrole]:
                if _acl.id == acl_id:
                    acl = _acl
                    role = self.acl_roles[_aclrole]
                    break

        if acl:

            # Check that we do not point to ourselves
            if use_role and use_role == role.name:
                raise ACLException(C.make_error("ROLE_CANNOT_POINT_TO_ITSELF"))

            # Update the priority
            if priority:
                acl.set_priority(priority)

            # Let this acl point to a role
            if use_role:
                acl.clear_actions()
                acl.use_role(use_role)

            elif actions:

                # Update the acl actions
                if actions:
                    acl.clear_actions()
                    for action in actions:
                        acl.add_action(action['topic'], action['acls'], action['options'])

            # Update the scope value.
            if scope:
                acl.set_scope(scope_int)
            self.check.cache_clear()
        else:
            raise ACLException(C.make_error("ACL_NOT_FOUND"))

    @Command(needsUser=True, __help__=N_("Remove defined role-acl by ID."))
    def removeRoleACL(self, user, role_id):
        """

        Removes a defined role ACL by its id.

        (You can use getACLRoles() to list the role-acl IDs)

        ============== =============
        Key            Description
        ============== =============
        role_id        The ID of the role-acl to remove.
        ============== =============
        """

        # Check permissions
        if not self.check(user, '%s.acl' % self.env.domain, 'w', None, self.base):
            raise ACLException(C.make_error("PERMISSION_REMOVE", target=self.base))

        # Try to find role-acl with the given ID.
        for _aclrole in self.acl_roles:
            for _acl in self.acl_roles[_aclrole]:
                if _acl.id == role_id:
                    self.acl_roles[_aclrole].remove(_acl)
                    self.check.cache_clear()
                    return

        raise ACLException(C.make_error("ROLE_NOT_FOUND", role=role_id))

    @Command(needsUser=True, __help__=N_("Remove a defined acl-role by name"))
    def removeRole(self, user, rolename):
        """
        Removes a defined role by its name.

        ============== =============
        Key            Description
        ============== =============
        rolename       The name of the role.
        ============== =============
        """

        # Check permissions
        if not self.check(user, '%s.acl' % self.env.domain, 'w', None, self.base):
            raise ACLException(C.make_error("PERMISSION_REMOVE", target=self.base))

        # Try to find role-acl with the given ID.
        self.remove_role(rolename)
