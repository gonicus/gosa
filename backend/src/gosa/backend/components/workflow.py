import os
import sys
from lxml import objectify, etree
from gosa.common import Environment
from gosa.common.components import PluginRegistry
from pkg_resources import resource_filename


class WorkflowException(Exception):
    pass


class Workflow:

    env = None
    dn = None
    uuid = None
    _path = None
    _xml_root = None

    def __init__(self, _id, what=None, user=None):
        schema = etree.XMLSchema(file=resource_filename("gosa.backend", "data/workflow.xsd"))
        parser = objectify.makeparser(schema=schema)
        self.env = Environment.getInstance()
        self.uuid = _id
        self.dn = self.env.base

        self._path = self.env.config.get("core.workflow_path", "/var/lib/gosa/workflows")
        self._xml_root = objectify.parse(os.path.join(self._path, _id, "workflow.xml"), parser).getroot()

    def get_all_method_names(self):
        return ["commit", "get_templates", "get_translations"]

    def commit(self):
        if self._has_mandatory_attributes_values():
            with open(os.path.join(self._path, self.uuid, "workflow.py"), "r") as fscr:
                return self._execute_embedded_script(fscr.read())

        return False

    def get_id(self):
        find = objectify.ObjectPath("Workflow.Id")
        return find(self._xml_root[0]).text

    def get_templates(self):
        templates = {}

        find = objectify.ObjectPath("Workflow.Templates")
        for template in find(self._xml_root[0]).getchildren():
            with open(os.path.join(self._path, self.uuid, "templates", template.text), "r") as ftpl:
                templates[template.text] = ftpl.read()

        return templates

    def get_translations(self, locale):
        translations = {}

        find = objectify.ObjectPath("Workflow.Templates")
        for template in find(self._xml_root[0]).getchildren():
            translation = template[:-2] + "locale"
            translation_path = os.path.join(self._path, self.env, "i18n", locale, translation)
            if os.path.isfile(translation_path):
                with open(translation_path, "r") as ftpl:
                    translations[template] = ftpl.read()
            else:
                translations[template] = None

        return translations

    def _load(self, attr, element, default=None):
        """
        Helper function for loading XML attributes with defaults.
        """
        if element not in attr.__dict__:
            return default

        return attr[element]

    def _get_attributes(self):
        res = {}
        for element in self._xml_root:
            find = objectify.ObjectPath("Workflow.Attributes")
            if find.hasattr(element):
                for attr in find(element).iterchildren():
                    if attr.tag == "{http://www.gonicus.de/Workflows}Attribute":
                        if attr.Name.text not in res:
                            res[attr.Name.text] = {}

                        res[attr.Name.text] = {
                            'description': str(self._load(attr, "Description", "")),
                            'type': attr.Type.text,
                            'multivalue': bool(self._load(attr, "MultiValue", False)),
                            'mandatory': bool(self._load(attr, "Mandatory", False)),
                            'read-only': bool(self._load(attr, "ReadOnly", False)),
                            'case-sensitive': bool(self._load(attr, "CaseSensitive", False)),
                            'unique': bool(self._load(attr, "Unique", False)),
                            'objects': [],
                            'primary': [],
                        }
        return res

    def _execute_embedded_script(self, script):
        try:
            env = dict(data=self._get_data())
            dispatcher = PluginRegistry.getInstance('CommandRegistry')

            def make_dispatch(method):
                def call(*args, **kwargs):
                    return dispatcher.call(method, *args, **kwargs)
                return call

            # Add public calls
            for method in dispatcher.getMethods():
                env[method] = make_dispatch(method)

            exec(script, env)

        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]

            print("Exception while executing the embedded script:")
            print(fname, "line", exc_tb.tb_lineno)
            print(exc_type)
            print(e)
            return False

        return True

    def _get_data(self):
        """
        Returns a dictionary with key being the attribute ids and the values the data the user entered.
        """
        return {
            "pn": "Siegfried",
            "sn": "Siegtorson"
        }

    def _has_mandatory_attributes_values(self):
        """
        Checks if all mandatory attributes have values. Returns true if check is ok or the id of the first mandatory
        attribute that has no value.
        """
        data = self._get_data()
        for key, value in self._get_attributes().items():
            if value["mandatory"]:
                if key not in data or data[key] is None or (isinstance(data[key], str) and data[key].strip() == ""):
                    print("ERROR: The attribute '%s' is mandatory but has no value." % key)
                    return False
        return True
