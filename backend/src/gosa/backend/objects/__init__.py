# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

"""
Object abstraction
==================

Basic usage
-----------

The object abstraction module allows to access managed-information in an object oriented way.

You can get an object instance like this:

>>> from gosa.backend.objects import ObjectFactory
>>> person = f.getObject('User', "cn=Cajus Pollmeier,ou=people,ou=Technik,dc=gonicus,dc=de")

and then you can access, update and persist values like this:

>>> print person->sn
>>> print person->givenName
>>> person->sn = "New Surname"
>>> person->givenName = "Cajus"
>>> person->commit()
>>> person->close()

... or call object methods:

>>> person->notify(u"Shutdown of your client", u"Please prepare yourselves for a system reboot!")

... create new users:

>>> person = f.getObject('User', u'ou=people,dc=gonicus,dc=de', mode="create")
>>> person.uid = u"..."
>>> person.sn = u"..."
>>> person.givenName = u"..."
>>> person.commit()

... or add and remove extension:

>>> person = f.getObject('PosixUser', u'cn=Klaus Mustermann,ou=people,dc=gonicus,dc=de', mode="extend")
>>> person->homeDirectory = u"..."
>>> person->commit()

>>> person = f.getObject('PosixUser', u'cn=Klaus Mustermann,ou=people,dc=gonicus,dc=de')
>>> person->retract()

(Each object modification sends an event, with the related action and the objects uuid. These action
can then be caught later to perform different tasks, e.g. remove the mail-account from the server when
a Mail extension is removed)


How does it work - XML definition for objects
--------------------------------------------------

What properties are managed and how they are managed is defined in a set of XML files.
Each of these XML files can contain one or more object definition, you can find
them here ``gosa/backend/data/objects/``.

An object definition consist of the following information:

=================== ===========================
Name                Description
=================== ===========================
Name                The Name of the object
Description         A description
DisplayName         A display name for the object.
Backend             A backend which defines which storage backend is used to persist the data
BackendParameters   A list parameters for the backend.
Attributes          Attributes that are provided by this object
Methods             Methods that can be called on object instances
Container           A list of potential sub-objects this object can contain
Extends             Another objects name that we can extend. E.g. PosixUser can extend a User object
BaseObject          Defines this object as root object. E.g. User is a base object
FixedRDN            A RDN. For objects that are bound to a specific name. E.g. PeopleContainer (ou=people)
RequiresExtension   Defines a list of required extensions
ExtensionConditions A condition that must be true to enable a certain extension (uses the same structure as the validators)
=================== ===========================


XML definition of objects in detail
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. warning::
    We try to keep this documentation up to date, but at the moment the
    definition
    changes frequently.


A minimum example
~~~~~~~~~~~~~~~~~

All starts with an ``<Object>`` tag which introduces a new object, this
``<Object>`` tag must contain at least a ``<Name>``, a ``<Description>``, a ``<DisplayName>`` and a
``<Backend>`` tag. The name and the description are self-explaining.
The default-backend specifies which backend has to be used as default, for example
a LDAP or a MySQL backend - There may be more depending on your setup.

Backends are storage points for objects, they take care of caching,
loading and saving of objects and their attributes from different stores e.g. MySQL
or LDAP.

Here is a minimum configuration for an object. It does not have any
methods nor attributes:

.. code-block:: xml

    <?xml version="1.0" encoding="UTF-8"?>
    <Objects xmlns="http://www.gonicus.de/Objects">
        ...
        <Object>
            <Name>Dummy</Name>
            <DisplayName>A dummy</DisplayName>
            <Description>A dummy class</Description>
            <Backend>LDAP</Backend>
        </Object>
        ...
    </Objects>


Some optional properties added
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Here is a more complete example which include some optional values, but still
lacks attribute and method definitions:

.. code-block:: xml

    <?xml version="1.0" encoding="UTF-8"?>
    <Objects xmlns="http://www.gonicus.de/Objects">
        ...
        <Object>
            <Name>User</Name>
            <DisplayName>A dummy</DisplayName>
            <Description>User class</Description>
            <Backend>LDAP</Backend>

            <Container>
                <Type>Something</Type>
            </Container>
            <Extends>Base</Extends>
            <BaseObject>false</BaseObject>
        </Object>
        ...
    </Objects>

As you can see, three more tags were introduced here.

A ``<Container>`` tag which specifies for which objects we are a container.
For example an ``OrganizationalUnit`` is a container for ``PeopleContainer`` and ``GroupContainer`` objects.
In this example we could place ``Something`` objects under ``User`` objects.

A ``User`` object may have extensions like mail, posix, samba, ...  which can be added to or
removed from our object dynamically.
To be able to identify those addable extension we have the ``<Extends>`` tag, it specifies
which objects could be added to our object as extension.

The ``<BaseObject>`` tag, defines our object as root object, (if set to true) it cannot be attached
to some other objects, like described above in the ``<Extends>`` tag.


With the above example we can now instantiate a ``User`` object, it has no attributes
nor methods, but we could add a ``PosixUser`` and a ``Mail`` extension to it.


Adding attributes and their in- and out-filters
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To be able to store a users name or its postal address we need to define object-attributes.

Attributes can be access easily like this:

>>> print person->givenName

or can be set this way.

>>> person->postalAddress = "Herr Musterman\\n11111 Musterhausen\\nMusterstr. 55"

Here is a minimum example of an attribute:

.. code-block:: xml

    <?xml version="1.0" encoding="UTF-8"?>
    <Objects xmlns="http://www.gonicus.de/Objects">
        ...
        <Object>
            <Name>User</Name>
            <DisplayName>User</DisplayName>
            <Description>User</Description>
            <Backend>LDAP</Backend>
            ...
            <Attributes>
                <Attribute>
                    <Name>sn</Name>
                    <Description>Surname</Description>
                    <Type>String</Type>
                </Attribute>
            </Attributes>
            ...
        </Object>
    </Objects>

The above definition creates an attribute named ``sn`` which is
stored in the LDAP backend. If you want to store this attribute in another Backend, then
you can specify it explicitly like this:

.. code-block:: xml

    <?xml version="1.0" encoding="UTF-8"?>
    <Objects xmlns="http://www.gonicus.de/Objects">
        ...
        <Object>
            ...
            <Backend>LDAP</Backend>
            ...
            <Attributes>
                <Attribute>
                    <Name>sn</Name>
                    <Description>Surname</Description>
                    <Backend>LDAP</Backend>
                    <Type>String</Type>
                </Attribute>
            </Attributes>
            ...
        </Object>
    </Objects>


Attribute definition can contain the following tags, including optional:

=============== =========== ===========================
Name            Optional    Description
=============== =========== ===========================
Name            No          The attributes name.
Description     No          A short description for the attribute.
DependsOn       Yes         A list of attributes that depends on this attribute.
Backend         Yes         The backend to store this attribute.
Type            No          A simple string which defines the attributes syntax, e.g. String.
BackendType     Yes         Some attributes use a different type to be stored the backend.
Validators      Yes         A validation rule.
InFilter        Yes         A filter which is used to read the attribute from the backend.
OutFilter       Yes         A filter which is used to store the attribute in the backend.
MultiValue      Yes         A boolean flag, which marks this value as multiple value.
Readonly        Yes         Marks the attribute as read only.
Mandatory       Yes         Marks the attribute as mandatory.
Unique          Yes         Marks the attribute as system-wide unique.
Foreign         Yes         This Attribute is part of another object.
References      Yes         This Attribute contains references to other object that need to be updates, when the referenced value changes
=============== =========== ===========================

Here is an explanation of the simple properties above, the complex properties like ``Validators``,
``InFilter`` and ``OutFilter`` are described separately, later.

The tag ``<DependsOn>`` specifies a list of attributes that are related to the current attribute.
For example, the attribute 'cn' (common name) for a user is a combination of ``givenName`` and
``sn``, whenever you modify the users sn, you've to update the value of the ``cn`` attribute too.
If you now add ``cn`` to the ``<Depends>`` tag of the ``sn`` and ``givenName`` attributes, then
each modification of sn and givenName will mark the attribute cn as modified and thus forces it
to be saved again. (How sn and givenName are combined into the cn attribute will be described later
when the in- and out-filters are described).

With ``<Backend>`` you can specify another backend then defined in the ``<Object>s
<Backend>`` tag.

The ``<Type>`` specifies which syntax this attribute has, here is the list of the default types:

   * Boolean: bool
   * String: unicode
   * Integer: int
   * Timestamp: time.time
   * Date: datetime.date
   * Binary

An attribute may have multiple values, for example you can have multiple phone numbers or mail addresses.
If you want an attribute to be multi value then just add the ``<MultiValue>`` tag and set it to true.

To create a read only attribute add the tag ``<Readonly>`` and set it to true.

If the attribute is required then you should add the ``<Mandatory>`` flag and set it
to true.

If the attribute contains references to other object, e.g a ``PosixGroup`` contains a list of ``uid`` values,
you have to make sure that the reference does not get lost if a user uid gets changed. Just add

.. code-block:: xml

    <References>
        <Reference>
            <Object>PosixUser</Object>
            <Attribute>uid</Attribute>
        </Reference>
    </References>


Writing attribute validators
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can use validators to check the value of an attribute.

Validators are defined in an ``<Validators>`` tag using either the ``<Condition>`` or the ``<ConditionOperator>`` tag.
The ``<Condition>`` tag is a single check like shown below, where ``<ConditionOperator>`` are combined conditions:

A simple single condition:

.. code-block:: xml

    <Validators>
        <Condition>
            <Name>stringLength</Name>
            <Param>4</Param>
            <Param>20</Param>
        </Condition>
    </Validators>

This example uses the stringLength condition with a set of parameters to check the values length.
Right now there is a very limited set of conditions available - but there will be more.

.. hint::

    You can add the object instance as parameter to the condition by using the reserved keyword ``__self__``
    as parameter. e.g.``<Param>__self__</Param>``

You can also define more complex validators like this (This example does not make much sense!):

.. code-block:: xml

        <Validators>
            <ConditionOperator>
                <Operator>or</Operator>
                <LeftConditionChain>
                    <Condition>
                        <Name>stringLength</Name>
                        <Param>5</Param>
                        <Param>10</Param>
                    </Condition>
                </LeftConditionChain>
                <RightConditionChain>
                    <Condition>
                        <Name>Equals</Name>
                        <Param>Heh?</Param>
                        <Param>%{sn}s</Param>
                    </Condition>
                </RightConditionChain>
            </ConditionOperator>
        </Validators>


The above example is valid, when the value has a length of 5-10 characters OR the value of sn is 'Heh?'.

Instead of ``or`` can also ``and`` be used.

And you can even stack ``<ConditionOperator>`` as deep as you want:

.. code-block:: xml

            <ConditionOperator>
                <Operator>or</Operator>
                <LeftConditionChain>
                    <ConditionOperator>
                        <Operator>and</Operator>
                        <LeftConditionChain>
                            <ConditionOperator>...</ConditionOperator>
                        </LeftConditionChain>
                        <RightConditionChain>
                            <ConditionOperator>...</ConditionOperator>
                        </RightConditionChain>
                    </ConditionOperator>
                </LeftConditionChain>
                <RightConditionChain>
                    <ConditionOperator>
                        <Operator>and</Operator>
                        <LeftConditionChain>
                            <Condition>...</Condition>
                        </LeftConditionChain>
                        <RightConditionChain>
                            <Condition>...</Condition>
                        </RightConditionChain>
                    </ConditionOperator>
                </RightConditionChain>
            </ConditionOperator>


Creating in and out filters
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Normally attributes are stored and read from the defined backend directly without any modification.
If you want to manipulate the value before it gets saved or read, then you've to use in- and out-filters.

This is useful for values like passwords or values that have to be converted before they get saved.

For example you can generate a hash out of a text-password instead of storing the password in clear-text.
Or you could generate the cn (common name) for a user out of his sn and givenName, automatically.

The in-filters are executed when the objects gets loaded and the out-filters when the object is saved.

Here is an example out-filter which combines ``sn`` and ``givenName`` in the attribute cn:

.. code-block:: xml

    <Attribute>
        <Name>cn</Name>
        ...
        <OutFilter>
            <FilterChain>
                <FilterEntry>
                    <Filter>
                        <Name>Clear</Name>
                    </Filter>
                </FilterEntry>
                <FilterEntry>
                    <Filter>
                        <Name>ConcatString</Name>
                        <Param>%(givenName)s %(sn)s</Param>
                        <Param>left</Param>
                    </Filter>
                </FilterEntry>
            </FilterChain>
        </OutFilter>

Out-filters are defined in the ``<OutFilter>`` tag and in-filters in
the ``<InFilter>`` tag of the ``<Attribute>``,
the filter definition is then placed inside a ``<FilterChain>`` tag.
Both definitions, for in- and out filter, are created in the same way.

The ``<FilterChain>`` tag inside of the ``<In/OutFilter>`` tag contains
various ``<FilterEntry>`` tags, which will be executed
sequentially, when the filter is executed.

The example above will do the following when the property cn gets saved:

 * Clear the contents of the attribute cn
 * Add the value ``"%(givenName)s %(sn)s"`` to the left of the current value of cn while the ``%(..)s`` are replaced by real values.

Another filter action could be, to change an attributes name during the filter execution:

.. code-block:: xml

    <Attribute>
        <Name>cn</Name>
        ...
        <InFilter>
            <FilterChain>
                <FilterEntry>
                    <Filter>
                        <Name>Target</Name>
                        <Param>commonName</Param>
                    </Filter>
                </FilterEntry>
            </FilterChain>
        </InFilter>

        <OutFilter>
            <FilterChain>
                <FilterEntry>
                    <Filter>
                        <Name>Target</Name>
                        <Param>cn</Param>
                    </Filter>
                </FilterEntry>
            </FilterChain>
        </OutFilter>

In the above example we change the attributes name from ``cn`` to
``commonName`` in the in-filter and back to ``cn`` in the out-filter.
This enables us to access the value like this:

>>> print person->commonName

while the attribute is still stored as ``cn`` due to the out-filter definition.

You can also add conditions to your filters like shown below:

.. code-block:: xml

    <FilterChain>
        <FilterEntry>
            <Choice>
                <When>
                    <ConditionChain>
                        <Condition>
                            <Name>stringLength</Name>
                            <Param>0</Param>
                            <Param>5</Param>
                        </Condition>
                    </ConditionChain>
                    <FilterChain>
                        <FilterEntry>
                            <Filter>
                                <Name>Clear</Name>
                            </Filter>
                        </FilterEntry>
                    </FilterChain>
                    <Else>
                        <FilterChain>
                            <FilterEntry>
                                <Filter>
                                    <Name>ConcatString</Name>
                                    <Param>Value is longer than 5 chars: </Param>
                                    <Param>left</Param>
                                </Filter>
                            </FilterEntry>
                        </FilterChain>
                    </Else>
                </When>
            </Choice>

If the value is smaller then 6 chars it will be cleared, if it is greater then 6 chars a string will be appended to the left.

.. warning::
    Once we've more operators, filters and so on, we should generate better examples.
    The following example does not work at the moment due to missing comparators.

Another example could be to convert a list of flags into different boolean values, like this.

Lets say we've a given flag list which looks like this:

>>>  flagList = [LVM]

Where L stands for Lookup ...

While loading the flagList we can convert this string flag list into real
boolean value like this:

.. code-block:: xml

    <Attribute>
        <Name>Flag_Lookup</Name>
        ...
        <InFilter>

            <FilterChain>
                <FilterEntry>
                    <Choice>
                        <When>
                            <ConditionChain>
                                <Condition>
                                    <Name>RegEx</Name>
                                    <Param>%(flagList)s</Param>
                                    <Param>/[L]/i</Param>
                                </Condition>
                            </ConditionChain>
                            <FilterChain>
                                <FilterEntry>
                                    <Filter>
                                        <Name>SetValue</Name>
                                        <Param>true</Param>
                                        <Param>Boolean</Param>
                                    </Filter>
                                </FilterEntry>
                            </FilterChain>
                            <Else>
                                <FilterChain>
                                    <FilterEntry>
                                        <Filter>
                                            <Name>SetValue</Name>
                                            <Param>false</Param>
                                            <Param>Boolean</Param>
                                        </Filter>
                                    </FilterEntry>
                                </FilterChain>
                            </Else>
                        </When>
                    </Choice>

And then we could define an out filter which looks like this, to store the boolean values as string again:

.. code-block:: xml

    <Attribute>
        <Name>flagList</Name>
        ...
        <OutFilter>
            <FilterChain>
                <FilterEntry>
                    <Filter>
                        <Name>Clear</Name>
                    </Filter>
                </FilterEntry>
                <FilterEntry>
                    <Choice>
                        <When>
                            <ConditionChain>
                                <Condition>
                                    <Name>Equals</Name>
                                    <Param>%(Flag_Lookup)s</Param>
                                    <Param>true</Param>
                                    <Param>Boolean</Param>
                                </Condition>
                            </ConditionChain>
                            <FilterChain>
                                <FilterEntry>
                                    <Filter>
                                        <Name>ConcatString</Name>
                                        <Param>L</Param>
                                        <Param>left</Param>
                                    </Filter>
                                </FilterEntry>
                            </FilterChain>
                        </When>
                    </Choice>
                </FilterEntry>
                ... add here the other flag checks...
                <FilterEntry>
                    <Filter>
                        <Name>ConcatString</Name>
                        <Param>[</Param>
                        <Param>left</Param>
                    </Filter>
                </FilterEntry>
                <FilterEntry>
                    <Filter>
                        <Name>ConcatString</Name>
                        <Param>]</Param>
                        <Param>right</Param>
                    </Filter>
                </FilterEntry>

When saving the flagList again, it will be created out of the flag states.


Introduction of methods
~~~~~~~~~~~~~~~~~~~~~~~

We can also define methods for objects within the XML definition, these methods can
then be called directly on an instance of these object:

>>> person->notify(u"Shutdown of your client", u"Please prepare yourselves for a system reboot!")

Here is the XML code for the above method call, all other object tags are removed for better reading:

.. code-block:: xml

    <?xml version="1.0" encoding="UTF-8"?>
    <Objects xmlns="http://www.gonicus.de/Objects">
        ...
        <Object>
            <Name>User</Name>
            ...
            <Methods>
                <Method>
                    <Name>notify</Name>
                    <MethodParameters>
                        <MethodParameter>
                            <Name>notify_title</Name>
                            <Type>String</Type>
                            <Default>Notification</Default>
                        </MethodParameter>
                        <MethodParameter>
                            <Name>notify_message</Name>
                            <Type>String</Type>
                            <Required>true</Required>
                        </MethodParameter>
                    </MethodParameters>
                    <Command>notifyUser</Command>
                    <CommandParameters>
                        <CommandParameter>
                            <Value>%(uid)s</Value>
                        </CommandParameter>
                        <CommandParameter>
                            <Value>Der angegebene Titel war: %(notify_title)s</Value>
                        </CommandParameter>
                        <CommandParameter>
                            <Value>%(notify_message)s</Value>
                        </CommandParameter>
                    </CommandParameters>
                </Method>
            </Methods>
            ...
        </Object>
    </Objects>

Methods are introduced by a ``<Method>`` tag and are grouped within the ``<Methods>`` tag.
You can have multiple methods if you want.

Methods consist of four tags:

    * The ``<Name>`` tag which specifies the name of the method.
    * A ``<MethodParameters>`` tag, which contains a list of parameters to this method.
    * A ``<Command>`` tag, which represents to GOsa command we want to call.
    * The ``<CommandParameters>`` tag, defines a list parameters we want to pass to the
      GOsa command call.

The above definition creates a method named notify which looks like this:

>>> def notify(notify_message, notify_title = u"Notification"):

If you call this method like this:

>>> person->notifyUser("Warning", "Restart imminent!")

it will invoke a GOsa command named notifyUser with this parameters:

>>> notifyUser(u"user1", u"Der angegebene Titel war: Warning", u"Restart imminent!")

As you can see, you cannot freely create whatever method you want, you can just call
existing GOsa commands and adjust their arguments.

You can use placeholders using ``%(property_name)s``, to dynamically fill in
command parameters, like done for the first ``<CommandParameter>``.

.. code-block:: xml

    <CommandParameter>
        <Value>%(uid)s</Value>
    </CommandParameter>

or you can use it to refer to the method-parameters like this:

.. code-block:: xml

    <CommandParameter>
        <Value>Placeholder: %(notify_message)s</Value>
    </CommandParameter>

You can use all the attribute names you have defined and additionally all the
parameters of the method as placeholders.


Relations between objects
~~~~~~~~~~~~~~~~~~~~~~~~~

Objects can be related to each other, e.g. a ``PosixGroup`` contains a list of ``PosixUser`` objects.
Usually this is defined by a list of foreign keys in a multi-valued attribute of the group.
Those keys can either by a DN or an attribute value which is unique when you know the related objects type
(e.g. the RDN).
So in the backend the relation is store in the group, the related object does not store a relation to the group its in.

In GOsa those relations are bi-directional by using a "virtual" attribute in the object, which contains the group relation.
This attribute is filled at load time and not persisted in any way. This behaviour makes it possible to edit the
relationship between the group and the user on both ends, e.g. removing the user by editing the group or
removing the group by editing the user.

Of course there are some things that need to be taken care of to keep those relations up-to-date. The main problem is
that the attributes value of the related object might change. GOsa needs to update this change in the group attribute
to keep the relation intact.

.. code-block:: xml
    :caption: Example for a PosixGroup related to PosixUsers

     <BackendParameters>
      ...
      <Backend memberUid="PosixUser:uid,">ObjectHandler</Backend>
    </BackendParameters>
    ...
    <Attribute>
        <Name>memberUid</Name>
        <Description>A list of member-uids</Description>
        <Type>String</Type>
        <MultiValue>true</MultiValue>
        <Mandatory>false</Mandatory>
        <References>
          <Reference>
            <Object>PosixUser</Object>
            <Attribute>uid</Attribute>
          </Reference>
        </References>
        <Validators>
          <Condition>
            <Name>ObjectWithPropertyExists</Name>
            <Param>PosixUser</Param>
            <Param>uid</Param>
          </Condition>
        </Validators>
    </Attribute>

.. code-block:: xml
    :caption: Example of a PosixUser related to a PosixGroup

     <BackendParameters>
      ...
      <Backend groupMembership="PosixGroup:cn,memberUid=uid">ObjectHandler</Backend>
    </BackendParameters>
    ...
    <Attribute>
        <Name>groupMembership</Name>
        <Description>A list on posix-group names this user is member of</Description>
        <Type>String</Type>
        <Backend>ObjectHandler</Backend>
        <MultiValue>true</MultiValue>
        <Validators>
          <Condition>
            <Name>ObjectWithPropertyExists</Name>
            <Param>PosixGroup</Param>
            <Param>cn</Param>
          </Condition>
        </Validators>
    </Attribute>

There are two important things that need to be defined and take care of different aspects of the relation.
The most important thing (the relation itself) is defined in the backend parameters for the ``ObjectHandler``
backend. The ``ÒbjectHandler``'s backend only purpose is to keep track of the informations about relations.

So in the group definition we have ``memberUid="PosixUser:uid,"``. The attribute name ``memberUid`` defines
the local attribute where the entries to the related objects can be found. The attributes value ``PosixUser:uid,``
defines the content of the ``memberUid`` attribute. In this case it is a relation to the ``uid`` attribute of
``PosixUser`` object.

In the user definition we find the other side of the relation:
``groupMembership="PosixGroup:cn,memberUid=uid"``. Again the attribute name defines the local attribute, where the
entries to the related objects can be found. In the example the ``groupMembership`` attribute can have multiple
relations to ``PosixGroup`` objects (as the user can be part of multiple groups at the same time). Please note that
``groupMembership`` only purpose is to hold the references to the groups. It is the "virtual" attribute mentioned
some lines above. The "virtual" behaviour is enabled by the ``<Backend>ObjectHandler</Backend>`` definition.
And the attribute value defines the comma-separated, local and remote content of the related attributes.
Which means in the local ``groupMembership`` we find a list of ``cn`` values of ``PosixGroup`` objects
and in the remote ``memberUid`` attribute we find a list of ``uid`` values of ``PosixUser`` attributes.

The last thing we need to take care of is the change of ``uid`` values of ``PosixUser`` objects.
If we do not track those changes the group would contain references to not existing ``uid``'s.
So the ``memberUid`` attribute needs to know when it has to update its references, this is defined
by the ``References`` attribute:

.. code-block:: xml

    <References>
        <Reference>
            <Object>PosixUser</Object>
            <Attribute>uid</Attribute>
        </Reference>
    </References>

Is this case we tell GOsa to update the ``memberUid`` values, whenever a ``uid`` value of one of the entries changes.

**Let the object know when it got removed from a group**

In the example above, we used a "virtual" attribute to keep track of the object->group relation. As mentioned this
attribute is non-persistent, as it only gets filled when you load an object. There might be use cases where you need
to persist this relation end-point in a backend. In those cases the object needs to be informed when it got removed
from or added to a group, in order to update its group attribute relation.

As an example we can think of a group of ``ForemanHost``'s that are part of a ``ForemanHostGroup``.
The ``ForemanHost`` needs to know its group relationship as that has to be persisted in the foreman backend.

As both mentioned object are extensions of base objects (Device->ForemanHost, GroupOfNames->ForemanHostGroup)
the definitions get a little bit more complicated.

.. code-block:: xml
    :caption: Excerpt from the GroupOfNames definition

    <BackendParameters>
      ...
      <Backend member="*:dn,">ObjectHandler</Backend>
    </BackendParameters>

    <Attribute>
        <Name>member</Name>
        <Description>RFC2256: member of a group</Description>
        <Type>UnicodeString</Type>
        <MultiValue>true</MultiValue>
        <Mandatory>true</Mandatory>
        ...
        <References>
          <Reference>
            <Object>*</Object>
            <Attribute>dn</Attribute>
          </Reference>
        </References>
        ...
      </Attribute>

The ``GroupOfNames`` member attribute contains a list of ``DN`` values of any type of object.

.. code-block:: xml
    :caption: Excerpt from the ForemanHost definition

    <BackendParameters>
        ...
        <Backend groupMembership="GroupOfNames:dn,member=dn">ObjectHandler</Backend>
    </BackendParameters>
    ...
    <Attribute>
        <Name>groupMembership</Name>
        <Description>Assigned host group</Description>
        <Type>String</Type>
        <Backend>ObjectHandler</Backend>
        ...
        <UpdateHooks>
          <UpdateHook>
            <Object>ForemanHostGroup</Object>
            <Attribute>member</Attribute>
          </UpdateHook>
        </UpdateHooks>
    </Attribute>

So regarding our use case the ``groupMembership`` attribute needs to be informed about changes in the relation of
its group membership to be able to forward those changes to the *foreman* backend. As we see the attribute
is still "virtual" and not related to the *foreman* backend, we come to that later.
To get the information about the change we define an ``UpdateHook``, which will be executed every time the
content of the ``member`` attribute of a ``ForemanHostGroup`` has changed.

.. NOTE::

    To be precise: the ``member``attribute is actually defined in the base type
    ``GroupOfNames`` of the extension ``ForemanHostGroup``. But we are not interested in changes
    if the ``member`` attribute of ``GroupOfNames`` that are not extended by ``ForemanHostGroup``'s.

So for now we have an updated ``groupMembership`` which contains a ``DN`` of a ``ForemanHostGroup`` (or
is empty). The relations in the *foreman* backend need a ``foremanGroupId``:

.. code-block: xml
    :caption: Relevant parts of the ForemanHostGroup definition

    <BaseObject>false</BaseObject>
    ...
    <Attribute>
        <Name>foremanGroupId</Name>
        <Description>ID used in foreman to identify the hostGroup</Description>
        <Type>String</Type>
        <Mandatory>true</Mandatory>
    </Attribute>
    ...
    <Extends>
        <Value>GroupOfNames</Value>
    </Extends>

We need to map the ``DN`` to a ``foremanGroupId`` and write that to the ``hostgroup_id`` attribute of the ``ForemanHost``.

.. code-block:: xml
    :caption: Excerpt from the ForemanHost definition


    <Attribute>
        <Name>hostgroup_id</Name>
        <Description>ID of the hostgroup this host is part of</Description>
        <Type>String</Type>
        <BackendType>Integer</BackendType>
        <Backend>Foreman</Backend>
        <DependsOn>
          <Attribute>groupMembership</Attribute>
        </DependsOn>
        <InFilter>
          <FilterChain>
            <FilterEntry>
              <Filter>
                <Name>IntegerToString</Name>
              </Filter>
            </FilterEntry>
            <FilterEntry>
              <Filter>
                <Name>CopyForeignValueTo</Name>
                <Param>ForemanHostGroup</Param>
                <Param>foremanGroupId</Param>
                <Param>dn</Param>
                <Param>groupMembership</Param>
              </Filter>
            </FilterEntry>
          </FilterChain>
        </InFilter>
        <OutFilter>
          <FilterChain>
            <FilterEntry>
              <Filter>
                <Name>CopyForeignValueFrom</Name>
                <Param>ForemanHostGroup</Param>
                <Param>foremanGroupId</Param>
                <Param>dn</Param>
                <Param>groupMembership</Param>
              </Filter>
            </FilterEntry>
          </FilterChain>
        </OutFilter>
      </Attribute>

We use In- and Out-Filters in the ``hostgroup_id`` attribute to handle that. This attribute is written to / read from
the *foreman* backend. When a ``ForemanHost`` object gets opened the in-filter chain converts the value from integer
to string, retrieved the corresponding DN of the ``ForemanHostGroup`` with the given id and writes that value to
the ``groupMembership``.

The out-filter goes the other way around. When a ``ForemanHost`` object is saved it reads the DN from the ``groupMembership``
attribute, converts is to the corresponding  ``hostgroup_id`` and sends that value to the *foreman* backend.

"""
__import__('pkg_resources').declare_namespace(__name__)

from gosa.backend.objects.proxy import ObjectProxy, ProxyException
from gosa.backend.objects.factory import ObjectFactory
from gosa.backend.objects.object import ObjectException, ObjectChanged

SCOPE_BASE = 0
SCOPE_ONE = 1
SCOPE_SUB = 2
