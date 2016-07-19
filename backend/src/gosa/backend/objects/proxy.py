# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

"""
Object Proxy
============

The object proxy sits on top of the :class:`gosa.backend.objects.factory:ObjectFactory`
and is the glue between objects that are defined via XML descriptions. The proxy should
be used to load, remove and modify objects.

Here are some examples:

    >>> obj = ObjectProxy(u"ou=people,dc=example,dc=net", "User")
    >>> obj.uid = "user1"
    >>> obj.sn = u"Mustermann"
    >>> obj.givenName = u"Eike"
    >>> obj.commit()

This fragment creates a new user on the given base.

    >>> obj.extend('PosixUser')
    >>> obj.homeDirectory = '/home/' + obj.uid
    >>> obj.gidNumber = 4711
    >>> obj.commit()

This fragment will add the *PosixUser* extension to the object, while

    >>> obj.get_extension_types()

will list the available extension types for that specific object.

"""
import pkg_resources
import re
import time
import zope.event
from lxml import etree
from ldap.dn import str2dn, dn2str
from logging import getLogger
from gosa.common import Environment
from gosa.common.utils import is_uuid, N_
from gosa.common.components import PluginRegistry
from gosa.common.error import GosaErrorHandler as C
from gosa.backend.exceptions import ACLException, ProxyException
from gosa.common.components.jsonrpc_utils import Binary
from io import StringIO

# Register the errors handled  by us
C.register_codes(dict(
    OBJECT_UNKNOWN_TYPE=N_("Unknown object type '%(type)s'"),
    OBJECT_EXTENSION_NOT_ALLOWED=N_("Extension '%(extension)s' not allowed"),
    OBJECT_EXTENSION_DEFINED=N_("Extension '%(extension)s' already there"),
    OBJECT_EXTENSION_DEPENDS=N_("Extension '%(extension)s' depends on '%(missing)s'"),
    PERMISSION_EXTEND=N_("No permission to extend %(target)s with %(extension)s"),
    OBJECT_NO_SUCH_EXTENSION=N_("Extension '%(extension)s' already retracted"),
    OBJECT_EXTENSION_IN_USE=N_("Extension '%(extension)s' is required by '%(origin)s'"),
    PERMISSION_RETRACT=N_("No permission to retract '%(extension)s' from '%(target)s'"),
    PERMISSION_MOVE=N_("No permission to move '%(source)s' to '%(target)s'"),
    OBJECT_HAS_CHILDREN=N_("Object '%(target)s' has children"),
    PERMISSION_REMOVE=N_("No permission to remove '%(target)s'"),
    PERMISSION_CREATE=N_("No permission to create '%(target)s'"),
    PERMISSION_ACCESS=N_("No permission to access '%(topic)s' on '%(target)s'"),
    OBJECT_UUID_MISMATCH=N_("UUID of base (%(b_uuid)s) and extension (%(e_uuid)s) differ")
    ))


