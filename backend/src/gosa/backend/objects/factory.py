# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

"""

Object Factory
==============

Short description
^^^^^^^^^^^^^^^^^

The object factory provides access to backend-data in an object
oriented way. You can create, read, update and delete objects easily.

What object-types are available is configured using XML files, these files
are located here: "src/gosa/backend/data/objects/".

Each XML file can contain multiple object definitions, with object related
information, like attributes, methods, how to store and read
objects.

(For a detailed documentation of the of XML files, please have a look at the
./doc directory)

A python meta-class will be created for each object-definition.
Those meta-classes will then be used to instantiate a new python object,
which will then provide the defined attributes, methods, aso.

Here are some examples on how to instantiate on new object:

>>> from gosa.backend.objects import ObjectFactory
>>> f = ObjectFactory.getInstance()
>>> person = f.getObject('Person', "410ad9f0-c4c0-11e0-962b-0800200c9a66")
>>> print person.sn
>>> person.sn = "Surname"
>>> person.commit()

"""
import pkg_resources
import os
import re
import json
import logging
import ldap
import html

from gosa.backend.objects.xml_parsing import XmlParsing
from lxml import etree, objectify
from gosa.common import Environment
from gosa.common.components import PluginRegistry
from gosa.common.utils import N_, cache_return
from gosa.common.error import GosaErrorHandler as C
from gosa.backend.objects.backend.registry import ObjectBackendRegistry
from gosa.backend.objects.object import Object
from gosa.backend.exceptions import FactoryException
from io import StringIO

# Status
STATUS_OK = 0
STATUS_CHANGED = 1

# Scopes
SCOPE_BASE = ldap.SCOPE_BASE
SCOPE_ONE = ldap.SCOPE_ONELEVEL
SCOPE_SUB = ldap.SCOPE_SUBTREE


# Register the errors handled  by us
C.register_codes(dict(
    OBJECT_TYPE_NO_BASE_TYPE=N_("'%(type)s' is no base type"),
    OBJECT_TYPE_NOT_FOUND=N_("Unknown object type '%(type)s'"),
    OBJECT_NO_BASE_FOUND=N_("Cannot find base object for type '%(type)s'"),
    BASE_OBJECT_NOT_FOUND=N_("No base type for attribute '%(attribute)s found'"),
    FACTORY_TYPE_MISMATCH=N_("Cannot identify '%(topic)s' - it seems to be of type '%(type1)s' and '%(type2)s' at the same time"),
    FACTORY_SCHEMA_ERROR=N_("Cannot load object schema"),
    FACTORY_BLOCK_BY_NON_EXISTING=N_("Attribute '%(topic)s' is blocked by non existing attribute '%(blocker)s'"),
    FACTORY_DEPEND_NON_EXISTING=N_("Attribute '%(topic)s' depends on non existing attribute '%(dependency)s'"),
    FACTORY_INVALID_METHOD_DEPENDS=N_("Method '%(method)s' depends on unknown attribute %(attribute)s"),
    FACTORY_PARAMETER_MISSING=N_("Parameter '%(parameter)s' for command '%(command)s' is missing"),
    ))


def load(attr, element, default=None):
    """
    Helper function for loading XML attributes with defaults.
    """
    if not element in attr.__dict__:
        return default

    return attr[element]


