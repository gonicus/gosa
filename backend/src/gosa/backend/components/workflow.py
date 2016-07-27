import os
import sys
from lxml import objectify, etree
from pkg_resources import resource_filename


class WorkflowException(Exception):
    pass


class Workflow:

    def __init__(self, xml_file_path):
        schema = etree.XMLSchema(file=resource_filename("gosa.backend", "data/workflow.xsd"))
        parser = objectify.makeparser(schema=schema)
        self._xml_root = objectify.parse(xml_file_path, parser).getroot()

    def commit(self):
        find = objectify.ObjectPath("Workflow.Script")
        if self._has_mandatory_attributes_values():
            self._execute_embedded_script(find(self._xml_root)[0])

    def get_id(self):
        find = objectify.ObjectPath("Workflow.Id")
        return find(self._xml_root[0]).text

    def getTemplates(self):
        find = objectify.ObjectPath("Workflow.Templates")
        return find(self._xml_root[0]).getchildren()

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
            exec(script.text, {"data": self._get_data(), "save": self.save})
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]

            print("Exception while executing the embedded script:")
            print(fname, "line", exc_tb.tb_lineno)
            print(exc_type)
            print(e)

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
