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
import copy
import gettext

from datetime import datetime

import ldap
import pkg_resources
import re
import time
import zope.event
from lxml import etree, objectify
from ldap.dn import dn2str, str2dn
from logging import getLogger

from gosa.backend.routes.sse.main import SseHandler
from gosa.backend.utils.ldap import normalize_dn
from gosa.common import Environment
from gosa.common.event import EventMaker
from gosa.common.utils import is_uuid, N_
from gosa.common.components import PluginRegistry
from gosa.common.error import GosaErrorHandler as C
from gosa.backend.exceptions import ACLException, ProxyException
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
    OBJECT_UUID_MISMATCH=N_("UUID of base (%(b_uuid)s) and extension (%(e_uuid)s) differ"),
    MOVE_TARGET_INVALID=N_("moving object '%(target)s' from '%(old_dn)s' to '%(new_dn)s' failed: no valid container found"),
    OBJECT_EXTENSION_CONDITION_FAILED=N_("Extension '%(extension)s' condition not met"),
    CANNOT_CREATE_OBJECT_READ_ONLY=N_("Cannot create object in read-only mode.")
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
    __current_session_id = None
    __attribute_type_map = None
    __method_type_map = None
    __attributes = None
    __base_mode = None
    __property_map = None
    __foreign_attrs = None
    __all_method_names = None
    __search_aid = None
    __attribute_change_hooks = None
    __attribute_change_write_hooks = None
    __read_only = False

    def __init__(self, _id, what=None, user=None, session_id=None,
                 data=None, read_only=False, skip_value_population=False, open_mode=None):
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
        self.__current_session_id = session_id
        self.__acl_resolver = PluginRegistry.getInstance("ACLResolver")
        self.__attribute_type_map = {}
        self.__attributes = []
        self.__method_type_map = {}
        self.__property_map = {}
        self.__foreign_attrs = []
        self.__all_method_names = []
        self.__read_only = self.__env.mode == "proxy" or read_only
        # hooks that are triggered on every setattr
        self.__attribute_change_hooks = {}
        # hooks that are triggered when the attribute change is committed
        self.__attribute_change_write_hooks = {}
        self.__open_mode = open_mode

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
            if what not in object_types:
                raise ProxyException(C.make_error('OBJECT_UNKNOWN_TYPE', type=type))

            start_dn = dn_or_base
            dn_or_base = self.find_dn_for_object(what, base, start_dn, []) if base else dn_or_base
            self.create_missing_containers(dn_or_base, start_dn, base)
            base = what
            base_mode = "create"
            extensions = []

        if not base:
            raise ProxyException(C.make_error('OBJECT_NOT_FOUND', id=dn_or_base), status=404)

        if self.__read_only is True and base_mode == "create":
            raise ProxyException(C.make_error('CANNOT_CREATE_OBJECT_READ_ONLY', id=dn_or_base))

        # Get available extensions
        self.__log.debug("loading %s base object for %s" % (base, dn_or_base))
        all_extensions = object_types[base]['extended_by']

        # Load base object and extensions
        self.__base = self.__factory.getObject(base, dn_or_base,
                                               mode=base_mode,
                                               data=data[base] if data is not None and base in data else None,
                                               read_only=self.__read_only,
                                               skip_value_population=skip_value_population)
        self.__base._owner = self.__current_user
        self.__base._session_id = self.__current_session_id
        self.__base.parent = self
        self.__base_type = base
        self.__base_mode = base_mode
        for extension in extensions:
            self.__log.debug("loading %s extension for %s" % (extension, dn_or_base))
            try:
                self.__extensions[extension] = self.__factory.getObject(extension, self.__base.uuid,
                                                                        data=data[extension] if data is not None and extension in data else None,
                                                                        read_only=self.__read_only,
                                                                        skip_value_population=skip_value_population)
                self.__extensions[extension].dn = self.__base.dn
                self.__extensions[extension].parent = self
                self.__extensions[extension]._owner = self.__current_user
                self.__extensions[extension]._session_id = self.__current_session_id
                self.__initial_extension_state[extension] = {"active": True, "allowed": True}
            except Exception as e:
                if open_mode == "delete" and hasattr(e, "status_code") and e.status_code == 404:
                    self.__initial_extension_state[extension] = {"active": False, "allowed": True, "deleted": True}
                else:
                    raise e

        for extension in all_extensions:
            if extension not in self.__extensions:
                self.__extensions[extension] = None
                self.__initial_extension_state[extension] = {"active": False, "allowed": True}

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
        self.__property_map = self.__base.getProperties()
        for attr in [n for n, o in self.__property_map.items() if not o['foreign']]:
            self.__attributes.append(attr)
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
        self.__search_aid = PluginRegistry.getInstance("ObjectIndex").get_search_aid()

        # build property change hooks from extension conditions
        if self.__base.extension_conditions is not None:
            for ext_name in self.__base.extension_conditions:
                condition = self.__base.extension_conditions[ext_name]
                self.revalidate_extension_condition(ext_name, skip_event=True)

                if "properties" in condition:
                    for prop in condition["properties"]:
                        if prop not in self.__attribute_change_hooks:
                            self.__attribute_change_hooks[prop] = []
                        self.__attribute_change_hooks[prop].append({
                            "hook": self.revalidate_extension_condition,
                            "params": [ext_name]
                        })

        # build property change hooks from update_hooks
        self.__attribute_change_write_hooks = self.__factory.getUpdateHooks(self.__base_type)

    def inject_backend_data(self, data, force_update=False, raw=True):
        """
        Apply attribute values as if they were read from each backend.
        If a backend receives data e.g. by hook events there is no need to query the backend again, the received data
        can be used directly.

        :param data: dict with {extension_name: { backend_name: { attribute_name: value, ...}, ...}, ...}
        :type data: dict
        :param force_update: force the object to mark the attributes as changed
        :type force_update: boolean
        :param raw: if true the values in data like they are read directly from the backend and therefore need the in-filters and type
                    conversion applied, otherwise those are skipped
        :type raw: boolean
        """
        for extension in data:
            if self.__base_type == extension:
                self.__log.debug("applying data to base object %s" % extension)
                self.__base.inject_backend_data(data[extension], force_update=force_update, raw=raw)
            elif extension in self.__extensions:
                if not self.is_extended_by(extension):
                    self.__log.debug("applying data to new extension object %s" % extension)
                    if "common" in data[extension]:
                        self.extend(extension)
                        for key, value in data[extension]["common"].items():
                            setattr(self, key, value)
                    else:
                        self.extend(extension, data=data[extension], force_update=force_update)
                else:
                    self.__log.debug("applying data to existing extension object %s" % extension)
                    self.__extensions[extension].inject_backend_data(data[extension], force_update=force_update, raw=raw)
            else:
                self.__log.warning("unknown extension '%s', skipping data" % extension)

    def apply_update(self, update):
        """
        Change multiple attribute values and extensions at once
        :param update: dict of {attribute_name: new value,...,'__extensions__': []}
        :type update: dict
        """
        if '__extensions__' in update:
            for ext in update['__extensions__']:
                if not self.is_extended_by(ext) and ext != self.__base.get_type():
                    self.extend(ext)
            del update['__extensions__']

        for name, value in update.items():
            ext = self.get_extension_off_attribute(name)
            if ext != self.__base.get_type() and not self.is_extended_by(ext):
                self.extend(ext)
            setattr(self, name, value)

    def get_dn(self):
        return self.dn

    def get_uuid(self):
        return self.uuid

    def find_dn_for_object(self, new_base, current_base, dn="", checked=None):
        """
        Traverse through the object_types to find the container, which holds objects of type *base* and return that containers
        DN

        :param new_base: object type to be created
        :param current_base: object type the new object should be created in
        :param dn: base DN suffix
        :param checked: for internal use in recursive calls
        :return: DN of found container
        """
        if checked is None:
            checked = []
        object_types = self.__factory.getObjectTypes()

        if 'container' in object_types[current_base]:
            if new_base in object_types[current_base]['container']:
                return dn
            else:
                for sub_base in object_types[current_base]['container']:
                    if sub_base not in checked and 'container' in object_types[sub_base]:
                        checked.append(sub_base)
                        if new_base in object_types[sub_base]['container']:
                            self.__log.debug("found DN '%s,%s' for base '%s'" % (object_types[sub_base]['backend_attrs']['FixedRDN'], dn,
                                                                                 new_base))
                            return "%s,%s" % (object_types[sub_base]['backend_attrs']['FixedRDN'], dn)
                        else:
                            new_dn = dn
                            if 'FixedRDN' in object_types[sub_base]['backend_attrs']:
                                new_dn = "%s,%s" % (object_types[sub_base]['backend_attrs']['FixedRDN'], dn)
                            result = self.find_dn_for_object(new_base, sub_base, new_dn, checked)
                            if result is not None:
                                return result

    def create_missing_containers(self, new_dn, base_dn, base_type):
        if new_dn == base_dn:
            return
        for base, dn in self.get_missing_containers(new_dn, base_dn, base_type, []):
            if dn != new_dn:
                # create container
                self.__log.debug("create container of type %s in %s" % (base, dn))
                container = ObjectProxy(dn, base)
                container.commit()

    def get_missing_containers(self, new_dn, base_dn, base_type, result=None):
        if new_dn is None:
            return []
        if result is None:
            result = []
        if new_dn == base_dn:
            return result
        self.__log.debug("collect missing containers for new object '%s' starting from '%s' (%s)" % (new_dn, base_dn, base_type))
        rel_dn = new_dn[0:-len(base_dn)-1]
        parts = rel_dn.split(",")
        if len(parts) < 0:
            return result
        part = parts[-1]

        check_dn = "%s,%s" % (",".join(parts[-1:]), base_dn)
        index = PluginRegistry.getInstance("ObjectIndex")

        object_types = self.__factory.getObjectTypes()
        for sub_base in object_types[base_type]['container']:
            if 'FixedRDN' in object_types[sub_base]['backend_attrs'] and object_types[sub_base]['backend_attrs']['FixedRDN'] == part:
                base_type = sub_base
                break

        res = index.search({'dn': check_dn}, {'_type': 1})
        if len(res) == 0:
            # create container
            result.append((base_type, base_dn))

        if len(parts) > 1:
            return self.get_missing_containers(new_dn, check_dn, base_type, result=result)
        else:
            return result

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

    def repopulate_attribute_values(self, attribute_name):
        type = self.get_extension_off_attribute(attribute_name)
        if type == self.get_base_type():
            self.__base.update_population_of_attribute(attribute_name)
        elif type is not None:
            self.__extension[type].update_population_of_attribute(attribute_name)
        else:
            raise AttributeError(C.make_error('ATTRIBUTE_NOT_FOUND', attribute_name))

    def get_extension_off_attribute(self, attribute_name):
        if attribute_name in self.__attribute_map:
            return self.__attribute_map[attribute_name]['base']
        return

    def get_extension_dependencies(self, extension):
        required = []
        oTypes = self.__factory.getObjectTypes()

        def _resolve(ext):
            for r_ext in oTypes[ext]['requires']:
                required.append(r_ext)
                _resolve(r_ext)

        _resolve(extension)

        return required

    def get_attributes(self, detail=False, locale=None):
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
                if self.__current_user not in self.__acl_resolver.admins:
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
                readonly = self.__property_map[attr]['readonly']
                attr_type = self.__attribute_type_map[attr]
                topic = "%s.objects.%s.attributes.%s" % (self.__env.domain, attr_type, attr)

                # check if user is allowed to edit this attribute, otherwise set it to readonly
                if not readonly and not self.__acl_resolver.check(self.__current_user, topic, "w", base=self.dn):
                    readonly = True

                validator_information = {}
                # check if the validator have some hints for us
                if self.__property_map[attr]["validator"] is not None:
                    for id in self.__property_map[attr]["validator"]:
                        entry = self.__property_map[attr]["validator"][id]
                        if "condition" in entry:
                            tmp = entry["condition"].get_gui_information(self.__property_map, attr, self.__property_map[attr]["value"], *entry["params"])
                            if tmp is not None:
                                validator_information.update(tmp)

                res[attr] = {
                    'case_sensitive': self.__property_map[attr]['case_sensitive'],
                    'unique': self.__property_map[attr]['unique'],
                    'mandatory': self.__property_map[attr]['mandatory'],
                    'depends_on': self.__property_map[attr]['depends_on'],
                    'blocked_by': self.__property_map[attr]['blocked_by'],
                    'default': self.__property_map[attr]['default'],
                    'readonly': readonly,
                    'values': self.__property_map[attr]['values'],
                    'multivalue': self.__property_map[attr]['multivalue'],
                    'type': self.__property_map[attr]['type'],
                    'auto': self.__property_map[attr]['auto'],
                    'value_inherited_from': self.__property_map[attr]['value_inherited_from'],
                    'validator_information': validator_information if len(validator_information.keys()) else None}

                if locale is not None and isinstance(res[attr]['values'], dict):
                    t = gettext.translation('messages',
                                            pkg_resources.resource_filename("gosa.backend", "locale"),
                                            fallback=True,
                                            languages=[locale])

                    for (key, value) in res[attr]['values'].items():
                        if isinstance(value, dict):
                            if value["value"] not in self.__property_map[attr]['skip_translation_values']:
                                value["value"] = t.gettext(value["value"])
                        elif value not in self.__property_map[attr]['skip_translation_values']:
                            res[attr]['values'][key] = t.gettext(value)

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

    def get_final_dn(self):
        """
        Returns the final DN of this object. If this object is creates the `dn` properties value is not the final one
        but the parent DN. In these cases this method generates the future DN this obejct will get after it has been stored in LDAP
        backend
        """
        self.__base.get_final_dn()

    def get_parent_dn(self, dn=None):
        if not dn:
            dn = self.__base.dn
        return dn2str(str2dn(dn, flags=ldap.DN_FORMAT_LDAPV3)[1:])

    def get_adjusted_parent_dn(self, dn=None):
        return ObjectProxy.get_adjusted_dn(self.get_parent_dn(dn), self.__env.base)

    @classmethod
    def get_adjusted_dn(cls, dn, base, property='dn'):
        index = PluginRegistry.getInstance("ObjectIndex")
        factory = ObjectFactory.getInstance()
        tdn = []
        pdn = dn
        # Skip base
        if len(pdn) < len(base):
            return pdn

        while True:
            if pdn == base or len(pdn) < len(base):
                break

            # Fetch object type for pdn
            res = index.search({property: pdn}, {'_type': 1})
            if len(res) == 0:
                raise Exception("no type found for DN: %s" % pdn)
            ptype = res[0]['_type']

            schema = factory.getXMLSchema(ptype)
            # Note: schema.StructuralInvisible is a BoolElement and no boolean value so never use "is True" use == operator instead
            if not ("StructuralInvisible" in schema.__dict__ and schema.StructuralInvisible == True):
                tdn.append(str2dn(pdn.encode('utf-8'))[0])

            pdn = dn2str(str2dn(pdn)[1:])

        tdn = str2dn(base)[::-1] + tdn[::-1]

        return dn2str(tdn[::-1])

    def get_base_type(self):
        return self.__base.__class__.__name__

    def get_extension_types(self):
        return dict([(e, i is not None) for e, i in self.__extensions.items()])

    def get_templates(self):
        res = {self.get_base_type(): self.__base.getTemplate()}
        for name, ext in self.__extensions.items():
            res[name] = ext.getTemplate() if ext else self._get_template(name)
        return res

    def _get_object_templates(self, obj):
        templates = []
        schema = self.__factory.getXMLSchema(obj)
        if "Templates" in schema.__dict__:
            for template in schema.Templates.iterchildren():
                templates.append(template.text)

        return templates

    def _get_template(self, obj):
        templates = self._get_object_templates(obj)
        if templates:
            return self.__base.__class__.getNamedTemplate(self.__env, templates)

        return None

    def get_attribute_values(self):
        """
        Return a dictionary containing all property values.
        """
        res = {'value': {}, 'values': {}, 'saveable': {}}
        base_properties = self.__base.getProperties()
        for item in self.get_attributes():
            if self.__base_type == self.__attribute_type_map[item]:
                res['value'][item] = getattr(self, item)
                res['saveable'][item] = base_properties[item]['readonly'] is False and \
                                        ('skip_save' not in base_properties[item] or base_properties[item]['skip_save'] is False)
                if base_properties[item]['values_populate']:
                    res['values'][item] = base_properties[item]['values']
            elif self.__extensions[self.__attribute_type_map[item]]:
                res['value'][item] = getattr(self, item)
                map = self.__extensions[self.__attribute_type_map[item]].getProperties()[item]
                res['saveable'][item] = map['readonly'] is False and ('skip_save' not in map or map['skip_save'] is False)
                if map['values_populate']:
                    res['values'][item] = map['values']

        return res

    def get_object_info(self, locale=None):
        res = {'base': self.get_base_type(), 'extensions': self.get_extension_types()}

        # Resolve all available extensions for their dependencies
        ei = {}
        for e in res['extensions'].keys():
            ei[e] = self.get_extension_dependencies(e)
        res['extension_deps'] = ei
        res['extension_methods'] = {}
        for method in self.__method_type_map:
            if self.__method_type_map[method] not in res['extension_methods']:
                res['extension_methods'][self.__method_type_map[method]] = []
            res['extension_methods'][self.__method_type_map[method]].append(method)

        res["extension_states"] = self.__initial_extension_state
        return res

    def extend(self, extension, data=None, force_update=False):
        """
        Extends the base-object with the given extension
        """

        # Is this a valid extension?
        if not extension in self.__extensions:
            raise ProxyException(C.make_error('OBJECT_EXTENSION_NOT_ALLOWED', extension=extension))

        # Is this extension already active?
        # if self.__extensions[extension] is not None:
        #     raise ProxyException(C.make_error('OBJECT_EXTENSION_DEFINED', extension=extension))

        # Ensure that all precondition for this extension are fulfilled
        object_types = self.__factory.getObjectTypes()
        for required_extension in object_types[extension]['requires']:
            if not required_extension in self.__extensions or self.__extensions[required_extension] is None:
                raise ProxyException(C.make_error('OBJECT_EXTENSION_DEPENDS',
                                                  extension=extension,
                                                  missing=required_extension))

        # check extension conditions (not in create mode, as conditions mostly do not verify in a new object)
        if self.__base_mode != "create" and extension in object_types[self.__base_type]['extension_conditions']:
            # as the extension validators are always dependant from the base type we use only its properties here
            # the values of self.__attribute_map might not be up to date
            props_copy = copy.deepcopy(self.__base.myProperties)

            res, error = self.__base.processValidator(object_types[self.__base_type]['extension_conditions'][extension], "extension",
                                            self.__base_type, props_copy)
            if not res:
                raise ProxyException(C.make_error('OBJECT_EXTENSION_CONDITION_FAILED',
                                                  extension=extension,
                                                  details=error))

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
            mode = "extend"
            if self.__extensions[extension]:
                mode = "update"
            self.__log.debug("creating new extension '%s' in '%s' mode%s" % (extension, mode, " with initial data" if data is not None
            else ""))
            self.__extensions[extension] = self.__factory.getObject(extension, self.__base.uuid, mode=mode, data=data, force_update=force_update)
            self.__extensions[extension].parent = self
            self.__extensions[extension]._owner = self.__current_user
            self.__extensions[extension]._session_id = self.__current_session_id

        # Register the extensions methods
        object_types = self.__factory.getObjectTypes()
        for method in object_types[extension]['methods']:
            self.__method_map[method] = getattr(self.__extensions[extension], method)
            self.__method_type_map[method] = extension

        # Set initial values for foreign properties
        self.populate_to_foreign_properties(extension)

    def is_extended_by(self, extension):
        return extension in self.__extensions and self.__extensions[extension] is not None

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
                if extension in oTypes[ext]['requires']:
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
        # find the right container in the new base
        old_dn = self.__base.dn
        ident = self.__factory.identifyObject(new_base)
        if ident is None or ident == (None, None):
            self.__log.error("moving object '%s' from '%s' to '%s' failed: no valid container found" % (self.__base.uuid, old_dn, new_base))
            raise ProxyException(C.make_error('MOVE_TARGET_INVALID', target=self.__base.uuid, old_dn=old_dn, new_dn=new_base))

        base_type = ident[0]
        base_dn = new_base
        real_new_base = self.find_dn_for_object(self.__base_type, base_type, new_base, checked=[])

        if real_new_base is None:
            self.__log.error("moving object '%s' from '%s' to '%s' failed: no valid container found" % (self.__base.uuid, old_dn, new_base))
            raise ProxyException(C.make_error('MOVE_TARGET_INVALID', target=self.__base.uuid, old_dn=old_dn, new_dn=new_base))
        else:
            new_base = real_new_base

        # Check ACLs
        # to move an object we need the 'w' (write) right< on the virtual attribute base,
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

        zope.event.notify(ObjectChanged("pre object move", self.__base, dn=dn2str([str2dn(self.__base.dn, flags=ldap.DN_FORMAT_LDAPV3)[0]]) + "," + new_base))

        old_base = self.__base.dn

        self.create_missing_containers(real_new_base, base_dn, base_type)

        if recursive:

            try:
                child_new_base = dn2str([str2dn(self.__base.dn, flags=ldap.DN_FORMAT_LDAPV3)[0]]) + "," + new_base

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
                    new_child_base = dn2str(str2dn(new_child_dn, flags=ldap.DN_FORMAT_LDAPV3)[1:])

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

                zope.event.notify(ObjectChanged("post object move", self.__base, dn=self.__base.dn, orig_dn=old_base))
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
            zope.event.notify(ObjectChanged("post object move", self.__base, dn=self.__base.dn, orig_dn=old_base))
            return True

        except Exception as e:
            from traceback import print_exc
            print_exc()
            self.__log.error("moving object '%s' from '%s' to '%s' failed: %s" % (self.__base.uuid, old_dn, new_base, str(e)))
            return False

    def can_host(self, typ):
        return typ in self.__base._container_for

    def get_mode(self):
        return self.__base_mode

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
            children = index.search({"dn": ["%," + self.__base.dn]}, {'dn': 1})
            children = [c['dn'] for c in children]

            children.sort(key=len, reverse=True)

            for child in children:
                try:
                    c_obj = ObjectProxy(child)
                    c_obj.remove(recursive=True)
                except Exception as e:
                    self.__log.error("Error removing child %s: %s" % (child, str(e)))

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

    def commit(self, skip_write_hooks=False):
        if self.__read_only is True:
            # no changes in read-only mode
            return

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
        for idx in list(self.__retractions.keys()):
            if self.__initial_extension_state[idx]["active"]:
                self.__retractions[idx].retract()
            del self.__retractions[idx]

        # Check each extension before trying to save them
        check_props = self.__base.check()
        for extension in [ext for ext in self.__extensions.values() if ext]:
            check_props.update(extension.check(check_props))

        if self.__base_mode != "create":
            # we need a UUID to mark as dirty and thats only available in non creation mode
            index.mark_as_dirty(self)

        # Handle commits
        save_props = self.__base.commit()

        # Skip further actions if we're in create mode
        if self.__base_mode == "create":
            # update values
            self.dn = self.__base.dn
            self.uuid = self.__base.uuid
            index.mark_as_dirty(self)

        for extension in self.__extensions.values():
            if extension:
                # Populate the base uuid to the extensions
                if extension.uuid and extension.uuid != self.__base.uuid:
                    raise ProxyException(C.make_error('OBJECT_UUID_MISMATCH',
                                                      b_uuid=self.__base.uuid,
                                                      e_uuid=extension.uuid))
                if not extension.uuid:
                    extension.uuid = self.__base.uuid
                extension.dn = self.__base.dn
                save_props.update(extension.commit(save_props))

        # Did the commit result in a move?
        if self.__base_mode != "create" and self.dn != self.__base.dn:

            if children:
                # Move additional backends if needed
                for fbe, fdn in root_elements.items():

                    # Get new base of child
                    new_child_dn = fdn[:len(fdn) - len(old_base)] + self.__base.dn
                    new_child_base = dn2str(str2dn(new_child_dn, flags=ldap.DN_FORMAT_LDAPV3)[1:])

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

        changed_props = []

        for name, settings in save_props.items():
            if self.__base_mode == "update":
                if not self.__is_equal(settings['value'], settings['orig_value']):
                    self.__log.info("%s changed from %s to %s" % (name, settings['orig_value'], settings['value']))
                    changed_props.append(name)

            # only react to real changes here
            if skip_write_hooks is False and name in self.__attribute_change_write_hooks and settings['status'] == STATUS_CHANGED:
                for hook in self.__attribute_change_write_hooks[name]:
                    if hook["extension"] is not None and not self.is_extended_by(hook["extension"]):
                        self.__log.debug("skipping hook because object is not extended by %s" % hook["extension"])
                        continue

                    self.__log.debug("checking update hook for %s.%s" % (hook["notified_obj"], hook["notified_obj_attribute"]))
                    # Calculate value that have to be removed/added
                    remove = list(set(settings['orig_value']) - set(settings['value']))
                    add = list(set(settings['value']) - set(settings['orig_value']))
                    self.__log.debug("removing: %s" % remove)
                    self.__log.debug("adding: %s" % add)

                    if len(remove):
                        query = {"dn": {"in_": remove}}
                        if self.__factory.isBaseType(hook["notified_obj"]):
                            query["_type"] = hook["notified_obj"]
                        else:
                            query["extension"] = hook["notified_obj"]
                        res = index.search(query, {"dn": 1})
                        for x in res:
                            obj = ObjectProxy(x["dn"])
                            self.__log.debug("removing reference to %s from %s.%s" % (self.dn, obj.dn, hook["notified_obj_attribute"]))
                            setattr(obj, hook["notified_obj_attribute"], None)
                            obj.commit()

                    if len(add):
                        query = {"dn": {"in_": add}}
                        if self.__factory.isBaseType(hook["notified_obj"]):
                            query["_type"] = hook["notified_obj"]
                        else:
                            query["extension"] = hook["notified_obj"]
                        res = index.search(query, {"dn": 1})
                        for x in res:
                            obj = ObjectProxy(x["dn"])
                            self.__log.debug("adding reference to %s to %s.%s" % (self.dn, obj.dn, hook["notified_obj_attribute"]))
                            setattr(obj, hook["notified_obj_attribute"], self.dn)
                            obj.commit()

        zope.event.notify(ObjectChanged("post object %s" % self.__base_mode, self.__base, changed_props=changed_props))

    def __is_equal(self, val1, val2):
        return (val1 is None or val1 == []) and (val2 is None or val2 == []) or val1 == val2

    def is_changed(self, attribute_name):
        """
        Return True if the attribute value has been changed
        :param attribute_name: name of the attribute to check
        :return: True if changed False of not
        """
        # Valid attribute?
        if attribute_name not in self.__attribute_map:
            raise AttributeError(C.make_error('ATTRIBUTE_NOT_FOUND', attribute_name))
        else:
            # Load from primary object
            base_object = self.__attribute_map[attribute_name]['base']
            if self.__base_type == base_object:
                return self.__base.is_changed(attribute_name)

            # Check for extensions
            if base_object in self.__extensions and self.__extensions[base_object]:
                return self.__extensions[base_object].is_changed(attribute_name)

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
                if name in self.__attribute_change_hooks and self.__base.is_changed(name):
                    self.__execute_attribute_change_hook(name)
                continue

            # Forward attribute modification to all extension that provide
            # that given value (even if it is foreign)
            if obj in self.__extensions and self.__extensions[obj]:
                found = True
                setattr(self.__extensions[obj], name, value)
                continue

        if not found:
            raise AttributeError(C.make_error('ATTRIBUTE_NOT_FOUND', name))

    def __execute_attribute_change_hook(self, name):
        for hook in self.__attribute_change_hooks[name]:
            hook["hook"](*hook["params"])

    def revalidate_extension_condition(self, name, skip_event=False):
        """

        :param name: extension name
        :param index: condition index
        :param value: new property value that triggered the change
        :return:
        """
        condition = self.__base.extension_conditions[name]

        # check extension conditions
        # as the extension validators are always dependant from the base type we use only its properties here
        # the values of self.__attribute_map might not be up to date
        props_copy = copy.deepcopy(self.__base.myProperties)

        res, error = self.__base.processValidator(condition, "extension", self.__base_type, props_copy)
        changed = self.__initial_extension_state[name]["allowed"] != res
        self.__initial_extension_state[name]["allowed"] = res
        if skip_event is False and changed is True:
            e = EventMaker()
            event = e.Event(e.ExtensionAllowed(
                e.UUID(self.uuid if self.uuid is not None else ""),
                e.DN(self.dn if self.dn is not None else ""),
                e.ModificationTime(datetime.now().strftime("%Y%m%d%H%M%SZ")),
                e.ExtensionName(name),
                e.Allowed(str(res))
            ))
            event_object = objectify.fromstring(etree.tostring(event, pretty_print=True).decode('utf-8'))
            SseHandler.notify(event_object, channel="user.%s" % self.__current_user)

    def asJSON(self, only_indexed=False):
        """
        Returns JSON representations for the base-object and all its extensions.
        """
        atypes = self.__factory.getAttributeTypes()

        object_types = self.__factory.getObjectTypes()

        # Check permissions
        topic = "%s.objects.%s" % (self.__env.domain, self.__base_type)
        if self.__current_user is not None and not self.__acl_resolver.check(self.__current_user, topic, "r", base=self.dn):
            self.__log.debug("user '%s' has insufficient permissions for asJSON on %s, required is %s:%s" % (
                self.__current_user, self.dn, topic, "r"))
            raise ACLException(C.make_error('PERMISSION_ACCESS', topic, target=self.dn))

        res = {'dn': normalize_dn(self.__base.dn), '_type': self.__base.__class__.__name__,
               '_parent_dn': self.get_parent_dn(self.__base.dn),
               '_adjusted_parent_dn': self.get_adjusted_parent_dn(self.__base.dn),
               '_uuid': self.__base.uuid,
               '_invisible': object_types[self.__base.__class__.__name__]['invisible'],
               '_master_backend': getattr(self.__base, '_backend')}

        # Create non object pseudo attributes
        if self.__base.modifyTimestamp:
            res['_last_changed'] = time.mktime(self.__base.modifyTimestamp.timetuple())

        res['_extensions'] = [k for k in self.__extensions.keys() if self.__extensions[k]]

        props = self.__property_map
        for propname in self.__property_map:
            # only index attributes that are required for searching
            # if propname in self.__search_aid['used_attrs']:

            # Use the object-type conversion method to get valid item string-representations.
            prop_value = props[propname]['value']
            if props[propname]['type'] != "Binary":
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
            # only index attributes that are required for searching
            # if propname in self.__search_aid['used_attrs']:

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
from .object import ObjectChanged, Object, STATUS_CHANGED