class ObjectFactory(object):
    """
    This class reads object definitions and generates python-meta classes
    for each object, which can then be instantiated using
    :meth:`gosa.backend.objects.factory.ObjectFactory.getObject`.
    """
    __instance = None
    __xml_defs = {}
    __classes = {}
    __var_regex = re.compile('^[a-z_][a-z0-9\-_]*$', re.IGNORECASE)
    __attribute_type = {}
    __object_types = {}
    __xml_objects_combined = None
    __class_names = []

    def __init__(self):
        self.env = Environment.getInstance()
        self.log = logging.getLogger(__name__)

        self.__xml_parsing = XmlParsing()

        # Initialize backend registry
        ObjectBackendRegistry.getInstance()

        # Load attribute type mapping
        for entry in pkg_resources.iter_entry_points("gosa.object.type"):
            module = entry.load()
            self.log.info("attribute type %s included" % module.__alias__)
            self.__attribute_type[module.__alias__] = module()

        # Initialize parser
        schema_path = pkg_resources.resource_filename('gosa.backend', 'data/object.xsd') #@UndefinedVariable
        schema_doc = open(schema_path, 'rb').read()

        # Prepare list of object types
        object_types = b""
        for o_type in self.__attribute_type.keys():
            object_types += b"<enumeration value=\"%s\"></enumeration>" % (o_type.encode(),)

        # Insert available object types into the xsd schema
        schema_doc = re.sub(b"<simpleType name=\"AttributeTypes\">\n?\s*<restriction base=\"string\"></restriction>\n?\s*</simpleType>",
            b"""
            <simpleType name="AttributeTypes">
              <restriction base="string">
                %(object_types)s
              </restriction>
            </simpleType>
            """ % {b'object_types': object_types},
            schema_doc)

        schema_root = etree.XML(schema_doc)
        schema = etree.XMLSchema(schema_root)
        self.__parser = objectify.makeparser(schema=schema)

        self.log.info("object factory initialized")

        # Load and parse schema
        self.load_schema()
        self.load_object_types()

    def getAttributeTypes(self):
        return self.__attribute_type

    def __get_class(self, name):
        if not name in self.__classes:
            self.__classes[name] = self.__build_class(name)
        return self.__classes[name]

    def create_classes(self):
        for name in self.__class_names:
            self.__get_class(name)

    def getObjectBackendProperties(self, name):
        return getattr(self.__get_class(name), "_backendAttrs")

    def getObjectProperties(self, name):
        return getattr(self.__get_class(name), "__properties")

    def getObjectMethods(self, name):
        return list(getattr(self.__get_class(name), "__methods").keys())

    def getXMLDefinitionsCombined(self):
        """
        Returns a complete XML of all defined objects.
        """
        return self.__xml_objects_combined

    def getIndexedAttributes(self):
        """
        Returns a list of attributes that have to be indexed.
        """
        res = []
        for element in self.__xml_defs.values():

            # Get all <Attribute> tags
            find = objectify.ObjectPath("Object.Attributes.Attribute")
            if find.hasattr(element):
                for attr in find(element):
                    res.append(attr.Name.text)

        return list(set(res))

    def getBinaryAttributes(self):
        """
        Returns a list of binary attributes
        """
        res = []
        for element in self.__xml_defs.values():

            # Get all <Attribute> tags
            find = objectify.ObjectPath("Object.Attributes.Attribute")
            if find.hasattr(element):
                for attr in find(element):
                    if attr.Type.text == "Binary":
                        res.append(attr.Name.text)

        return list(set(res))

    def getAvailableObjectNames(self, only_base_objects=False, base=None):
        """
        Returns a list with all available object names
        """
        if only_base_objects:
            return [name for name in self.__xml_defs.keys() if name in self.__object_types and self.__object_types[name]['base']
                    and not self.__object_types[name]['invisible']]
        else:
            return list(self.__xml_defs.keys())

    def getObjectTemplates(self, objectType):
        """
        Returns a list of templates for this object.
        """
        names = self.getObjectTemplateNames(objectType)
        return Object.getNamedTemplate(self.env, names)

    def getObjectDialogs(self, objectType):
        """
        Returns a list of templates for this object.
        """
        names = self.getObjectDialogNames(objectType)
        return Object.getNamedTemplate(self.env, names)

    def getObjectTemplateNames(self, objectType):
        """
        Returns a list of template filenames for this object.
        """
        if not objectType in self.__xml_defs:
            raise KeyError(C.make_error("OBJECT_TYPE_NOT_FOUND", type=objectType))

        res = []
        find = objectify.ObjectPath("Object.Templates.Template")
        if find.hasattr(self.__xml_defs[objectType]):
            for attr in find(self.__xml_defs[objectType]):
                res.append(attr.text)

        return res

    def getObjectDialogNames(self, objectType):
        """
        Returns a list of template filenames for this object.
        """
        if not objectType in self.__xml_defs:
            raise KeyError(C.make_error("OBJECT_TYPE_NOT_FOUND", type=objectType))

        res = []
        find = objectify.ObjectPath("Object.Dialogs.Dialog")
        if find.hasattr(self.__xml_defs[objectType]):
            for attr in find(self.__xml_defs[objectType]):
                res.append(attr.text)

        return res

    def getObjectSearchAid(self, objectType):
        """
        Returns a hash containing information about how to search for this
        object.
        """
        if not objectType in self.__xml_defs:
            raise KeyError(C.make_error("OBJECT_TYPE_NOT_FOUND", type=objectType))

        res = {}
        find = objectify.ObjectPath("Object.Find.Aspect")
        if find.hasattr(self.__xml_defs[objectType]):
            for attr in find(self.__xml_defs[objectType]):
                res['type'] = objectType
                res['tag'] = attr['Tag']

                res['search'] = []
                for s in attr['Search']:
                    res['search'].append(s.text)

                res['keyword'] = []
                for s in attr['Keyword']:
                    res['keyword'].append(s.text)

                res['resolve'] = []
                if "Resolve" in attr.__dict__:
                    for r in attr.Resolve:
                        res['resolve'].append(dict(attribute=r.text,
                            filter=r.attrib['filter'] if 'filter' in r.attrib else None,
                            type=r.attrib['type'] if 'type' in r.attrib else None))

                res['map'] = {}
                if 'Result' in attr.__dict__:
                    for r in attr['Result']:
                        for m in r['Map']:
                            res['map'][m['Destination'].text] = m['Source'].text

        return res

    def getAllowedSubElementsForObject(self, objectType, includeInvisible=False):
        """
        Returns a list of objects that can be stored as sub-objects for the given object.
        """
        if not objectType in self.__xml_defs:
            raise KeyError(C.make_error("OBJECT_TYPE_NOT_FOUND", type=objectType))

        if not self.__xml_defs[objectType]['BaseObject']:
            raise TypeError(C.make_error("OBJECT_TYPE_NO_BASE_TYPE", type=objectType))

        # Get list of allowed sub-elements
        res = []
        find = objectify.ObjectPath("Object.Container.Type")
        if find.hasattr(self.__xml_defs[objectType]):
            for attr in find(self.__xml_defs[objectType]):
                if attr.text in self.__object_types and self.__object_types[attr.text]['base']:
                    if self.__object_types[attr.text]['invisible']:
                        # look deeper
                        if includeInvisible:
                            res.append(attr.text)
                        res.extend(self.getAllowedSubElementsForObject(attr.text))
                    else:
                        res.append(attr.text)
        return res

    def getAllowedSubElementsForObjectWithActions(self, user, objectType):
        res = {}
        resolver = PluginRegistry.getInstance("ACLResolver")
        for type in self.getAllowedSubElementsForObject(objectType):
            actions = resolver.getAllowedActions(user, topic="%s.objects.%s" % (self.env.domain, type))
            if len(actions):
                res[type] = actions

        return res

    def getAttributeTypeMap(self, objectType):
        """
        Returns a mapping containing all attributes provided by
        the given object Type and the object-type they belong to.
        """
        if not objectType in self.__xml_defs:
            raise KeyError(C.make_error("OBJECT_TYPE_NOT_FOUND", type=objectType))

        if not self.__xml_defs[objectType]['BaseObject']:
            raise TypeError(C.make_error("OBJECT_TYPE_NO_BASE_TYPE", type=objectType))

        # Collect all object-types that can extend this class.
        find = objectify.ObjectPath("Object.Extends.Value")
        dependandObjectTypes = [objectType]
        for oc in self.__xml_defs:
            if find.hasattr(self.__xml_defs[oc]) and objectType in map(lambda x: x.text, find(self.__xml_defs[oc])):
                dependandObjectTypes.append(oc)

        # Get all <Attribute> tags and check if the property is not foreign
        res = {}
        for oc in dependandObjectTypes:
            find = objectify.ObjectPath("Object.Attributes.Attribute")
            if find.hasattr(self.__xml_defs[oc]):
                for attr in find(self.__xml_defs[oc]):
                    res[attr.Name.text] = oc
        return res

    def getReferences(self, s_obj=None, s_attr=None):
        """
        Returns a dictionary containing all attribute references.
        e.g. A groups memberlist may have references to users.

            {'PosixGroup': {'memberUid': [('PosixUser', 'uid')]}}
        """
        res = {}
        for element in self.__xml_defs.values():

            # Get all <Attributes> tag and iterate through their children
            find = objectify.ObjectPath("Object.Attributes")
            if find.hasattr(element):
                for attr in find(element).iterchildren():

                    # Extract the objects name.
                    obj = attr.getparent().getparent().Name.text

                    # Extract reference information
                    if load(attr, "References", None) is not None:

                        # Append the result if it matches the given parameters.
                        for ref in attr.References.iterchildren():
                            if (s_obj is None or s_obj == ref.Object.text) and (s_attr is None or s_attr == ref.Attribute.text):

                                # Ensure that values are initialized
                                if obj not in res:
                                    res[obj] = {}
                                if not attr.Name.text in res[obj]:
                                    res[obj][attr.Name.text] = []

                                mode = ref.attrib["mode"] if "mode" in ref.attrib else "replace"
                                pattern = {
                                    "identify": html.unescape(ref.attrib["identify-pattern"]) if "identify-pattern" in ref.attrib else None,
                                    "replace": html.unescape(ref.attrib["replace-pattern"]) if "replace-pattern" in ref.attrib else None,
                                    "delete": html.unescape(ref.attrib["delete-pattern"]) if "delete-pattern" in ref.attrib else None
                                }
                                if pattern["replace"] is None and pattern["identify"] is not None:
                                    pattern["replace"] = pattern["identify"]

                                res[obj][attr.Name.text].append((ref.Object.text, ref.Attribute.text, mode, pattern))

        return res

    def getUpdateHooks(self, base_type):
        res = {}
        for element in self.__xml_defs.values():

            # Get all <Attributes> tag and iterate through their children
            find = objectify.ObjectPath("Object.Attributes")
            if find.hasattr(element):
                for attr in find(element).iterchildren():

                    # Extract the objects name.
                    obj = attr.getparent().getparent().Name.text

                    # Extract reference information
                    if load(attr, "UpdateHooks", None) is not None:
                        for h in attr.UpdateHooks.iterchildren():
                            if self.__object_types[h["Object"].text]["base"] is False:
                                base_types = self.__object_types[h["Object"].text]["extends"]
                                extension = h["Object"].text
                            else:
                                base_types = [h["Object"].text]
                                extension = None

                        if base_type in base_types:
                                if not h["Attribute"].text in res:
                                    res[h["Attribute"].text] = []
                                for base_type in base_types:

                                    res[h["Attribute"].text].append({
                                        "notified_obj": obj,
                                        "extension": extension,
                                        "notified_obj_attribute": attr.Name.text
                                    })

        return res

    @cache_return()
    def __get_primary_class_for_foreign_attribute(self, attribute, obj):
        """
        Returns the primary class for a given primary attribute which belongs
        to the the given object (obj).

        e.g.    __get_primary_class_for_foreign_attribute("uidNumber", "PosixUser")
                would return "User"
        """

        # Find the base-object for the given object
        baseclass = None
        if obj in self.__xml_defs:

            # Is this class a base-object?
            # Then we can skip searching for the base-object of the given extension.
            if bool(load(self.__xml_defs[obj], "BaseObject", False)):
                baseclass = obj

            # Detect base-object for the given object
            else:
                find = objectify.ObjectPath("Object.Extends")
                if find.hasattr(self.__xml_defs[obj]):
                    for attr in find(self.__xml_defs[obj]).iterchildren():
                        baseclass = attr.text
                        break

            # No base class found
            if not baseclass:
                raise TypeError(C.make_error("OBJECT_NO_BASE_FOUND", type=obj))

            # Now find all possible extensions and check if they contain a primary-attribute with the given name
            for item in self.__xml_defs.values():
                find = objectify.ObjectPath("Object.Extends")
                if find.hasattr(item):
                    for ext in item["Extends"].iterchildren():
                        if ext.text == baseclass:
                            for attr in item["Attributes"].iterchildren():
                                if attr.tag == "{http://www.gonicus.de/Objects}Attribute" and attr["Name"] == attribute:
                                    return attr

                for attr in self.__xml_defs[baseclass]["Attributes"].iterchildren():
                    if attr.tag == "{http://www.gonicus.de/Objects}Attribute" and attr["Name"] == attribute:
                        return attr

            raise ValueError(C.make_error("BASE_OBJECT_NOT_FOUND", attribute=attribute))
        else:
            raise ValueError(C.make_error("OBJECT_TYPE_NOT_FOUND", type=obj))

    @cache_return()
    def get_attributes_by_object(self, object_name):
        """
        Extracts all attributes with their base/secondary classes.

        e.g.      get_attributes_by_object("User")
                    {'CtxCallback':       {'base': 'SambaUser', 'secondary': []},
                     'CtxCallbackNumber': {'base': 'SambaUser', 'secondary': []},
                     ...
                     'uid':               {'base': 'User',      'secondary': ['SambaUser', 'PosixUser']},
                     ...
        """

        # Helper method used to extract attributes and their base and secondary
        # classes.
        def extract_attrs(res, obj):
            find = objectify.ObjectPath("Object.Attributes")
            if find.hasattr(obj):
                for attr in find(obj).iterchildren():

                    # Skip comments in XML
                    if attr.tag == "comment":
                        continue

                    obj_name = attr.getparent().getparent().Name.text
                    if not attr.Name.text in res:
                        res[attr.Name.text] = {'base': None, 'secondary': []}

                    if attr.tag == "{http://www.gonicus.de/Objects}Attribute":
                        res[attr.Name.text]['base'] = obj_name
                    else:
                        res[attr.Name.text]['secondary'].append(obj_name)
            return res

        # Add base-object attributes
        res = {}
        if object_name in self.__xml_defs:
            if not bool(load(self.__xml_defs[object_name], "BaseObject", False)):
                raise TypeError(C.make_error("OBJECT_TYPE_NO_BASE_TYPE", type=object_name))

            res = extract_attrs(res, self.__xml_defs[object_name])
        else:
            raise TypeError(C.make_error("OBJECT_TYPE_NOT_FOUND", type=object_name))

        # Add extension attributes
        for element in self.__xml_defs.values():
            find = objectify.ObjectPath("Object.Extends")
            if find.hasattr(element):
                for extends in find(element).iterchildren():
                    if extends.text == object_name:
                        obj = extends.getparent().getparent()
                        res = extract_attrs(res, obj)
        return res

    @cache_return()
    def getAttributes(self):
        """
        Returns a list of all object-attributes
        Including information about primary/foreign attributes.
        """

        # Add primary attributes
        res = {}
        for element in self.__xml_defs.values():
            find = objectify.ObjectPath("Object.Attributes")
            if find.hasattr(element):
                for attr in find(element).iterchildren():
                    if attr.tag == "{http://www.gonicus.de/Objects}Attribute":
                        obj = attr.getparent().getparent().Name.text
                        if not attr.Name.text in res:
                            res[attr.Name.text] = {}

                        if not obj in res[attr.Name.text]:
                            res[attr.Name.text][obj] = {
                                'description': str(load(attr, "Description", "")),
                                'type': attr.Type.text,
                                'multivalue': bool(load(attr, "MultiValue", False)),
                                'mandatory': bool(load(attr, "Mandatory", False)),
                                'read-only': bool(load(attr, "ReadOnly", False)),
                                'case-sensitive': bool(load(attr, "CaseSensitive", False)),
                                'unique': bool(load(attr, "Unique", False)),
                                'objects': [],
                                'primary': [],
                                }
                            res[attr.Name.text][obj]['primary'].append(obj)

        # Add foreign attributes
        for element in self.__xml_defs.values():
            find = objectify.ObjectPath("Object.Attributes")
            if find.hasattr(element):
                for attr in find(element).iterchildren():
                    if attr.tag == "{http://www.gonicus.de/Objects}ForeignAttribute":
                        obj = attr.getparent().getparent().Name.text
                        if attr.Name.text in res:
                            for cls in res[attr.Name.text]:
                                res[attr.Name.text][cls]['objects'].append(obj)
        return res

    def load_object_types(self):
        types = {}
        extends = {}
        extension_conditions = {}

        # First, find all base objects
        # -> for every base object -> ask the primary backend to identify [true/false]
        for name, obj in self.__xml_defs.items():
            t_obj = obj
            is_base = bool(t_obj.BaseObject)
            backend = t_obj.Backend.text
            backend_attrs = self.__get_backend_parameters(t_obj)
            if "FixedRDN" in t_obj.__dict__:
                backend_attrs['FixedRDN'] = t_obj.FixedRDN.text

            methods = []
            if hasattr(t_obj, "Methods"):
                for method in t_obj.Methods.iterchildren():
                    methods.append(method.Name.text)

            types[name] = {
                'backend': backend,
                'backend_attrs': backend_attrs,
                'extended_by': [],
                'requires': [],
                'extension_conditions': {},
                'methods': methods,
                'base': is_base,
                'invisible': bool(t_obj.StructuralInvisible) if "StructuralInvisible" in t_obj.__dict__ else False
            }

            if "Extends" in t_obj.__dict__:
                types[t_obj.Name.text]['extends'] = [v.text for v in t_obj.Extends.Value]
                for ext in types[name]['extends']:
                    if ext not in extends:
                        extends[ext] = []
                    extends[ext].append(name)

            if "Container" in t_obj.__dict__:
                types[t_obj.Name.text]['container'] = [v.text for v in t_obj.Container.Type]

            if "RequiresExtension" in t_obj.__dict__:
                types[t_obj.Name.text]['requires'] = [v.text for v in t_obj.RequiresExtension.Extension]

            if "ExtensionConditions" in t_obj.__dict__:
                for ext_cond in t_obj.ExtensionConditions.ExtensionCondition:
                    if ext_cond.attrib["extension"] not in extension_conditions:
                        extension_conditions[ext_cond.attrib["extension"]] = {}
                    extension_conditions[ext_cond.attrib["extension"]][t_obj.Name.text] = self.__xml_parsing.build_filter(ext_cond)
                    if "properties" in ext_cond.attrib:
                        extension_conditions[ext_cond.attrib["extension"]][t_obj.Name.text]["properties"] = \
                            [x.strip() for x in ext_cond.attrib["properties"].split(",") if len(x)]

        for name, ext in extends.items():
            if name not in types:
                continue
            types[name]['extended_by'] = ext

        for name, entry in extension_conditions.items():
            if name not in types:
                continue
            types[name]['extension_conditions'] = entry

        self.__object_types = types

    def getObjectTypes(self):
        return self.__object_types

    def isBaseType(self, type):
        return self.__object_types[type]["base"]

    def identifyObject(self, dn):
        id_base = None
        id_base_fixed = None
        id_extend = []

        # First, find all base objects
        uuid = None
        for name, info in self.__object_types.items():
            be = ObjectBackendRegistry.getBackend(info['backend'])
            classr = self.__xml_defs[name]
            fixed_rdn = classr.FixedRDN.text if 'FixedRDN' in classr.__dict__ else None

            if info['base']:
                if be.identify(dn, info['backend_attrs'], fixed_rdn):
                    uuid = be.dn2uuid(dn)

                    if info['base']:
                        if fixed_rdn:
                            if id_base_fixed:
                                raise FactoryException(C.make_error("FACTORY_TYPE_MISMATCH", dn, type1=id_base, type2=name))
                            id_base_fixed = name

                        else:
                            if id_base:
                                raise FactoryException(C.make_error("FACTORY_TYPE_MISMATCH", dn, type1=id_base, type2=name))
                            id_base = name

        # .. then find all active extensions
        if uuid:
            for name, info in self.__object_types.items():

                if not name in self.__object_types[id_base]['extended_by']:
                    continue

                be = ObjectBackendRegistry.getBackend(info['backend'])
                classr = self.__xml_defs[name]
                fixed_rdn = classr.FixedRDN.text if 'FixedRDN' in classr.__dict__ else None
                if not info['base'] and (be.identify(dn, info['backend_attrs'], fixed_rdn) or
                                         be.identify_by_uuid(uuid, info['backend_attrs'])):
                    id_extend.append(name)

        if id_base or id_base_fixed:
            return id_base_fixed or id_base, id_extend

        return None, None

    def getObjectChildren(self, dn):
        res = {}

        # Identify possible children types
        ido = self.identifyObject(dn)
        if ido[0]:
            o_type = ido[0]
            o = self.__xml_defs[o_type]

            if 'Container' in o.__dict__:

                # Ask base backends for a one level query
                for c_type in o.Container.iterchildren():

                    if c_type.text not in self.__xml_defs:
                        continue

                    c = self.__xml_defs[c_type.text]

                    be = ObjectBackendRegistry.getBackend(c.Backend.text)
                    fixed_rdn = c.FixedRDN.text if 'FixedRDN' in c.__dict__ else None
                    for r in be.query(dn, scope=SCOPE_ONE,
                            params=self.__get_backend_parameters(c),
                            fixed_rdn=fixed_rdn):
                        res[r] = c_type.text

        else:
            self.log.warning("cannot identify child %s" % dn)

        return res

    def getObject(self, name, *args, **kwargs):
        """
        Returns a object instance.

        e.g.:

        >>> person = f.getObject('Person', "410ad9f0-c4c0-11e0-962b-0800200c9a66")

        """
        self.log.debug("object of type '%s' requested %s" % (name, args[0]))
        return self.__get_class(name)(*args, **kwargs)

    def load_schema(self):
        """
        This method reads all object defintion files (xml) and combines
        into one single xml-dump.

        This combined-xml-dump will then be forwarded to
        :meth:`gosa.backend.objects.factory.ObjectFactory.__parse_schema`
        to generate meta-classes for each object.

        This meta-classes can then be used to instantiate those objects.
        """
        path = pkg_resources.resource_filename('gosa.backend', 'data/objects') #@UndefinedVariable

        # Include built in schema
        schema_paths = []
        for f in [n for n in os.listdir(path) if n.endswith(os.extsep + 'xml')]:
            schema_paths.append(os.path.join(path, f))

        # Include additional schema configuration
        path = os.path.join(self.env.config.getBaseDir(), 'schema')
        if os.path.isdir(path):
            for f in [n for n in os.listdir(path) if n.endswith(os.extsep + 'xml')]:
                schema_paths.append(os.path.join(path, f))

        # Combine all object definition file into one single doc
        xstr = "<Paths xmlns=\"http://www.gonicus.de/Objects\">"
        for path in schema_paths:
            xstr += "<Path>%s</Path>" % path
        xstr += "</Paths>"

        # Now combine all files into one single xml construct
        xml_doc = etree.parse(StringIO(xstr))
        xslt_doc = etree.parse(pkg_resources.resource_filename('gosa.backend', 'data/combine_objects.xsl')) #@UndefinedVariable
        transform = etree.XSLT(xslt_doc)
        self.__xml_objects_combined = transform(xml_doc)
        self.__parse_schema(etree.tostring(self.__xml_objects_combined))

    def __parse_schema(self, schema):
        """
        Parses a schema definition
        :meth:`gosa.backend.objects.factory.ObjectFactory.__parser`
        method.
        """
        try:
            xml = objectify.fromstring(schema, self.__parser)
            find = objectify.ObjectPath("Objects.Object")
            if find.hasattr(xml):
                for attr in find(xml):
                    self.__xml_defs[attr['Name'].text] = attr
                    self.__class_names.append(attr['Name'].text)
                    self.log.info("loaded schema for '%s'" % attr['Name'].text)

        except etree.XMLSyntaxError as e:
            self.log.error("error loading object schema: %s" % str(e))
            raise FactoryException(C.make_error("FACTORY_SCHEMA_ERROR"))

    def __build_class(self, name):
        """
        This method builds a meta-class for each object definition read from the
        xml definition files.

        It uses a base-meta-class which will be extended by the define
        attributes and methods of the object.

        The final meta-class will be stored and can then be requested using:
        :meth:`gosa.backend.objects.factory.ObjectFactory.getObject`
        """

        self.log.debug("building meta-class for object-type '%s'" % (name,))

        class klass(Object):

            #noinspection PyMethodParameters
            def __init__(me, *args, **kwargs): #@NoSelf
                Object.__init__(me, *args, **kwargs)

            #noinspection PyMethodParameters
            def __setattr__(me, name, value): #@NoSelf
                me._setattr_(name, value)

            #noinspection PyMethodParameters
            def __getattr__(me, name): #@NoSelf
                return me._getattr_(name)

            #noinspection PyMethodParameters
            def __delattr__(me, name): #@NoSelf
                me._delattr_(name)

        # Collect Backend attributes per Backend
        classr = self.__xml_defs[name]
        back_attrs = {classr.Backend.text: {}}
        if "BackendParameters" in classr.__dict__:
            for entry in classr["BackendParameters"].Backend:
                back_attrs[entry.text] = entry.attrib

        # Collect extends lists. A list of objects that we can extend.
        extends = []
        if "Extends" in classr.__dict__:
            for entry in classr["Extends"].Value:
                extends.append(entry.text)

        # Load object properties like: is base object and allowed container elements
        base_object = bool(classr['BaseObject']) if "BaseObject" in classr.__dict__ else False
        container = []
        if "Container" in classr.__dict__:
            for entry in classr["Container"].Type:
                container.append(entry.text)

        # Load FixedRDN value
        fixed_rdn = None
        if "FixedRDN" in classr.__dict__:
            fixed_rdn = classr.FixedRDN.text
            back_attrs[classr.Backend.text]['FixedRDN'] = fixed_rdn

        setattr(klass, '__name__', name)
        setattr(klass, '_objectFactory', self)
        setattr(klass, '_backend', classr.Backend.text)
        setattr(klass, '_displayName', classr.DisplayName.text)
        setattr(klass, '_backendAttrs', back_attrs)
        setattr(klass, '_extends', extends)
        setattr(klass, 'extension_conditions', self.__object_types[name]["extension_conditions"]
                if name in self.__object_types and "extension_conditions" in self.__object_types[name] else None)
        setattr(klass, '_base_object', base_object)
        setattr(klass, '_container_for', container)

        # Prepare property and method list.
        props = {}
        methods = {}
        hooks = {}

        # Set template if available
        if 'Templates' in classr.__dict__:
            templates = []
            for template in classr.Templates.iterchildren():
                templates.append(template.text)

            setattr(klass, '_templates', templates)
        else:
            setattr(klass, '_templates', None)

        # Add documentation if available
        if 'Description' in classr.__dict__:
            setattr(klass, '_description', classr['Description'].text)

        # Load the backend and its attributes
        defaultBackend = classr.Backend.text

        # Append attributes
        if 'Attributes' in classr.__dict__:

            for prop in classr['Attributes'].iterchildren():

                # Skip xml parts that were commented-out
                if prop.tag == "comment":
                    continue

                self.log.debug("adding property: '%s'" % prop['Name'].text)

                # If this is a foreign attribute then load the definitions from its original class
                if prop.tag == "{http://www.gonicus.de/Objects}Attribute":
                    foreign = False
                else:
                    foreign = True
                    attrName = prop['Name'].text
                    prop = self.__get_primary_class_for_foreign_attribute(attrName, name)

                # Read backend definition per property (if it exists)
                backend = defaultBackend
                if "Backend" in prop.__dict__:
                    backend = prop.Backend.text

                # Prepare initial values
                out_f = []
                in_f = []
                blocked_by = []
                depends_on = []
                default = None
                validator = None
                backend_syntax = syntax = prop['Type'].text
                unique = bool(load(prop, "Unique", False))
                readonly = bool(load(prop, "ReadOnly", False))
                mandatory = bool(load(prop, "Mandatory", False))
                multivalue = bool(load(prop, "MultiValue", False))
                case_sensitive = bool(load(prop, "CaseSensitive", False))
                auto = bool(load(prop, "Auto", False))

                # Foreign attributes do not need any filters, validation or block settings
                # All this is done by its primary backend.
                if foreign:
                    mandatory = False
                else:

                    # Do we have an output filter definition?
                    if "OutFilter" in prop.__dict__:
                        for entry in  prop['OutFilter'].iterchildren():
                            self.log.debug(" appending out-filter")
                            of = self.__xml_parsing.handleFilterChain(entry)
                            out_f.append(of)

                    # Do we have a input filter definition?
                    if "InFilter" in prop.__dict__:
                        for entry in  prop['InFilter'].iterchildren():
                            self.log.debug(" appending in-filter")
                            in_f.append(self.__xml_parsing.handleFilterChain(entry))

                    # Read and build up validators
                    if "Validators" in prop.__dict__:
                        self.log.debug(" appending property validator")
                        validator = self.__xml_parsing.build_filter(prop['Validators'])

                    # Read the properties syntax
                    if "BackendType" in prop.__dict__:
                        backend_syntax = prop['BackendType'].text

                    # Read blocked by settings - When they are fullfilled, these property cannot be changed.
                    if "BlockedBy" in prop.__dict__:
                        for d in prop.__dict__['BlockedBy'].iterchildren():
                            blocked_by.append({'name': d.text, 'value': d.attrib['value']})

                    # Convert the default to the corresponding type.
                    if "Default" in prop.__dict__:
                        default = self.__attribute_type[syntax].convert_from('String', [prop.Default.text])

                    # Check for property dependencies
                    if "DependsOn" in prop.__dict__:
                        for d in prop.__dict__['DependsOn'].iterchildren():
                            depends_on.append(d.text)

                # Check for valid value list
                values = []
                values_populate = None
                re_populate_on_update = False
                skip_translation_values = []
                if "Values" in prop.__dict__:
                    values = {}

                    if 'populate' in prop.__dict__['Values'].attrib:
                        values_populate = prop.__dict__['Values'].attrib['populate']
                        if 'refresh-on-update' in prop.__dict__['Values'].attrib:
                            re_populate_on_update = prop.__dict__['Values'].attrib['refresh-on-update'].lower() == "true"
                    else:
                        for d in prop.__dict__['Values'].iterchildren():
                            if 'key' in d.attrib:
                                values[self.__attribute_type['String'].convert_to(syntax, [d.attrib['key']])[0]] = d.text
                            else:
                                values[self.__attribute_type['String'].convert_to(syntax, [d.text])[0]] = d.text

                            if 'translate' in d.attrib and d.attrib["translate"] == "false":
                                # never translate this value
                                skip_translation_values.append(d.text)

                value_inherited_from = None
                if 'InheritFrom' in prop.__dict__:
                    value_inherited_from = {
                        "rpc": prop["InheritFrom"].text,
                        "reference_attribute": prop.__dict__['InheritFrom'].attrib['relation']
                    }

                # Create a new property with the given information
                props[prop['Name'].text] = {
                    'value': [],
                    'values': values,
                    'skip_translation_values': skip_translation_values,
                    'values_populate': values_populate,
                    're_populate_on_update': re_populate_on_update,
                    'status': STATUS_OK,
                    'depends_on': depends_on,
                    'type': syntax,
                    'backend_type': backend_syntax,
                    'validator': validator,
                    'out_filter': out_f,
                    'in_filter': in_f,
                    'backend': [backend],
                    'in_value': [],
                    'default': default,
                    'orig_value': None,
                    'foreign': foreign,
                    'unique': unique,
                    'mandatory': mandatory,
                    'readonly': readonly,
                    'case_sensitive': case_sensitive,
                    'multivalue': multivalue,
                    'blocked_by': blocked_by,
                    'auto': auto,
                    'value_inherited_from': value_inherited_from}

        # Validate the properties 'depends_on' and 'blocked_by' lists
        for pname in props:

            # Blocked by
            for bentry in props[pname]['blocked_by']:

                # Does the blocking property exists?
                if bentry['name'] not in props:
                    raise FactoryException(C.make_error("FACTORY_BLOCK_BY_NON_EXISTING", pname, blocker=bentry['name']))

                # Convert the blocking condition to its expected value-type
                syntax = props[bentry['name']]['type']
                if bentry['value'] == "null":
                    bentry['value'] = None
                else:
                    bentry['value'] = self.__attribute_type['String'].convert_to(syntax, [bentry['value']])[0]

            # Depends on
            for dentry in props[pname]['depends_on']:
                if dentry not in props:
                    raise FactoryException(C.make_error("FACTORY_DEPEND_NON_EXISTING", pname, dependency=dentry))

        # Build up a list of callable methods
        if 'Methods' in classr.__dict__:
            for method in classr['Methods']['Method']:

                # Extract method information out of the xml tag
                methodName = method['Name'].text
                command = method['Command'].text

                # Get the list of method parameters
                mParams = []
                if 'MethodParameters' in method.__dict__:

                    # Todo: Check type of the property and handle the
                    # default value.

                    for param in method['MethodParameters']['MethodParameter']:
                        pName = param['Name'].text
                        pType = param['Type'].text
                        pRequired = bool(load(param, "Required", False))
                        pDefault = str(load(param, "Default"))
                        mParams.append((pName, pType, pRequired, pDefault))

                # Get the list of command parameters
                cParams = []
                if 'CommandParameters' in method.__dict__:
                    for param in method['CommandParameters']['Value']:
                        cParams.append(param.text)

                # Append the method to the list of registered methods for this
                # object
                self.log.debug("adding method: '%s'" % (methodName, ))
                cr = PluginRegistry.getInstance('CommandRegistry')
                methods[methodName] = {'ref': self.__create_class_method(klass, methodName, command, mParams, cParams,
                                                                         cr.callNeedsUser(command),
                                                                         cr.callNeedsSession(command))}

        # Build list of hooks
        if 'Hooks' in classr.__dict__:
            for method in classr['Hooks']['Hook']:

                # Extract method information out of the xml tag
                command = method['Command'].text
                m_type = method['Type'].text

                # Get the list of command parameters
                cParams = []
                if 'CommandParameters' in method.__dict__:
                    for param in method['CommandParameters']['Value']:
                        cParams.append(param.text)

                # Append the method to the list of registered methods for this
                # object
                self.log.debug("adding %s-hook with command '%s'" % (m_type, command))
                if not m_type in hooks:
                    hooks[m_type] = []
                hooks[m_type].append({'ref': self.__create_hook(klass, m_type, command, cParams)})

        # Set properties and methods for this object.
        setattr(klass, '__properties', props)
        setattr(klass, '__methods', methods)
        setattr(klass, '__hooks', hooks)
        return klass

    def __create_hook(self, klass, m_type, command, cParams):
        """
        Creates a new executable hook-method for the current object.
        """

        # Now add the method to the object
        def funk(caller_object, *args, **kwargs):

            # Load the objects actual property set
            props = caller_object.myProperties
            cloned_props = {}
            if "props" in kwargs:
                # this is the cloned property set with applied out filters (which might have changed the original values)
                cloned_props = kwargs["props"]

            # Build the command-parameter list.
            # Collect all property values of this object to be able to fill in
            # placeholders in command-parameters later.
            propList = {}
            for key in props:
                if props[key]['value']:
                    propList[key] = props[key]['value'][0]
                else:
                    propList[key] = None
                if key in cloned_props and cloned_props[key]['value']:
                    propList[key] = cloned_props[key]['value'][0]

            # Fill in the placeholders of the command-parameters now.
            parmList = []
            for value in cParams:
                if value in propList:
                    parmList.append(propList[value])
                elif value in ['dn', 'uuid']:
                    parmList.append(getattr(caller_object, value))
                else:
                    raise FactoryException(C.make_error("FACTORY_INVALID_METHOD_DEPENDS", method=command, attribute=value))

            cr = PluginRegistry.getInstance('CommandRegistry')
            self.log.info("Executed %s-hook for class %s which invoked %s(...)" % (m_type, klass.__name__, command))

            return cr.call(command, *parmList)

        return funk

    def __create_class_method(self, klass, methodName, command, mParams, cParams, needsUser=False, needsSession=False):
        """
        Creates a new klass-method for the current objekt.
        """

        # Now add the method to the object
        def funk(caller_object, *args, **kwargs):

            # Load the objects actual property set
            props = caller_object.myProperties

            # Convert all given parameters into named arguments
            # The eases up things a lot.
            cnt = 0
            arguments = {}
            for mParam in mParams:
                mName, mType, mRequired, mDefault = mParam #@UnusedVariable
                if mName in kwargs:
                    arguments[mName] = kwargs[mName]
                elif cnt < len(args):
                    arguments[mName] = args[cnt]
                elif mDefault:
                    arguments[mName] = mDefault
                else:
                    raise FactoryException(C.make_error("FACTORY_PARAMETER_MISSING", command=command, parameter=mName))

                # Convert value to its required type.
                arguments[mName] = self.__attribute_type['String'].convert_to(mType, [arguments[mName]])[0]
                cnt += 1

            # Build the command-parameter list.
            # Collect all property values of this object to be able to fill in
            # placeholders in command-parameters later.
            propList = {}
            for key in props:
                if props[key]['value']:
                    propList[key] = props[key]['value'][0]
                else:
                    propList[key] = None

            # Add method-parameters passed to this method.
            for entry in arguments:
                propList[entry] = arguments[entry]

            # Fill in the placeholders of the command-parameters now.
            parmList = []
            for value in cParams:
                if value in propList:
                    parmList.append(propList[value])
                elif value in ['dn']:
                    parmList.append(getattr(caller_object, value))
                elif value in ['__self__']:
                    parmList.append(caller_object.parent)
                else:
                    raise FactoryException(C.make_error("FACTORY_INVALID_METHOD_DEPENDS", method=command, attribute=value))

            cr = PluginRegistry.getInstance('CommandRegistry')
            self.log.info("Executed %s.%s which invoked %s(%s)" % (klass.__name__, methodName, command, parmList))

            if not needsSession and not needsUser:
                return cr.call(command, *parmList)

            # Do we need a user / session_id specification?
            args = []
            if needsUser:
                args.append(caller_object._owner)
            else:
                args.append(cr)
            if needsSession:
                args.append(caller_object._session_id)
            else:
                args.append(None)

            args.append(command)
            args.extend(parmList)
            return cr.dispatch(*args)

        return funk

    @staticmethod
    def getInstance():
        if not ObjectFactory.__instance:
            ObjectFactory.__instance = ObjectFactory()

        return ObjectFactory.__instance

    def __get_backend_parameters(self, obj):
        backend_attrs = {}

        if "BackendParameters" in obj.__dict__:
            for bp in obj.BackendParameters.Backend:
                if bp.text == obj.Backend:
                    backend_attrs = bp.attrib
                    break

        return backend_attrs

    def getXMLSchema(self, obj):
        """
        Returns a xml-schema for the requested object.
        """
        return self.__xml_defs[obj] if obj in self.__xml_defs else None

    def getXMLObjectSchema(self, asString=False):
        """
        Returns a xml-schema definition that can be used to validate the
        xml-objects returned by 'asXML()'
        """
        # Transform xml-combination into a useable xml-class representation
        xmldefs = self.getXMLDefinitionsCombined()
        xslt_doc = etree.parse(pkg_resources.resource_filename('gosa.backend', 'data/xml_object_schema.xsl')) #@UndefinedVariable
        transform = etree.XSLT(xslt_doc)
        if not asString:
            return transform(xmldefs)
        else:
            return etree.tostring(transform(xmldefs))

    def getNamedI18N(self, templates, language=None):
        if not language:
            return {}

        env = Environment.getInstance()
        i18n = None
        locales = []
        if "-" in language:
            tmp = language.split("-")
            locales.append(tmp[0].lower() + "_" + tmp[0].upper())
            locales.append(tmp[0].lower())
        else:
            locales.append(language)

        # If there's a i18n file, try to find it
        res = {}

        if templates:
            for template in templates:
                paths = []

                # Absolute path
                if template.startswith(os.path.sep):
                    tp = os.path.dirname(template)
                    tn = os.path.basename(template)[:-5]
                    for loc in locales:
                        paths.append(os.path.join(tp, "i18n", tn, "%s.json" % loc))

                # Relative path
                else:
                    tn = os.path.basename(template)[:-5]

                    # Find path
                    for loc in locales:
                        paths.append(pkg_resources.resource_filename('gosa.backend', os.path.join('data', 'templates', "i18n", tn, "%s.json" % loc))) #@UndefinedVariable
                        paths.append(os.path.join(env.config.getBaseDir(), 'templates', 'i18n', tn, "%s.json" % loc))

                for path in paths:
                    if os.path.exists(path):
                        with open(path, "rb") as f:
                            i18n = f.read()
                        break

                if i18n:
                    res = {**res, **json.loads(i18n.decode('utf-8'))}

        return res

    def getObjectBackendParameters(self, name, attribute):
        """
        Helper method to extract backendParameter infos
        """
        attrs = self.getObjectBackendProperties(name)

        for be in attrs:
            if attribute in attrs[be]:
                result = {}
                for targetAttr in attrs[be]:
                    res = re.match("^([^:]*):([^,]*)(,([^=]*)=([^,]*))?", attrs[be][targetAttr])
                    if res:
                        result[targetAttr] = []
                        result[targetAttr].append(res.groups()[0])
                        result[targetAttr].append(res.groups()[1])
                        result[targetAttr].append(res.groups()[3])
                        result[targetAttr].append(res.groups()[4])

                return result

        return None

    def getObjectNamesWithBackendSetting(self, backend_name, attribute_name, attribute_value):
        """
        Helper method to find object types with certain backend parameter settings.
        e.g. find all objects with a special foreman backend type setting
        """
        res = []
        for object_name in self.getObjectTypes().keys():
            attrs = self.getObjectBackendProperties(object_name)
            if backend_name in attrs and attribute_name in attrs[backend_name] and attrs[backend_name][attribute_name] == attribute_value:
                res.append(object_name)

        return res

