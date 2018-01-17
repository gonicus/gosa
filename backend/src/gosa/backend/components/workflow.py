import copy
import os
import sys
import logging

import datetime
from threading import Thread

import pkg_resources
from tornado import gen

from gosa.common.exceptions import FactoryException

from gosa.backend.objects.object import Object
from gosa.backend.objects.validator import Validator
from gosa.backend.objects.xml_parsing import XmlParsing
from lxml import objectify, etree

from gosa.backend.routes.sse.main import SseHandler
from gosa.common.event import EventMaker
from gosa.common.gjson import dumps
from gosa.common.utils import N_
from gosa.backend.objects import ObjectProxy
from gosa.common import Environment
from gosa.common.components import PluginRegistry
from gosa.common.error import GosaErrorHandler as C, GosaErrorHandler
from pkg_resources import resource_filename


# Register the errors handled  by us
C.register_codes(dict(
    WORKFLOW_SCRIPT_ERROR=N_("Error executing workflow script '%(topic)s'")
))

#TODO: exceptions
#      attribute handling


class WorkflowException(Exception):
    pass


class Workflow:

    env = None
    dn = None
    uuid = None
    parent = None
    _path = None
    _xml_root = None
    __attribute_map = None
    __attribute = None
    __user = None
    __session_id = None
    __reference_object = None
    __log = None
    __skip_refresh = False
    __xml_parsing = None
    __attribute_config = None  # information about attributes that shall not be in __attribute_map
    __validator = None
    __method_map = None
    __attribute_type = None

    def __init__(self, _id, what=None, user=None, session_id=None):
        schema = etree.XMLSchema(file=resource_filename("gosa.backend", "data/workflow.xsd"))
        parser = objectify.makeparser(schema=schema)
        self.env = Environment.getInstance()
        self.parent = self
        self.uuid = _id
        self.dn = self.env.base
        self.__xml_parsing = XmlParsing('Workflows')
        self.__validator = Validator(self)
        self.__attribute_config = {}
        self.__user = user
        self.__session_id = session_id
        self.__log = logging.getLogger(__name__)
        self.__attribute_type = {}

        for entry in pkg_resources.iter_entry_points("gosa.object.type"):
            mod = entry.load()
            self.__attribute_type[mod.__alias__] = mod()

        self._path = self.env.config.get("core.workflow-path", "/var/lib/gosa/workflows")
        self._xml_root = objectify.parse(os.path.join(self._path, _id, "workflow.xml"), parser).getroot()

        self.__attribute = {key: None for key in self.get_attributes()}
        self.__method_map = {
            "commit": None,
            "get_templates": None,
            "get_translations": None,
        }
        self.__fill_method_map()

        if what is not None:
            # load object and copy attribute values to workflow
            try:
                self.__reference_object = ObjectProxy(what)

                self.__skip_refresh = True
                # set the reference dn if possible
                if 'reference_dn' in self.__attribute:
                    setattr(self, 'reference_dn', what)

                # copy all other available attribute values to workflow object
                for key in self.__attribute:
                    if hasattr(self.__reference_object, key) and getattr(self.__reference_object, key) is not None:
                        setattr(self, key, getattr(self.__reference_object, key))

                self.__skip_refresh = False

            except Exception as e:
                # could not open the reference object
                self.__log.error(e)

    def get_methods(self):
        return self.get_all_method_names()

    def get_all_method_names(self):
        return list(self.__method_map)

    def get_attributes(self, detail=False):
        res = self._get_attributes()

        if detail:
            return res

        return list(res.keys())

    def get_attribute_values(self):
        """
        Return a dictionary containing all property values.
        """
        res = {'value': {}, 'values': {}, 'saveable': {}}
        for item in self.__attribute_map:
            res['value'][item] = getattr(self, item)
            res['values'][item] = self.__attribute_map[item]['values']
            res['saveable'][item] = self.__attribute_map[item]['readonly'] is False and \
                                    'skip_save' not in self.__attribute_map[item] or self.__attribute_map[item]['skip_save'] is False

        return res

    def __refresh_reference_object(self, new_dn, override=False):
        attributes_changed = []
        if not self.__reference_object:
            if new_dn is None:
                return

            # initial setting
            self.__reference_object = ObjectProxy(new_dn)
        elif self.__reference_object.dn == new_dn:
            # no change
            return
        elif new_dn is None:
            # reset object
            for key in self.__attribute:
                if hasattr(self.__reference_object, key) and \
                        getattr(self.__reference_object, key) is not None and \
                        getattr(self, key) == getattr(self.__reference_object, key) and \
                        self.__attribute_map[key]['mandatory'] is False:
                    setattr(self, key, None)
                    attributes_changed.append(key)

            self.__reference_object = None
            return
        else:
            self.__reference_object = ObjectProxy(new_dn)

        # update all attribute values that are not set yet
        if self.__reference_object is not None:
            for key in self.__attribute:
                if hasattr(self.__reference_object, key) and \
                            getattr(self.__reference_object, key) is not None and \
                            (getattr(self, key) is None or override is True):
                    setattr(self, key, getattr(self.__reference_object, key))
                    attributes_changed.append(key)

        if len(attributes_changed) > 0:
            # tell the GUI to reload the changes attributes
            e = EventMaker()
            ev = e.Event(e.ObjectChanged(
                e.UUID(self.uuid),
                e.DN(new_dn),
                e.ModificationTime(datetime.datetime.now().strftime("%Y%m%d%H%M%SZ")),
                e.ChangeType("update")
            ))
            event_object = objectify.fromstring(etree.tostring(ev, pretty_print=True).decode('utf-8'))
            SseHandler.notify(event_object, channel="user.%s" % self.__user)

    def commit(self):
        self.check()
        with open(os.path.join(self._path, self.uuid, "workflow.py"), "r") as fscr:
            thread = Thread(target=self._execute_embedded_script, args=(fscr.read(), ))
            thread.start()

    def get_id(self):
        find = objectify.ObjectPath("Workflow.Id")
        return find(self._xml_root[0]).text

    def get_templates(self):
        templates = {}

        find = objectify.ObjectPath("Workflow.Templates")
        for idx, template in enumerate(find(self._xml_root[0]).getchildren()):
            with open(os.path.join(self._path, self.uuid, "templates", template.text), "r") as ftpl:
                templates[template.text] = {
                    "index": idx,
                    "content": ftpl.read()
                }

        return templates

    def get_translations(self, locale):
        translations = {}

        find = objectify.ObjectPath("Workflow.Templates")
        for template in find(self._xml_root[0]).getchildren():
            translation = template.text[:-5]
            translation_path = os.path.join(self._path, self.uuid, "i18n", translation, "%s.json" % locale)
            if os.path.isfile(translation_path):
                with open(translation_path, "r") as ftpl:
                    translations[template.text] = ftpl.read()
            else:
                translations[template.text] = None

        return translations

    def _load(self, attr, element, default=None):
        """
        Helper function for loading XML attributes with defaults.
        """
        if element not in attr.__dict__:
            return default

        return attr[element]

    def __fill_method_map(self):
        from gosa.backend.objects.factory import load

        class Klass(Object):

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

        for element in self._xml_root:
            find = objectify.ObjectPath('Workflow.Methods')
            if (find.hasattr(element)):
                for method in find(element).iterchildren():
                    if method.tag == "{http://www.gonicus.de/Workflows}Method":
                        # method = attr.Command.text

                        # self.__method_map[method.text] = getattr(self.__base, method)

                        # Extract method information out of the xml tag
                        method_name = method['Name'].text
                        command = method['Command'].text

                        # Get the list of method parameters
                        m_params = []
                        if 'MethodParameters' in method.__dict__:
                            for param in method['MethodParameters']['MethodParameter']:
                                p_name = param['Name'].text
                                p_type = param['Type'].text

                                p_required = bool(load(param, "Required", False))
                                p_default = str(load(param, "Default"))
                                m_params.append((p_name, p_type, p_required, p_default))

                        # Get the list of command parameters
                        c_params = []
                        if 'CommandParameters' in method.__dict__:
                            for param in method['CommandParameters']['Value']:
                                c_params.append(param.text)

                        # Append the method to the list of registered methods for this object
                        cr = PluginRegistry.getInstance('CommandRegistry')
                        self.__method_map[method_name] = {'ref': self.__create_class_method(
                            Klass, method_name, command, m_params, c_params, cr.callNeedsUser(command),
                            cr.callNeedsSession(command))}

    def __create_class_method(self, klass, methodName, command, mParams, cParams, needsUser=False, needsSession=False):
        """
        Creates a new klass-method for the current objekt.
        """

        # Now add the method to the object
        def funk(caller_object, *args, **kwargs):

            # Load the objects actual property set
            props = caller_object.get_attribute_values()['value']

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
                if props[key]:
                    propList[key] = props[key]
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

    def _get_attributes(self):
        if not self.__attribute_map:
            res = {}
            references = {}
            for element in self._xml_root:
                find = objectify.ObjectPath("Workflow.Attributes")
                if find.hasattr(element):
                    for attr in find(element).iterchildren():
                        if attr.tag == "{http://www.gonicus.de/Workflows}Attribute":
                            if attr.Name.text not in res:
                                res[attr.Name.text] = {}

                            values_populate = None
                            value_inherited_from = None
                            re_populate_on_update = False
                            values = []
                            if 'Values' in attr.__dict__:
                                avalues = []
                                dvalues = {}

                                if 'populate' in attr.__dict__['Values'].attrib:
                                    values_populate = attr.__dict__['Values'].attrib['populate']
                                    if 'refresh-on-update' in attr.__dict__['Values'].attrib:
                                        re_populate_on_update = attr.__dict__['Values'].attrib['refresh-on-update'].lower() == "true"
                                else:
                                    for d in attr.__dict__['Values'].iterchildren():
                                        if 'key' in d.attrib:
                                            dvalues[d.attrib['key']] = d.text
                                        else:
                                            avalues.append(d.text)

                                if avalues:
                                    values = avalues
                                else:
                                    values = dvalues

                            if 'InheritFrom' in attr.__dict__:
                                value_inherited_from = {
                                    "rpc": str(self._load(attr, "InheritFrom", "")),
                                    "reference_attribute": attr.__dict__['InheritFrom'].attrib['relation']
                                }
                                if value_inherited_from["reference_attribute"] not in references:
                                    references[value_inherited_from["reference_attribute"]] = {}
                                if value_inherited_from["rpc"] not in references[value_inherited_from["reference_attribute"]]:
                                    references[value_inherited_from["reference_attribute"]][value_inherited_from["rpc"]] = []
                                references[value_inherited_from["reference_attribute"]][value_inherited_from["rpc"]].append(attr.Name.text)

                            if 'Validators' in attr.__dict__:
                                self.__attribute_config[attr.Name.text] = {
                                    'validators': self.__xml_parsing.build_filter(attr['Validators'])
                                }

                            blocked_by = []
                            if "BlockedBy" in attr.__dict__:
                                for d in attr.__dict__['BlockedBy'].iterchildren():
                                    blocked_by.append({
                                        'name': d.text,
                                        'value': None if d.attrib['value'] == 'null' else d.attrib['value']})

                            res[attr.Name.text] = {
                                'description': str(self._load(attr, "Description", "")),
                                'type': attr.Type.text,
                                'default': str(self._load(attr, "Default", "")),
                                'multivalue': bool(self._load(attr, "MultiValue", False)),
                                'mandatory': bool(self._load(attr, "Mandatory", False)),
                                'readonly': bool(self._load(attr, "ReadOnly", False)),
                                'is_reference_dn': bool(self._load(attr, "IsReferenceDn", False)),
                                'case_sensitive': bool(self._load(attr, "CaseSensitive", False)),
                                'unique': bool(self._load(attr, "Unique", False)),
                                'blocked_by': blocked_by,
                                'values_populate': values_populate,
                                're_populate_on_update': re_populate_on_update,
                                'value_inherited_from': value_inherited_from,
                                'values': values
                            }
                for attr, referenced_attrs in references.items():
                    res[attr]['value_inheriting_to'] = referenced_attrs
            self.__attribute_map = res

        return self.__attribute_map

    def _execute_embedded_script(self, script):
        log = logging.getLogger("%s.%s" % (__name__, self.uuid))
        try:
            log.info("start executing workflow script")
            env = dict(data=self._get_data())
            dispatcher = PluginRegistry.getInstance('CommandRegistry')

            def make_dispatch(method):
                def call(*args, **kwargs):
                    return dispatcher.dispatch(self.__user, self.__session_id, method, *args, **kwargs)
                return call

            # Add public calls
            for method in dispatcher.getMethods():
                env[method] = make_dispatch(method)

            # add logger
            env['log'] = log

            exec(script, env)

            log.info("finished executing workflow script")

            if self.__user is not None:
                # tell the frontend
                e = EventMaker()
                ev = e.Event(e.BackendDone(
                    e.UUID(self.uuid),
                    e.Type("workflow"),
                    e.State("success")
                ))
                event_object = objectify.fromstring(etree.tostring(ev, pretty_print=True).decode('utf-8'))
                SseHandler.notify(event_object, channel="user.%s" % self.__user)

        except Exception as ex:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]

            log.error("Exception while executing the embedded script:")
            log.error("%s line %s" % (fname, exc_tb.tb_lineno))
            log.error(exc_type)
            log.error(exc_obj)

            if GosaErrorHandler.get_error_id(str(ex)) is None:
                ex = ScriptError(C.make_error('WORKFLOW_SCRIPT_ERROR', str(ex)))

            e = EventMaker()
            ev = e.Event(e.BackendDone(
                e.UUID(self.uuid),
                e.Type("workflow"),
                e.State("error"),
                e.Message(str(ex))
            ))
            event_object = objectify.fromstring(etree.tostring(ev, pretty_print=True).decode('utf-8'))
            SseHandler.notify(event_object, channel="user.%s" % self.__user)
            raise ex

        return True

    def __getattr__(self, name):

        # Methods
        methods = self.__method_map
        if name in methods:
            def m_call(*args, **kwargs):
                return methods[name]['ref'](self, *args, **kwargs)
            return m_call

        # Valid attribute?
        if not name in self._get_attributes():
            raise AttributeError(C.make_error('ATTRIBUTE_NOT_FOUND', name))

        return self.__attribute[name]

    def __setattr__(self, name, value):
        # Store non property values
        try:
            object.__getattribute__(self, name)
            self.__dict__[name] = value
            return
        except AttributeError:
            pass

        # Valid attribute?
        if not name in self._get_attributes():
            raise AttributeError(C.make_error('ATTRIBUTE_NOT_FOUND', name))

        # Validate value
        # mandatory
        attributes = self._get_attributes()
        attribute = attributes[name]
        if attribute['mandatory'] and value is None:
            raise AttributeError(C.make_error('ATTRIBUTE_MANDATORY', name))

        # custom validators
        if name in self.__attribute_config:
            config = self.__attribute_config[name]
            if 'validators' in config and config['validators'] is not None:
                props_copy = copy.deepcopy(self.__attribute)
                res, error = self.__validator.process_validator(config['validators'], name, [value], props_copy)
                if res is False:
                    raise ValueError(C.make_error('ATTRIBUTE_CHECK_FAILED', name, details=error))

        changed = self.__attribute[name] != value
        self.__attribute[name] = value

        if changed is True:
            self.__update_population()

        if attribute['is_reference_dn'] and self.__skip_refresh is False:
            self.__refresh_reference_object(value)

        if 'value_inheriting_to' in attribute and \
                attribute['value_inheriting_to'] and self.__skip_refresh is False:
            registry = PluginRegistry.getInstance("CommandRegistry")
            inherited_change = False
            for rpc, values in attribute['value_inheriting_to'].items():
                res = registry.dispatch(registry, None, rpc, value)
                for a, val in res.items():
                    if a in values and hasattr(self, a) and getattr(self, a) != val:
                        setattr(self, a, val)
                        inherited_change = True

            if inherited_change is True:
                e = EventMaker()
                ev = e.Event(e.ObjectChanged(
                    e.UUID(self.uuid),
                    e.ModificationTime(datetime.datetime.now().strftime("%Y%m%d%H%M%SZ")),
                    e.ChangeType("update")
                ))
                event_object = objectify.fromstring(etree.tostring(ev, pretty_print=True).decode('utf-8'))
                SseHandler.notify(event_object, channel="user.%s" % self.__user)

    def repopulate_attribute_values(self, attribute_name):
        self.__update_population()

    def __update_population(self):
        # collect current attribute values
        data = {}
        for prop in self._get_attributes():
            data[prop] = getattr(self, prop)

        changes = {}

        for key in self.__attribute_map:
            if self.__attribute_map[key]['values_populate'] and self.__attribute_map[key]['re_populate_on_update'] is True:
                cr = PluginRegistry.getInstance('CommandRegistry')
                values = cr.call(self.__attribute_map[key]['values_populate'], data)
                if self.__attribute_map[key]['values'] != values:
                    changes[key] = values
                self.__attribute_map[key]['values'] = values

        if len(changes.keys()) and self.__user is not None:
            e = EventMaker()
            changed = list()
            for key, values in changes.items():
                change = e.Change(
                    e.PropertyName(key),
                    e.NewValues(dumps(values))
                )
                changed.append(change)

            ev = e.Event(
                e.ObjectPropertyValuesChanged(
                    e.UUID(self.uuid),
                    *changed
                )
            )
            event_object = objectify.fromstring(etree.tostring(ev).decode('utf-8'))
            SseHandler.notify(event_object, channel="user.%s" % self.__user)

    def _get_data(self):
        """
        Returns a dictionary with key being the attribute ids and the values the data the user entered.
        """
        return self.__attribute

    def check(self):
        """
        Checks whether everything is fine with the workflow and its given values or not.
        """
        props = self._get_attributes()
        data = self._get_data()
        # Collect values by store and process the property filters
        for key, prop in self._get_attributes().items():

            # Check if this attribute is blocked by another attribute and its value.
            is_blocked = False
            # for bb in prop['blocked_by']:
            #     if bb['value'] == data[bb['name']]:
            #         is_blocked = True
            #         break

            # Check if all required attributes are set. (Skip blocked once, they cannot be set!)
            if not is_blocked and prop['mandatory'] and data[key] is None or (isinstance(data[key], str) and data[key].strip() == ""):
                raise AttributeError(C.make_error('ATTRIBUTE_MANDATORY', key))

        return props


class ScriptError(Exception):
    pass
