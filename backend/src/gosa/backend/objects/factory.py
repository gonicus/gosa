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

What object-types are avaialable is configured using XML files, these files
are located here: "src/gosa/backend/data/objects/".

Each XML file can contain multiple object definitions, with object related
information, like attributes, methods, how to store and read
objects.

(For a detailed documentation of the of XML files, please have a look at the
./doc directory)

A python meta-class will be created for each object-definition.
Those meta-classes will then be used to instantiate a new python object,
which will then provide the defined attributes, methods, aso.

Here are some examples on how to instatiate on new object:

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
import logging
import ldap
from lxml import etree, objectify
from gosa.common import Environment
from gosa.common.components import PluginRegistry
from gosa.common.utils import N_
from gosa.common.error import GosaErrorHandler as C
from gosa.backend.objects.filter import get_filter
from gosa.backend.objects.backend.registry import ObjectBackendRegistry
from gosa.backend.objects.comparator import get_comparator
from gosa.backend.objects.operator import get_operator
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
    FACTORY_TYPE_MISMATCH=N_("Cannot identify '%(topic)s' - it seems to be of type '%(type1)s and %(type2)s at the same time'"),
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
    This class reads object defintions and generates python-meta classes
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

    def __init__(self):
        self.env = Environment.getInstance()
        self.log = logging.getLogger(__name__)

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

    def getObjectBackendProperties(self, name):
        if not name in self.__classes:
            self.__classes[name] = self.__build_class(name)

        return getattr(self.__classes[name], "_backendAttrs")

    def getObjectProperties(self, name):
        if not name in self.__classes:
            self.__classes[name] = self.__build_class(name)

        return getattr(self.__classes[name], "__properties")

    def getObjectMethods(self, name):
        if not name in self.__classes:
            self.__classes[name] = self.__build_class(name)

        return list(getattr(self.__classes[name], "__methods").keys())

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

    def getAvailableObjectNames(self):
        """
        Retuns a list with all available object names
        """
        return self.__xml_defs.keys()

    def getObjectTemplates(self, objectType, theme="default"):
        """
        Returns a list of templates for this object.
        """
        names = self.getObjectTemplateNames(objectType)
        return Object.getNamedTemplate(self.env, names, theme)

    def getObjectDialogs(self, objectType, theme="default"):
        """
        Returns a list of templates for this object.
        """
        names = self.getObjectDialogNames(objectType)
        return Object.getNamedTemplate(self.env, names, theme)

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
                for r in attr['Result']:
                    for m in r['Map']:
                        res['map'][m['Destination'].text] = m['Source'].text

        return res

    def getAllowedSubElementsForObject(self, objectType):
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
                res.append(attr.text)
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

                                res[obj][attr.Name.text].append((ref.Object.text, ref.Attribute.text))

        return res

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
                                'description': attr.Description.text,
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

        # First, find all base objects
        # -> for every base object -> ask the primary backend to identify [true/false]
        for name, obj in self.__xml_defs.items():
            t_obj = obj
            is_base = bool(t_obj.BaseObject)
            backend = t_obj.Backend.text
            backend_attrs = self.__get_backend_parameters(t_obj)

            methods = []
            if hasattr(t_obj, "Methods"):
                for method in t_obj.Methods.iterchildren():
                    methods.append(method.Name.text)

            types[name] = {
                'backend': backend,
                'backend_attrs': backend_attrs,
                'extended_by': [],
                'requires': [],
                'methods': methods,
                'base': is_base,
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

        for name, ext in extends.items():
            if not name in types:
                continue
            types[name]['extended_by'] = ext

        self.__object_types = types

    def getObjectTypes(self):
        return self.__object_types

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
        self.log.debug("object of type '%s' requested %s" % (name, args))
        if not name in self.__classes:
            self.__classes[name] = self.__build_class(name)

        return self.__classes[name](*args, **kwargs)

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
                    self.log.info("loaded schema for '%s'" % attr['Name'].text)

        except etree.XMLSyntaxError as e:
            self.log.error("error loading object schema: %s" % str(e))
            raise FactoryException(C.make_error("FACTORY_SCHEMA_ERROR"))

    def __build_class(self, name):
        """
        This method builds a meta-class for each object defintion read from the
        xml defintion files.

        It uses a base-meta-class which will be extended by the define
        attributes and mehtods of the object.

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
            for entry in classr["Extends"]:
                extends.append(entry.Value.text)

        # Load object properties like: is base object and allowed container elements
        base_object = bool(classr['BaseObject']) if "BaseObject" in classr.__dict__ else False
        container = []
        if "Container" in classr.__dict__:
            for entry in classr["Container"]:
                container.append(entry.Type.text)

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

                # Foreign attributes do not need any filters, validation or block settings
                # All this is done by its primary backend.
                if foreign:
                    mandatory = False
                else:

                    # Do we have an output filter definition?
                    if "OutFilter" in prop.__dict__:
                        for entry in  prop['OutFilter'].iterchildren():
                            self.log.debug(" appending out-filter")
                            of = self.__handleFilterChain(entry)
                            out_f.append(of)

                    # Do we have a input filter definition?
                    if "InFilter" in prop.__dict__:
                        for entry in  prop['InFilter'].iterchildren():
                            self.log.debug(" appending in-filter")
                            in_f.append(self.__handleFilterChain(entry))

                    # Read and build up validators
                    if "Validators" in prop.__dict__:
                        self.log.debug(" appending property validator")
                        validator = self.__build_filter(prop['Validators'])

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
                if "Values" in prop.__dict__:
                    avalues = []
                    dvalues = {}

                    if 'populate' in prop.__dict__['Values'].attrib:
                        values_populate = prop.__dict__['Values'].attrib['populate']
                    else:
                        for d in prop.__dict__['Values'].iterchildren():
                            if 'key' in d.attrib:
                                dvalues[self.__attribute_type['String'].convert_to(syntax, [d.attrib['key']])[0]] = d.text
                            else:
                                avalues.append(d.text)

                    if avalues:
                        values = self.__attribute_type['String'].convert_to(syntax, avalues)
                    else:
                        values = dvalues

                    #values = self.__attribute_type['String'].convert_to(syntax, values)

                # Create a new property with the given information
                props[prop['Name'].text] = {
                    'value': [],
                    'values': values,
                    'values_populate': values_populate,
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
                    'blocked_by': blocked_by}

        # Validate the properties 'depends_on' and 'blocked_by' lists
        for pname in props:

            # Blocked by
            for bentry in props[pname]['blocked_by']:

                # Does the blocking property exists?
                if bentry['name'] not in props:
                    raise FactoryException(C.make_error("FACTORY_BLOCK_BY_NON_EXISTING", pname, blocker=bentry['name']))

                # Convert the blocking condition to its expected value-type
                syntax = props[bentry['name']]['type']
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
                methods[methodName] = {'ref': self.__create_class_method(klass, methodName, command, mParams, cParams, cr.callNeedsUser(command))}

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
        Creates a new executeable hook-method for the current objekt.
        """

        # Now add the method to the object
        def funk(caller_object, *args, **kwargs):

            # Load the objects actual property set
            props = caller_object.myProperties

            # Build the command-parameter list.
            # Collect all property values of this object to be able to fill in
            # placeholders in command-parameters later.
            propList = {}
            for key in props:
                if props[key]['value']:
                    propList[key] = props[key]['value'][0]
                else:
                    propList[key] = None

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

    def __create_class_method(self, klass, methodName, command, mParams, cParams, needsUser=False):
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
            self.log.info("Executed %s.%s which invoked %s(...)" % (klass.__name__, methodName, command))

            # Do we need a user specification?
            if needsUser:
                return cr.dispatch(caller_object.owner, None, command, *parmList)

            return cr.call(command, *parmList)
        return funk

    def __build_filter(self, element, out=None):
        """
        Attributes of objects can be filtered using in- and out-filters.
        These filters can manipulate the raw-values while they are read form
        the backend or they can manipulate values that have to be written to
        the backend.

        This method converts the read XML filter-elements of the defintion into
        a process lists. This list can then be easily executed line by line for
        each property, using the method:

        :meth:`gosa.backend.objects.object.Object.__processFilter`

        """

        # Parse each <FilterChain>, <Condition>, <ConditionChain>
        out = {}
        for el in element.iterchildren():
            if el.tag == "{http://www.gonicus.de/Objects}FilterChain":
                out = self.__handleFilterChain(el, out)
            elif  el.tag == "{http://www.gonicus.de/Objects}Condition":
                out = self.__handleCondition(el, out)
            elif  el.tag == "{http://www.gonicus.de/Objects}ConditionOperator":
                out = self.__handleConditionOperator(el, out)

        return out

    def __handleFilterChain(self, element, out=None):
        """
        This method is used in '__build_filter' to generate a process
        list for the in and out filters.

        The 'FilterChain' element is handled here.

        Occurrence: OutFilter->FilterChain
        """
        if not out:
            out = {}

        # FilterChains can contain muliple "FilterEntry" tags.
        # But at least one.
        # Here we forward these elements to their handler.
        for el in element.iterchildren():
            if el.tag == "{http://www.gonicus.de/Objects}FilterEntry":
                out = self.__handleFilterEntry(el, out)
        return out

    def __handleFilterEntry(self, element, out):
        """
        This method is used in '__build_filter' to generate a process
        list for the in and out filters.

        The 'FilterEntry' element is handled here.

        Occurrence: OutFilter->FilterChain->FilterEntry
        """

        # FilterEntries contain a "Filter" OR a "Choice" tag.
        # Here we forward the elements to their handler.
        for el in element.iterchildren():
            if el.tag == "{http://www.gonicus.de/Objects}Filter":
                out = self.__handleFilter(el, out)
            elif el.tag == "{http://www.gonicus.de/Objects}Choice":
                out = self.__handleChoice(el, out)
        return out

    def __handleFilter(self, element, out):
        """
        This method is used in '__build_filter' to generate a process
        list for the in and out filters.

        The 'Filter' element is handled here.

        Occurrence: OutFilter->FilterChain->FilterEntry->Filter
        """

        # Get the <Name> and the <Param> element values to be able
        # to create a process list entry.
        name = element.__dict__['Name'].text
        params = []
        for entry in element.iterchildren():
            if entry.tag == "{http://www.gonicus.de/Objects}Param":
                params.append(entry.text)

        # Attach the collected filter and parameter value to the process list.
        cnt = len(out) + 1
        out[cnt] = {'filter': get_filter(name)(self), 'params': params}
        return out

    def __handleChoice(self, element, out):
        """
        This method is used in '__build_filter' to generate a process
        list for the in and out filters.

        The 'Choice' element is handled here.

        Occurrence: OutFilter->FilterChain->FilterEntry->Choice
        """

        # We just forward <When> tags to their handler.
        for el in element.iterchildren():
            if el.tag == "{http://www.gonicus.de/Objects}When":
                out = self.__handleWhen(el, out)
        return out

    def __handleWhen(self, element, out):
        """
        This method is used in '__build_filter' to generate a process
        list for the in and out filters.

        The 'When' element is handled here.

        Occurrence: OutFilter->FilterChain->FilterEntry->Choice->When
        """

        # (<When> tags contain a <ConditionChain>, a <FilterChain> tag and
        # an optional <Else> tag.
        #  The <FilterChain> is only executed when the <ConditionChain> matches
        #  the given values.)

        # Forward the tags to their correct handler.
        filterChain = {}
        elseChain = {}
        for el in element.iterchildren():
            if el.tag == "{http://www.gonicus.de/Objects}ConditionChain":
                out = self.__handleConditionChain(el, out)
            if el.tag == "{http://www.gonicus.de/Objects}FilterChain":
                filterChain = self.__handleFilterChain(el, filterChain)
            elif el.tag == "{http://www.gonicus.de/Objects}Else":
                elseChain = self.__handleElse(el, elseChain)

        # Collect jump points
        cnt = len(out)
        match = cnt + 2
        endMatch = match + len(filterChain)
        noMatch = endMatch + 1
        endNoMatch = noMatch + len(elseChain)

        # Add jump point for this condition
        cnt = len(out)
        out[cnt + 1] = {'jump': 'conditional', 'onTrue': match, 'onFalse': noMatch}

        # Add the <FilterChain> process.
        cnt = len(out)
        for entry in filterChain:
            cnt += 1
            out[cnt] = filterChain[entry]

        # Add jump point to jump over the else chain
        cnt = len(out)
        out[cnt + 1] = {'jump': 'non-conditional', 'to': endNoMatch}

        # Add the <Else> process.
        cnt = len(out)
        for entry in elseChain:
            cnt += 1
            out[cnt] = elseChain[entry]

        return out

    def __handleElse(self, element, out):
        """
        This method is used in '__build_filter' to generate a process
        list for the in and out filters.

        The 'Else' element is handled here.

        Occurrence: OutFilter->FilterChain->FilterEntry->Choice->Else
        """

        # Handle <FilterChain> elements of this else tree.
        for el in element.iterchildren():
            if el.tag == "{http://www.gonicus.de/Objects}FilterChain":
                out = self.__handleFilterChain(el, out)

        return out

    def __handleConditionChain(self, element, out):
        """
        This method is used in '__build_filter' to generate a process
        list for the in and out filters.

        The 'ConditionChain' element is handled here.

        Occurrence: OutFilter->FilterChain->FilterEntry->Choice->When->ConditionChain
        """

        # Forward <Condition> tags to their handler.
        for el in element.iterchildren():
            if el.tag == "{http://www.gonicus.de/Objects}Condition":
                out = self.__handleCondition(el, out)
            elif el.tag == "{http://www.gonicus.de/Objects}ConditionOperator":
                out = self.__handleConditionOperator(el, out)

        return out

    def __handleConditionOperator(self, element, out):
        """
        This method is used in '__build_filter' to generate a process
        list for the in and out filters.

        The 'ConditionOperator' element is handled here.

        Occurrence: OutFilter->FilterChain->FilterEntry->Choice->When->ConditionChain->ConditionOperator
        """

        # Forward <Left and <RightConditionChains> to the ConditionChain handler.
        out = self.__handleConditionChain(element.__dict__['LeftConditionChain'], out)
        out = self.__handleConditionChain(element.__dict__['RightConditionChain'], out)

        # Append operator
        cnt = len(out)
        if element.__dict__['Operator'] == "or":
            out[cnt + 1] = {'operator': get_operator('Or')(self)}
        else:
            out[cnt + 1] = {'operator': get_operator('And')(self)}

        return out

    def __handleCondition(self, element, out):
        """
        This method is used in '__build_filter' to generate a process
        list for the in and out filters.

        The 'Condition' element is handled here.

        Occurrence: OutFilter->FilterChain->FilterEntry->Choice->When->ConditionChain->Condition
        """

        # Get the condition name and the parameters to use.
        # The name of the condition specifies which ElementComparator
        # we schould use.
        name = element.__dict__['Name'].text
        params = []
        for entry in element.iterchildren():
            if entry.tag == "{http://www.gonicus.de/Objects}Param":
                params.append(entry.text)

        # Append the condition to the process list.
        cnt = len(out) + 1
        out[cnt] = {'condition': get_comparator(name)(self), 'params': params}
        return out

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

    def getNamedI18N(self, templates, language=None, theme="default"):
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
                    tn = os.path.basename(template)[:-3]
                    for loc in locales:
                        paths.append(os.path.join(tp, "i18n", "%s_%s.ts" % (tn, loc)))

                # Relative path
                else:
                    tn = os.path.basename(template)[:-3]

                    # Find path
                    for loc in locales:
                        paths.append(pkg_resources.resource_filename('gosa.backend', os.path.join('data', 'templates', theme, "i18n", "%s_%s.ts" % (tn, loc)))) #@UndefinedVariable
                        paths.append(os.path.join(env.config.getBaseDir(), 'templates', theme, "%s_%s.ts" % (tn, loc)))
                        paths.append(pkg_resources.resource_filename('gosa.backend', os.path.join('data', 'templates', "default", "i18n", "%s_%s.ts" % (tn, loc)))) #@UndefinedVariable
                        paths.append(os.path.join(env.config.getBaseDir(), 'templates', "default", "%s_%s.ts" % (tn, loc)))

                for path in paths:
                    if os.path.exists(path):
                        with open(path, "r") as f:
                            i18n = f.read()
                        break

                if i18n:
                    # Reading the XML file will ignore extra tags, because they're not supported
                    # for ordinary GUI rendering (i.e. plural needs a 'count').
                    root = etree.fromstring(i18n)
                    contexts = root.findall("context")

                    for context in contexts:
                        for message in context.findall("message"):
                            if "numerus" in message.keys():
                                continue

                            translation = message.find("translation")

                            # With length variants?
                            if "variants" in translation.keys() and translation.get("variants") == "yes":
                                res[message.find("source").text] = [m.text for m in translation.findall("lengthvariant")][0]

                            # Ordinary?
                            else:
                                if translation.text:
                                    res[message.find("source").text] = translation.text

        return res

    def getObjectBackendParameters(self, backend, attribute):
        """
        Helper method to extract backendParameter infos
        """
        attrs = self.getObjectBackendProperties(backend)

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
