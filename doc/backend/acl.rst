.. _acl-handling:

ACL handling
============

This chapter details the way access control is handled within the GOsa core
engine, from the gosa-shell and from the command line using the acl-admin.py tool.

First of all, here is a small graphic that shows how the Acl-objects are used internally in the agent.

How an ACL assigment could look like
------------------------------------

>>> ACLSet
>>>  |-> ACL
>>>  |-> ACL
>>>  |-> ACL -> ACLRole (test1)
>>>  |-> ACL

>>> ACLRole (test1)
>>>  |-> ACLRoleEntry
>>>  |-> ACLRoleEntry


--------

Internal ACL handling - A short explanation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This section describes how ACLs are defined and used internally in the GOsa core, a normal user will not use ACLs this way, but I guess it helps understanding how things work. The use of the acl-admin.py tool and the use of acls in the gosa-shell will follow a few lines below.

As the small graph above shows, ACLs are represented by a set of classes. One of these is the ``ACLSet`` class, which
combines a list of ``ACL`` entries into a set of effective ACLs.

The ACLSet has a base property which specifies the base, this set of
acls is valid for. E.g. dc=example,dc=net

::

>>> aclset = ACLSet("dc=example,dc=de")
    

The ``ACL`` object describes a set of actions/objects/topics that can be accessed in a given scope, by a list of users.

::

>>> acl = ACL(scope=ACL.ONE)
>>> acl.set_members([u'tester1', u'tester2'])
>>> acl.add_action('^org\.clacks\.event\.ClientLeave$', 'rwx')
>>> acl.set_priority(100)


The classes ``ACLRole`` and ``ACLRoleEntry`` allow to build up roles that can then be used in ACLSets to 
simplify the use ACL that are frequently used.

::

>>> aclrole = ACLRole('role1')
>>> acl = ACLRoleEntry(scope=ACL.SUB)
>>> acl.add_action('^org\.clacks\.event\.ClientLeave$', 'rwx')
>>> aclrole.add(acl)


Once you've created an ACLSet or ACLRole object and want to activate it, you've to attach it to the ACLResolver object.

::

>>> resolver = PluginRegistry.getInstance("ACLResolver")
>>> resolver.add(aclset1)
>>> resolver.add(role1)

Now you can check for permissions like this:

::

>>> resolver = PluginRegistry.getInstance("ACLResolver")
>>> resolver.check('user1', 'org.clacks.event.ClientLeave', 'x')


ACLs in detail
^^^^^^^^^^^^^^

As the explanation above shows how acls are used, this section explains each option in detail. 

**ACLSet**

The ACLSet is initialized with a base parameter::

>>> aclset = ACLSet("dc=example,dc=net")

The base given for an ACLSet specifies which objects are affected by the ACLSet.
All objects, beneath and including "dc=exmaple,dc=net", will be affected by the acl ACLSet above.

If you want to set an ACL for a single object, e.g. a single User, then you've to use the users dn for the ACLset.

ACLSet can contain multiple ACL objects::

>>> aclset.add(acl1)
>>> aclset.add(acl2)
>>> aclset.add(acl3)

And you can remove ACLs in different ways:

>>> aclset.remove_acl(acl_object)
>>> aclset.remove_acls_for_user(user_name)



**ACL** 

ACL objects contain the real acl definitions that will later by applied to a base using the ACLSet.

**ACL - scopes**

They are initialized by a scope parameter, which defines how the containing acls take affect::

>>> acl = ACL(scope=ACL.ONE)

Here is a list of all available scopes::

    Scope values - internal use - agent-core:

        * ``ACL.ONE`` for one level.
        * ``ACL.SUB`` for all sub-level. This can be revoked using ``ACL.RESET``
        * ``ACL.RESET`` revokes the actions described in this ``ACL`` object for all sub-levels of the tree.
        * ``ACL.PSUB`` for all sub-level, cannot be revoked using ``ACL.RESET``

    Scope values - external use, e.g. when executing commands using the gosa-shell or from the backend-acl.py tool:

        * ``"one"`` for one level.
        * ``"sub"`` for all sub-level. This can be revoked using ``ACL.RESET``
        * ``"reset"`` revokes the actions described in this ``ACL`` object for all sub-levels of the tree.
        * ``"psub"`` for all sub-level, cannot be revoked using ``ACL.RESET``

The scope "one" or ACL.ONE used in the example above, will apply to the base we used in the ACLSet and all 
objects one level below to base. 

**ACL - members** 

>>> acl.set_members([u'tester1', u'tester2'])

ACL members can also contain regular expressions, like this:

>>> acl.set_members([u"user1", u"^user[0-9]*$"])

**ACL - actions**

The permission an ACL contains are defined in actions, each action contains a topic, a set of acls-flags and some optional options.

Here is an example which allows to (r)ead (w)rite and e(x)ecute the topic org.clacks.event.ClientLeave. 

>>> acl.add_action('^org\.clacks\.event\.ClientLeave$', 'rwx')
>>> acl.add_action(**Topic**, **permissions**, **options**)