class ObjectProxy(object):
    _no_pickle_ = True
    dn = None
    uuid = None
    __env = None
    __log = None
    __base = None
    __base_type = None
    __extensions = None
    __initial_extension_state = None
    __retractions = None
    __factory = None
    __attribute_map = None
    __method_map = None
    __acl_resolver = None
    __current_user = None
    __attribute_type_map = None
    __method_type_map = None
    __attributes = None
    __base_mode = None
    __property_map = None
    __foreign_attrs = None
    __all_method_names = None

    def __init__(self, _id, what=None, user=None):
        self.__env = Environment.getInstance()
        self.__log = getLogger(__name__)
        self.__factory = ObjectFactory.getInstance()
        self.__base = None
        self.__extensions = {}
        self.__initial_extension_state = {}
        self.__retractions = {}
        self.__attribute_map = {}
        self.__method_map = {}
        self.__current_user = user
        self.__acl_resolver = PluginRegistry.getInstance("ACLResolver")
        self.__attribute_type_map = {}
        self.__attributes = []
        self.__method_type_map = {}
        self.__property_map = {}
        self.__foreign_attrs = []
        self.__all_method_names = []

        # Do we have a uuid when opening?
        dn_or_base = _id
        if is_uuid(_id):
            index = PluginRegistry.getInstance("ObjectIndex")
            res = index.search({'uuid': _id}, {'dn': 1})
            if len(res) == 1:
                dn_or_base = res[0]['dn']
            else:
                raise ProxyException(C.make_error('OBJECT_NOT_FOUND', id=_id))

        # Load available object types
        object_types = self.__factory.getObjectTypes()

        base_mode = "update"
        base, extensions = self.__factory.identifyObject(dn_or_base)
        if what:
            if not what in object_types:
                raise ProxyException(C.make_error('OBJECT_UNKNOWN_TYPE', type=type))

            base = what
            base_mode = "create"
            extensions = []

        if not base:
            raise ProxyException(C.make_error('OBJECT_NOT_FOUND', id=dn_or_base))

        # Get available extensions
        self.__log.debug("loading %s base object for %s" % (base, dn_or_base))
        all_extensions = object_types[base]['extended_by']

        # Load base object and extensions
        self.__base = self.__factory.getObject(base, dn_or_base, mode=base_mode)
        self.__base.owner = self.__current_user
        self.__base.parent = self
        self.__base_type = base
        self.__base_mode = base_mode
        for extension in extensions:
            self.__log.debug("loading %s extension for %s" % (extension, dn_or_base))
            self.__extensions[extension] = self.__factory.getObject(extension, self.__base.uuid)
            self.__extensions[extension].dn = self.__base.dn
            self.__extensions[extension].parent = self
            self.__extensions[extension].owner = self.__current_user
            self.__initial_extension_state[extension] = True
        for extension in all_extensions:
            if extension not in self.__extensions:
                self.__extensions[extension] = None
                self.__initial_extension_state[extension] = False

        # Collect all method names (also not available due to deactivated extension)
        for obj in [base] + all_extensions:
            self.__all_method_names = self.__all_method_names + self.__factory.getObjectMethods(obj)

        # Generate method mapping
        for obj in [base] + extensions:
            for method in object_types[obj]['methods']:
                if obj == self.__base.__class__.__name__:
                    self.__method_map[method] = getattr(self.__base, method)
                    self.__method_type_map[method] = self.__base_type
                    continue
                if obj in self.__extensions:
                    self.__method_map[method] = getattr(self.__extensions[obj], method)
                    self.__method_type_map[method] = obj

        for ext in all_extensions:
            if self.__extensions[ext]:
                props = self.__extensions[ext].getProperties()
            else:
                props = self.__factory.getObjectProperties(ext)

        # Generate read and write mapping for attributes
        self.__attribute_map = self.__factory.get_attributes_by_object(self.__base_type)

        # Generate attribute to object-type mapping
        for attr in [n for n, o in self.__base.getProperties().items() if not o['foreign']]:
            self.__attributes.append(attr)
        self.__property_map = self.__base.getProperties()
        for ext in all_extensions:
            if self.__extensions[ext]:
                props = self.__extensions[ext].getProperties()
            else:
                props = self.__factory.getObjectProperties(ext)

            for attr in props:
                if not props[attr]['foreign']:
                    self.__attributes.append(attr)
                    self.__property_map[attr] = props[attr]
                else:

                    # Remember foreign properties to be able to the correct
                    # values to them after we have finished building up all classes
                    self.__foreign_attrs.append((attr, ext))

        # Get attribute to object-type mapping
        self.__attribute_type_map = self.__factory.getAttributeTypeMap(self.__base_type)
        self.uuid = self.__base.uuid
        self.dn = self.__base.dn

        self.populate_to_foreign_properties()

    def get_all_method_names(self):
        return self.__all_method_names

    def populate_to_foreign_properties(self, extension=None):
        """
        Populate values to foreign attributes.
        After creating an extension we've to tell it which values
        have to be used for its foreign properties.

        This is only necessary initially. If we modified a property
        that is used as foreign property somewhere else, then the setter
        method of this proxy will forward the value to all classes.
        """
        for attr, ext in self.__foreign_attrs:

            # Only populate value for the given extension
            if extension is not None and extension != ext:
                continue

            # Tell the class that own the foreign property that it
            # has to use the source property data.
            cur = self.__property_map[attr]
            if ext in self.__extensions and self.__extensions[ext]:
                self.__extensions[ext].set_foreign_value(attr, cur)

    def get_extension_dependencies(self, extension):
        required = []
        oTypes = self.__factory.getObjectTypes()

        def _resolve(ext):
            for r_ext in oTypes[ext]['requires']:
                required.append(r_ext)
                _resolve(r_ext)

        _resolve(extension)

        return required

    def get_attributes(self, detail=False):
        """
        Returns a list containing all property names known for the instantiated object.
        """
        attrs = None

        # Do we have read permissions for the requested attribute, method
        if self.__current_user:
            def check_acl(self, attribute):
                attr_type = self.__attribute_type_map[attribute]
                topic = "%s.objects.%s.attributes.%s" % (self.__env.domain, attr_type, attribute)
                result = self.__acl_resolver.check(self.__current_user, topic, "r", base=self.dn)
                if result:
                    self.__log.debug("User %s is allowed to access property %s!" % (self.__current_user, topic))
                else:
                    self.__log.debug("User %s is NOT allowed to access property %s!" % (self.__current_user, topic))
                return result

            attrs = list(filter(lambda x: check_acl(self, x), self.__attributes))
        else:
            attrs = self.__attributes

        if detail:
            res = {}
            for attr in attrs:
                res[attr] = {
                    'case_sensitive': self.__property_map[attr]['case_sensitive'],
                    'unique': self.__property_map[attr]['unique'],
                    'mandatory': self.__property_map[attr]['mandatory'],
                    'depends_on': self.__property_map[attr]['depends_on'],
                    'blocked_by': self.__property_map[attr]['blocked_by'],
                    'default': self.__property_map[attr]['default'],
                    'readonly': self.__property_map[attr]['readonly'],
                    'values': self.__property_map[attr]['values'],
                    'multivalue': self.__property_map[attr]['multivalue'],
                    'type': self.__property_map[attr]['type']}

            return res

        return attrs

    def get_methods(self):
        """
        Returns a list containing all method names known for the instantiated object.
        """

        # Do we have read permissions for the requested method
        if self.__current_user:
            def check_acl(method):
                attr_type = self.__method_type_map[method]
                topic = "%s.objects.%s.methods.%s" % (self.__env.domain, attr_type, method)
                return self.__acl_resolver.check(self.__current_user, topic, "x", base=self.dn)

            return list(filter(lambda x: check_acl(x), self.__method_map.keys()))

        return self.__method_map.keys()

    def get_parent_dn(self, dn=None):
        if not dn:
            dn = self.__base.dn
        return dn2str(str2dn(dn)[1:])

    def get_adjusted_parent_dn(self, dn=None):
        index = PluginRegistry.getInstance("ObjectIndex")
        tdn = []
        pdn = self.get_parent_dn(dn)

        # Skip base
        if len(pdn) < len(self.__env.base):
            return pdn

        while True:
            if pdn == self.__env.base or len(pdn) < len(self.__env.base):
                break

            # Fetch object type for pdn
            ptype = index.search({"dn": pdn}, {'_type': 1})[0]['_type']
            schema = self.__factory.getXMLSchema(ptype)
            if not ("StructuralInvisible" in schema.__dict__ and schema.StructuralInvisible == True):
                tdn.append(str2dn(pdn.encode('utf-8'))[0])

            pdn = self.get_parent_dn(pdn)

        tdn = str2dn(self.__env.base)[::-1] + tdn[::-1]

        return dn2str(tdn[::-1])

    def get_base_type(self):
        return self.__base.__class__.__name__

    def get_extension_types(self):
        return dict([(e, i is not None) for e, i in self.__extensions.items()])

    def get_templates(self, theme="default"):
        res = {self.get_base_type(): self.__base.getTemplate(theme)}
        for name, ext in self.__extensions.items():
            res[name] = ext.getTemplate(theme) if ext else self._get_template(name, theme)
        return res

    def _get_object_templates(self, obj):
        templates = []
        schema = self.__factory.getXMLSchema(obj)
        if "Templates" in schema.__dict__:
            for template in schema.Templates.iterchildren():
                templates.append(template.text)

        return templates

    def _get_template(self, obj, theme):
        templates = self._get_object_templates(obj)
        if templates:
            return self.__base.__class__.getNamedTemplate(self.__env, templates, theme)

        return None

    def get_attribute_values(self):
        """
        Return a dictionary containing all property values.
        """
        res = {'value': {}, 'values': {}}
        for item in self.get_attributes():
            if self.__base_type == self.__attribute_type_map[item]:
                res['value'][item] = getattr(self, item)
                if self.__base.getProperties()[item]['values_populate']:
                    res['values'][item] = self.__base.getProperties()[item]['values']
            elif self.__extensions[self.__attribute_type_map[item]]:
                res['value'][item] = getattr(self, item)
                if self.__extensions[self.__attribute_type_map[item]].getProperties()[item]['values_populate']:
                    res['values'][item] = self.__extensions[self.__attribute_type_map[item]].getProperties()[item]['values']

        return res

    def get_object_info(self, locale=None, theme="default"):
        res = {'base': self.get_base_type(), 'extensions': self.get_extension_types()}

        # Resolve all available extensions for their dependencies
        ei = {}
        for e in res['extensions'].keys():
            ei[e] = self.get_extension_dependencies(e)
        res['extension_deps'] = ei
        res['extension_methods'] = {};
        for method in self.__method_type_map:
            if self.__method_type_map[method] not in res['extension_methods']:
                res['extension_methods'][self.__method_type_map[method]] = []
            res['extension_methods'][self.__method_type_map[method]].append(method)

        return res

    def extend(self, extension):
        """
        Extends the base-object with the given extension
        """

        # Is this a valid extension?
        if not extension in self.__extensions:
            raise ProxyException(C.make_error('OBJECT_EXTENSION_NOT_ALLOWED', extension=extension))

        # Is this extension already active?
        if self.__extensions[extension] is not None:
            raise ProxyException(C.make_error('OBJECT_EXTENSION_DEFINED', extension=extension))

        # Ensure that all precondition for this extension are fullfilled
        oTypes = self.__factory.getObjectTypes()
        for r_ext in oTypes[extension]['requires']:
            if not r_ext in self.__extensions or self.__extensions[r_ext] is None:
                raise ProxyException(C.make_error('OBJECT_EXTENSION_DEPENDS', extension=extension, missing=r_ext))

        # Check Acls
        # Required is the 'c' (create) right for the extension on the current object.
        if self.__current_user is not None:
            topic = "%s.objects.%s" % (self.__env.domain, extension)
            if not self.__acl_resolver.check(self.__current_user, topic, "c", base=self.__base.dn):
                self.__log.debug("user '%s' has insufficient permissions to add extension %s to %s, required is %s:%s on %s" % (
                self.__current_user, extension, self.__base.dn, topic, "c", self.__base.dn))
                raise ACLException(C.make_error('PERMISSION_EXTEND', extension=extension, target=self.__base.dn))

        # Create extension
        if extension in self.__retractions:
            self.__extensions[extension] = self.__retractions[extension]
            del self.__retractions[extension]
        else:
            self.__extensions[extension] = self.__factory.getObject(extension, self.__base.uuid, mode="extend")
            self.__extensions[extension].parent = self
            self.__extensions[extension].owner = self.__current_user

        # Register the extensions methods
        object_types = self.__factory.getObjectTypes()
        for method in object_types[extension]['methods']:
            self.__method_map[method] = getattr(self.__extensions[extension], method)
            self.__method_type_map[method] = extension

        # Set initial values for foreign properties
        self.populate_to_foreign_properties(extension)

    def retract(self, extension):
        """
        Retracts an extension from the current object
        """
        if not extension in self.__extensions:
            raise ProxyException(C.make_error('OBJECT_EXTENSION_NOT_ALLOWED', extension=extension))

        if self.__extensions[extension] is None:
            raise ProxyException(C.make_error('OBJECT_NO_SUCH_EXTENSION', extension=extension))

        # Collect all extensions that are required due to dependencies..
        oTypes = self.__factory.getObjectTypes()
        for ext in self.__extensions:
            if self.__extensions[ext]:
                if extension in  oTypes[ext]['requires']:
                    raise ProxyException(C.make_error('OBJECT_EXTENSION_IN_USE', extension=extension, origin=ext))

        # Check Acls
        # Required is the 'd' (delete) right for the extension on the current object.
        if self.__current_user is not None:
            topic = "%s.objects.%s" % (self.__env.domain, extension)
            if not self.__acl_resolver.check(self.__current_user, topic, "d", base=self.__base.dn):
                self.__log.debug("user '%s' has insufficient permissions to add extension %s to %s, required is %s:%s on %s" % (
                self.__current_user, extension, self.__base.dn, topic, "d", self.__base.dn))
                raise ACLException(C.make_error('PERMISSION_RETRACT', extension=extension, target=self.__base.dn))

        # Unregister the extensions methods
        for method in list(self.__method_type_map):
            if self.__method_type_map[method] == extension:
                del(self.__method_map[method])
                del(self.__method_type_map[method])

        # Move the extension to retractions
        self.__retractions[extension] = self.__extensions[extension]
        self.__extensions[extension] = None

    def move(self, new_base, recursive=False):
        """
        Moves the currently proxied object to another base
        """

        # Check ACLs
        # to move an object we need the 'w' (write) right on the virtual attribute base,
        # the d (delete) right for the complete source object and at least the c (create)
        # right on the target base.
        if self.__current_user is not None:

            # Prepare ACL results
            topic_user = "%s.objects.%s" % (self.__env.domain, self.__base_type)
            topic_base = "%s.objects.%s.attributes.base" % (self.__env.domain, self.__base_type)

            allowed_base_mod = self.__acl_resolver.check(self.__current_user, topic_base, "w", base=self.dn)
            allowed_delete = self.__acl_resolver.check(self.__current_user, topic_user, "d", base=self.dn)
            allowed_create = self.__acl_resolver.check(self.__current_user, topic_user, "c", base=new_base)

            # Check for 'w' access to attribute base
            if not allowed_base_mod:
                self.__log.debug("user '%s' has insufficient permissions to move %s, required is %s:%s on %s" % (
                    self.__current_user, self.__base.dn, topic_base, "w", self.__base.dn))
                raise ACLException(C.make_error('PERMISSION_MOVE', source=self.__base.dn, target=new_base))

            # Check for 'd' permission on the source object
            if not allowed_delete:
                self.__log.debug("user '%s' has insufficient permissions to move %s, required is %s:%s on %s" % (
                    self.__current_user, self.__base.dn, topic_user, "d", self.__base.dn))
                raise ACLException(C.make_error('PERMISSION_MOVE', source=self.__base.dn, target=new_base))

            # Check for 'c' permission on the source object
            if not allowed_create:
                self.__log.debug("user '%s' has insufficient permissions to move %s, required is %s:%s on %s" % (
                    self.__current_user, self.__base.dn, topic_user, "c", new_base))
                raise ACLException(C.make_error('PERMISSION_MOVE', source=self.__base.dn, target=new_base))

        zope.event.notify(ObjectChanged("pre object move", self.__base))

        if recursive:
            old_base = self.__base.dn

            try:
                child_new_base = dn2str([str2dn(self.__base.dn)[0]]) + "," + new_base

                # Get primary backend of the object to be moved
                p_backend = getattr(self.__base, '_backend')

                # Traverse tree and find different backends
                foreign_backends = {}
                index = PluginRegistry.getInstance("ObjectIndex")
                children = index.search({"dn": [self.__base.dn, "%," + self.__base.dn]},
                    {'dn': 1, '_type': 1})

                # Note all elements with different backends
                for v in children:
                    cdn = v['dn']
                    ctype = v['_type']
                    cback = self.__factory.getObjectTypes()[ctype]['backend']
                    if cback != p_backend:
                        if not cback in foreign_backends:
                            foreign_backends = []
                        foreign_backends[cback].append(cdn)

                # Only keep the first per backend that is close to the root
                root_elements = {}
                for fbe, fdns in foreign_backends.items():
                    fdns.sort(key=len)
                    root_elements[fbe] = fdns[0]

                # Move base object
                self.__base.move(new_base)

                # Move additional backends if needed
                for fbe, fdn in root_elements.items():

                    # Get new base of child
                    new_child_dn = fdn[:len(fdn) - len(old_base)] + child_new_base
                    new_child_base = dn2str(str2dn(new_child_dn)[1:])

                    # Select objects with different base and trigger a move, the
                    # primary backend move will be triggered and do a recursive
                    # move for that backend.
                    obj = self.__factory.getObject(children[fdn], fdn)
                    obj.parent = self
                    obj.move(new_child_base)

                # Update all DN references
                # Emit 'post move' events
                for child in children:
                    cdn = child['dn']
                    ctype = child['_type']

                    # Don't handle objects that already have been moved
                    if cdn in root_elements.values():
                        continue

                    # These objects have been moved automatically. Open
                    # them and let them do a simulated move to update
                    # their refs.
                    new_cdn = cdn[:len(cdn) - len(old_base)] + child_new_base
                    obj = self.__factory.getObject(ctype, new_cdn)
                    obj.parent = self
                    obj.simulate_move(cdn)

                zope.event.notify(ObjectChanged("post object move", self.__base))
                return True

            except Exception as e:
                from traceback import print_exc
                print_exc()
                self.__log.error("moving object '%s' from '%s' to '%s' failed: %s" % (self.__base.uuid, old_base, new_base, str(e)))
                return False

        else:
            # Test if we've children
            if len(self.__factory.getObjectChildren(self.__base.dn)):
                raise ProxyException(C.make_error('OBJECT_HAS_CHILDREN', target=self.__base.dn))

        try:
            self.__base.move(new_base)
            zope.event.notify(ObjectChanged("post object move", self.__base))
            return True

        except Exception as e:
            from traceback import print_exc
            print_exc()
            self.__log.error("moving object '%s' from '%s' to '%s' failed: %s" % (self.__base.uuid, self.__base.dn, new_base, str(e)))
            return False

    def remove(self, recursive=False):
        """
        Removes the currently proxied object.
        """

        # Check ACLs
        # We need the 'd' right for the current base-object and all its active extensions to be able to remove it.
        if self.__current_user is not None:
            required_acl_objects = [self.__base_type] + [ext for ext, item in self.__extensions.items() if
                                                         item is not None]
            for ext_type in required_acl_objects:
                topic = "%s.objects.%s" % (self.__env.domain, ext_type)
                if not self.__acl_resolver.check(self.__current_user, topic, "d", base=self.dn):
                    self.__log.debug("user '%s' has insufficient permissions to remove %s, required is %s:%s" % (
                        self.__current_user, self.__base.dn, topic, 'd'))
                    raise ACLException(C.make_error('PERMISSION_REMOVE', target=self.__base.dn))

        zope.event.notify(ObjectChanged("pre object remove", self.__base))

        if recursive:

            # Load all children and remove them, starting from the most
            # nested ones.
            index = PluginRegistry.getInstance("ObjectIndex")
            children = index.search({"dn": [self.__base.dn, "%," + self.__base.dn]}, {'dn': 1})
            children = [c['dn'] for c in children]

            children.sort(key=len, reverse=True)

            for child in children:
                c_obj = ObjectProxy(child)
                c_obj.remove(recursive=True)

        else:
            # Test if we've children
            index = PluginRegistry.getInstance("ObjectIndex")
            if len(index.search({"dn": "%," + self.__base.dn}, {'dn': 1})):
                raise ProxyException(C.make_error('OBJECT_HAS_CHILDREN', target=self.__base.dn))

        for extension in [e for e in self.__extensions.values() if e]:
            extension.remove_refs()
            extension.retract()

        self.__base.remove_refs()
        self.__base.remove()

        zope.event.notify(ObjectChanged("post object remove", self.__base))

    def commit(self):

        # Check create permissions
        if self.__base_mode == "create":
            topic = "%s.objects.%s" % (self.__env.domain, self.__base_type)
            if self.__current_user is not None and not self.__acl_resolver.check(self.__current_user, topic, "c", base=self.dn):
                self.__log.debug("user '%s' has insufficient permissions to create %s, required is %s:%s" % (
                    self.__current_user, self.__base.dn, topic, 'c'))
                raise ACLException(C.make_error('PERMISSION_CREATE', target=self.__base.dn))

        zope.event.notify(ObjectChanged("pre object %s" % self.__base_mode, self.__base))

        # Gather information about children
        old_base = self.__base.dn

        # Get primary backend of the object to be moved
        p_backend = getattr(self.__base, '_backend')

        # Traverse tree and find different backends
        foreign_backends = {}
        index = PluginRegistry.getInstance("ObjectIndex")
        children = index.search({"dn": [self.__base.dn, "%," + self.__base.dn]},
            {'dn': 1, '_type': 1})

        # Note all elements with different backends
        for v in children:
            cdn = v['dn']
            ctype = v['_type']

            cback = self.__factory.getObjectTypes()[ctype]['backend']
            if cback != p_backend:
                if not cback in foreign_backends:
                    foreign_backends[cback] = []
                foreign_backends[cback].append(cdn)

        # Only keep the first per backend that is close to the root
        root_elements = {}
        for fbe, fdns in foreign_backends.items():
            fdns.sort(key=len)
            root_elements[fbe] = fdns[0]

        # Handle retracts
        for idx in self.__retractions.keys():
            if self.__initial_extension_state[idx]:
                self.__retractions[idx].retract()
            del self.__retractions[idx]

        # Check each extension before trying to save them
        check_props = self.__base.check()
        for extension in [ext for ext in self.__extensions.values() if ext]:
            check_props.update(extension.check(check_props))

        # Handle commits
        save_props = self.__base.commit()
        for extension in [ext for ext in self.__extensions.values() if ext]:

            # Populate the base uuid to the extensions
            if extension.uuid and extension.uuid != self.__base.uuid:
                raise ProxyException(C.make_error('OBJECT_UUID_MISMATCH', b_uuid=self.__base.uuid, e_uuid=extension.uuid))
            if not extension.uuid:
                extension.uuid = self.__base.uuid
            extension.dn = self.__base.dn
            save_props.update(extension.commit(save_props))

        # Skip further actions if we're in create mode
        if self.__base_mode == "create":
            pass

        # Did the commit result in a move?
        elif self.dn != self.__base.dn:

            if children:
                # Move additional backends if needed
                for fbe, fdn in root_elements.items():

                    # Get new base of child
                    new_child_dn = fdn[:len(fdn) - len(old_base)] + self.__base.dn
                    new_child_base = dn2str(str2dn(new_child_dn)[1:])

                    # Select objects with different base and trigger a move, the
                    # primary backend move will be triggered and do a recursive
                    # move for that backend.
                    obj = self.__factory.getObject(children[fdn], fdn)
                    obj.move(new_child_base)

                # Update all DN references
                # Emit 'post move' events
                for entry in children:
                    cdn = entry['dn']
                    ctype = entry['_type']

                    # Don't handle objects that already have been moved
                    if cdn in root_elements.values():
                        continue

                    # These objects have been moved automatically. Open
                    # them and let them do a simulated move to update
                    # their refs.
                    new_cdn = cdn[:len(cdn) - len(old_base)] + self.__base.dn
                    obj = self.__factory.getObject(ctype, new_cdn)
                    obj.simulate_move(cdn)

            self.dn = self.__base.dn

            zope.event.notify(ObjectChanged("post object move", self.__base))

        zope.event.notify(ObjectChanged("post object %s" % self.__base_mode, self.__base))

    def __getattr__(self, name):

        # Valid method? and enough permissions?
        if name in self.__method_map:

            # Check permissions
            # To execute a method the 'x' permission is required.
            attr_type = self.__method_type_map[name]
            topic = "%s.objects.%s.methods.%s" % (self.__env.domain, attr_type, name)
            if self.__current_user is not None and not self.__acl_resolver.check(self.__current_user, topic, "x", base=self.dn):
                self.__log.debug("user '%s' has insufficient permissions to execute %s on %s, required is %s:%s" % (
                    self.__current_user, name, self.dn, topic, "x"))
                raise ACLException(C.make_error('PERMISSION_ACCESS', topic, target=self.dn))
            return self.__method_map[name]

        if name == 'modifyTimestamp':
            timestamp = self.__base.modifyTimestamp
            for obj in self.__extensions.values():
                if obj and obj.modifyTimestamp and timestamp < obj.modifyTimestamp:
                    timestamp = obj.modifyTimestamp

            return timestamp

        # Valid attribute?
        if not name in self.__attribute_map:
            raise AttributeError(C.make_error('ATTRIBUTE_NOT_FOUND', name))

        # Do we have read permissions for the requested attribute
        attr_type = self.__attribute_type_map[name]
        topic = "%s.objects.%s.attributes.%s" % (self.__env.domain, attr_type, name)
        if self.__current_user is not None and not self.__acl_resolver.check(self.__current_user, topic, "r", base=self.dn):
            self.__log.debug("user '%s' has insufficient permissions to read %s on %s, required is %s:%s" % (
                self.__current_user, name, self.dn, topic, "r"))
            raise ACLException(C.make_error('PERMISSION_ACCESS', topic, target=self.dn))

        # Load from primary object
        base_object = self.__attribute_map[name]['base']
        if self.__base_type == base_object:
            return getattr(self.__base, name)

        # Check for extensions
        if base_object in self.__extensions and self.__extensions[base_object]:
            return getattr(self.__extensions[base_object], name)

        # Not set
        return None

    def __setattr__(self, name, value):

        # Store non property values
        try:
            object.__getattribute__(self, name)
            self.__dict__[name] = value
            return
        except AttributeError:
            pass

        # If we try to modify object specific properties then check acls
        if self.__attribute_map and name in self.__attribute_map and self.__current_user is not None:

            # Do we have read permissions for the requested attribute, method
            attr_type = self.__attribute_type_map[name]
            topic = "%s.objects.%s.attributes.%s" % (self.__env.domain, attr_type, name)
            if not self.__acl_resolver.check(self.__current_user, topic, "w", base=self.dn):
                self.__log.debug("user '%s' has insufficient permissions to write %s on %s, required is %s:%s" % (
                    self.__current_user, name, self.dn, topic, "w"))
                raise ACLException(C.make_error('PERMISSION_ACCESS', topic, target=self.dn))

        # Valid attribute?
        if not name in self.__attribute_map:
            raise AttributeError(C.make_error('ATTRIBUTE_NOT_FOUND', name))

        found = False
        classes = [self.__attribute_map[name]['base']] + self.__attribute_map[name]['secondary']

        for obj in classes:

            if self.__base_type == obj:
                found = True
                setattr(self.__base, name, value)
                continue

            # Forward attribute modification to all extension that provide
            # that given value (even if it is foreign)
            if obj in self.__extensions and self.__extensions[obj]:
                found = True
                setattr(self.__extensions[obj], name, value)
                continue

        if not found:
            raise AttributeError(C.make_error('ATTRIBUTE_NOT_FOUND', name))

    def asJSON(self, only_indexed=False):
        """
        Returns JSON representations for the base-object and all its extensions.
        """
        atypes = self.__factory.getAttributeTypes()

        # Check permissions
        topic = "%s.objects.%s" % (self.__env.domain, self.__base_type)
        if self.__current_user is not None and not self.__acl_resolver.check(self.__current_user, topic, "r", base=self.dn):
            self.__log.debug("user '%s' has insufficient permissions for asJSON on %s, required is %s:%s" % (
                self.__current_user, self.dn, topic, "r"))
            raise ACLException(C.make_error('PERMISSION_ACCESS', topic, target=self.dn))

        res = {'dn': self.__base.dn, '_type': self.__base.__class__.__name__,
               '_parent_dn': self.get_parent_dn(self.__base.dn),
               '_adjusted_parent_dn': self.get_adjusted_parent_dn(self.__base.dn),
               '_uuid': self.__base.uuid}

        # Create non object pseudo attributes
        if self.__base.modifyTimestamp:
            res['_last_changed'] = time.mktime(self.__base.modifyTimestamp.timetuple())

        res['_extensions'] = [k for k in self.__extensions.keys() if self.__extensions[k]]

        props = self.__property_map
        for propname in self.__property_map:

            # Use the object-type conversion method to get valid item string-representations.
            prop_value = props[propname]['value']
            if props[propname]['type'] == "Binary":
                res[propname] = list(map(lambda x: Binary(str(x.get())), prop_value))

            # Make remaining values unicode
            else:
                res[propname] = atypes[props[propname]['type']].convert_to("UnicodeString", prop_value)

        return res

    def asXML(self, only_indexed=False):
        """
        Returns XML representations for the base-object and all its extensions.
        """
        atypes = self.__factory.getAttributeTypes()

        # Check permissions
        topic = "%s.objects.%s" % (self.__env.domain, self.__base_type)
        if self.__current_user is not None and not self.__acl_resolver.check(self.__current_user, topic, "r", base=self.dn):
            self.__log.debug("user '%s' has insufficient permissions for asXML on %s, required is %s:%s" % (
                self.__current_user, self.dn, topic, "r"))
            raise ACLException(C.make_error('PERMISSION_ACCESS', topic, target=self.dn))

        # Get the xml definitions combined for all objects.
        xmldefs = etree.tostring(self.__factory.getXMLDefinitionsCombined())

        # Create a document wich contains all necessary information to create
        # xml reprentation of our own.
        # The class-name, all property values and the object definitions
        classtag = etree.Element("class")
        classtag.text = self.__base.__class__.__name__

        # Create a list of all class information required to build an
        # xml represention of this class
        propertiestag = etree.Element("properties")
        attrs = {'dn': [self.__base.dn], 'parent-dn': [re.sub("^[^,]*,", "", self.__base.dn)],
                 'entry-uuid': [self.__base.uuid]}
        if self.__base.modifyTimestamp:
            attrs['modify-date'] = atypes['Timestamp'].convert_to("UnicodeString", [self.__base.modifyTimestamp])

        # Create a list of extensions and their properties
        exttag = etree.Element("extensions")
        for name in self.__extensions.keys():
            if self.__extensions[name]:
                ext = etree.Element("extension")
                ext.text = name
                exttag.append(ext)

        props = self.__property_map
        for propname in self.__property_map:

            # Use the object-type conversion method to get valid item string-representations.
            # This does not work for boolean values, due to the fact that xml requires
            # lowercase (true/false)
            prop_value = props[propname]['value']
            if props[propname]['type'] == "Boolean":
                attrs[propname] = map(lambda x: 'true' if x == True else 'false', prop_value)

            # Skip binary ones
            elif props[propname]['type'] == "Binary":
                attrs[propname] = map(lambda x: x.encode(), prop_value)

            # Make remaining values unicode
            else:
                attrs[propname] = atypes[props[propname]['type']].convert_to("UnicodeString", prop_value)

        # Build a xml represention of the collected properties
        for key in attrs:

            # Skip empty ones
            if not len(list(attrs[key])):
                continue

            # Build up xml-elements
            xml_prop = etree.Element("property")
            for value in attrs[key]:
                xml_value = etree.Element("value")
                xml_value.text = value
                xml_name = etree.Element('name')
                xml_name.text = key
                xml_prop.append(xml_name)
                xml_prop.append(xml_value)

            propertiestag.append(xml_prop)

        # Combine all collected class info in a single xml file, this
        # enables us to compute things using xsl
        use_index = "<only_indexed>true</only_indexed>" if only_indexed else "<only_indexed>false</only_indexed>"
        xml = "<merge xmlns=\"http://www.gonicus.de/Objects\">%s<defs>%s</defs>%s%s%s</merge>" % (etree.tostring(classtag),
                                                                                                  xmldefs, etree.tostring(propertiestag), etree.tostring(exttag), use_index)

        # Transform xml-combination into a useable xml-class representation
        xml_doc = etree.parse(StringIO(xml))
        xslt_doc = etree.parse(pkg_resources.resource_filename('gosa.backend', 'data/object_to_xml.xsl')) #@UndefinedVariable
        transform = etree.XSLT(xslt_doc)
        res = transform(xml_doc)
        return etree.tostring(res)


from .factory import ObjectFactory
from .object import ObjectChanged