**Topic**

Topics are defined as regular expressions, which gives a huge flexibility.

For example ``^clacks\.[^\.]*\.factory$`` would match for:
    * clacks.test.factory
    * clacks.hallo.factory
but not for:
    * clacks.factory
    * clacks.level1.level2.factory

Where ``^clacks\..*\.factory$`` matches for:
    * clacks.factory
    * clacks.level1.factory
    * clacks.level1.level2.factory


**Acl - flags**

The acl parameter describes the action we can perform on a given ``topic``.
Possible actions are:

    * r - Read
    * w - Write
    * c - Create
    * d - Delete
    * o - Onwer only, this acl affects only loggedin user itself.
    * m - Manager, this acl applies for the manager of on object.
    * s - Search - or beeing found
    * x - Execute
    * e - Receive event

The actions have to passed as a string, which contains all actions at once

>>> add_action(``topic``, "rwcdm", ``options``)


**Options**

Options are additional check parameters that have to be fullfilled to get this acl to match.

The ``options`` parameter is a dictionary which contains a key and a value for each additional option we want to check for, e.g. 

>>> add_action('topic', 'acls', {'uid': 'hanspeter', 'ou': 'technik'})

If you've got a user object (``user1``) as dictionary, then you can check permissions like this

>>> resolver.check('some.topic', 'rwcdm', user1)

The resolver will then check if the keys ``uid`` and ``ou`` are present in the user1 dictionary and then check if the values match.
If not all options match, the ACL will not match.

**Priority**

Priorities can be given from -100 up to 100, where -100 is the highest.

>>> acl.set_priority(100)


**Examples**

A simple acl defintion.

Add an acl for user 'tester1' and 'tester2' for one-level on base 'dc=example,dc=net' to topic org.clacks.event.notify with acls 'rwx':

>>> aclset = ACLSet("dc=example,dc=net")
>>> acl = ACL(scope=ACL.ONE)
>>> acl.set_members([u'tester1', u'tester2'])
>>> acl.add_action('^org\.clacks\.event\.notify$', 'rwx')
>>> acl.set_priority(100)
>>> aclset.add(acl)

You can also use regular expressions for topics:

>>> acl.add_action('^org\.clacks\.event\.[^\.]*$', 'rwx')
"[^\.]*" means everything one level


Remove all acls for user tester1:

>>> aclset.remove_acls_for_user('tester1')

Using a acl-role

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


Setting ACLs from the Clacks-shell
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Listing ACLs**

You can use the following command in the clacks shell to build up ACL defintions.
The schema is the same as describes above with slight differences.

List all defined ACLs, you can filter by base and topic.

>>> getACls(base='dc=gonicus,dc=de')
>>> getACls(topic=r'^com\.gonicus\.factory$')

List all defined roles

>>> getACLRoles()


**Adding ACLs**

>>> addACL('dc=gonicus,dc=de', 'sub', 0, [u'tester1'], [{'topic': r'^some\.topic.*$', 'acls': 'rwcdm'}])

or with some options:

>>> resolver.addACL('dc=gonicus,dc=de', 'sub', 0, [u'tester1'], [{'topic': r'^some\.topic.*$', 'acls': 'rwcdm', 'options': {'uid': '^u[0-9]'}}])

**Adding roles**

>>> addACLRole('role1')
>>> addACLtoRole('role1', 'sub', 0, {...})

**Removing an acl**

The id of an ACL entry can found in the ACL itself, just get all defined ACLSets and then interate through them 
and use the id of the ACL.

>>> removeACL(id)

**Removing a role**

>>> removeRole('role1')


ACLs using the acl_admin.py tool
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

List acls

>>> ./acl-admin list acls

Add acls to an object

>>> ./acl-admin add roleacl with-actions "name=TEST,dc=example,dc=net" 1 sub "^net\.example\.objects\.Group\..*$:s"

Add a new role

>>> ./acl-admin add role dc=example,dc=net TEST

Add acls to a role

>>> ./acl-admin add roleacl with-actions "name=TEST,dc=example,dc=net" 1 sub "^net\.example\.command\.core\.(getSessionUser|get_error|getBase|search|openObject|dispatchObjectMethod|setObjectProperty|closeObject|reloadObject)$:x"

>>> ./acl-admin add add roleacl with-actions "name=TEST,dc=example,dc=net" 1 sub "^net\.example\.command\.gosa\.(getTemplateI18N|getAvailableObjectNames|getGuiTemplates|getUserDetails|search|getObjectDetails|searchForObjectDetails|loadUserPreferences|saveUserPreferences)$:x"

Remove a role 

>>> ./acl-admin remove role "name=TEST,dc=example,dc=net"

Remove all acls from a base

>>> ./acl-admin remove acls "dc=example,dc=net"

Remove all acls from a role

>>> ./acl-admin remove roleacls "name=TEST,dc=example,dc=net"


.. automodule:: gosa.backend.acl
   :members:
