import hashlib
import logging
import pprint
import cups
import os
import tempfile

from zope.interface import implementer

from gosa.backend.objects import ObjectProxy
from gosa.common.error import GosaErrorHandler as C
from gosa.common import Environment
from gosa.common.components import Plugin, Command, PluginRegistry
from gosa.common.gjson import loads
from gosa.common.handler import IInterfaceHandler
from gosa.common.utils import N_

conn = cups.Connection()

pp = pprint.PrettyPrinter()

C.register_codes(dict(
    ERROR_GETTING_SERVER_PPD=N_("Server PPD file could not be retrieved: '%(type)s'"),
    PPD_NOT_FOUND=N_("PPD file '%(ppd)s' not found"),
    OPTION_CONFLICT=N_("Setting option '%(option)s' to '%(value)s' caused %(conflicts)s"),
    OPTION_NOT_FOUND=N_("Option '%(option)s' not found in PPD")
))


@implementer(IInterfaceHandler)
class CupsClient(Plugin):
    _priority_ = 99
    _target_ = "cups"
    client = None
    __printer_list = None

    def __init__(self):
        self.env = Environment.getInstance()
        self.log = logging.getLogger(__name__)

    def serve(self):
        self.client = cups.Connection()

    def __get_printer_list(self):
        if self.__printer_list is None:
            res = {}
            for name, ppd in self.client.getPPDs().items():
                if ppd["ppd-make"] not in res:
                    res[ppd["ppd-make"]] = []
                res[ppd["ppd-make"]].append({"model": ppd["ppd-make-and-model"], "ppd": name})
            self.__printer_list = res
        return self.__printer_list

    @Command(__help__=N_("Write settings to PPD file"))
    def writePPD(self, printer_cn, server_ppd_file, custom_ppd_file, data):
        server_ppd = None
        try:
            server_ppd = self.client.getServerPPD(server_ppd_file)
            is_server_ppd = True
            ppd = cups.PPD(server_ppd)
        except:
            is_server_ppd = False
        else:
            ppd = cups.PPD(custom_ppd_file)

        if isinstance(data, str):
            data = loads(data)

        # apply options
        for option_name, value in data.items():
            option = ppd.findOption(option_name)
            if option is not None:
                conflicts = ppd.markOption(option_name, value)
                if conflicts > 0:
                    raise PPDException(C.make_error('OPTION_CONFLICT', option=option_name, value=value, conflicts=conflicts))
            else:
                raise PPDException(C.make_error('OPTION_NOT_FOUND', option=option_name))

        # calculate hash value for new PPD
        dir = self.env.config.get("cups.spool", default="/tmp/spool")
        if not os.path.exists(dir):
            os.makedirs(dir)

        temp_file = tempfile.NamedTemporaryFile(delete=False)
        try:
            with open(temp_file.name, "w") as tf:
                ppd.writeFd(tf.fileno())

            with open(temp_file.name, "r") as tf:
                result = tf.read()

            hash = hashlib.md5(repr(result).encode('utf-8')).hexdigest()
            index = PluginRegistry.getInstance("ObjectIndex")

            new_file = os.path.join(dir, "%s.ppd" % hash)
            if new_file == custom_ppd_file:
                # nothing to to
                return {}

            if not is_server_ppd:
                # check if anyone else is using a file with this hash value and delete the old file if not
                query = {"_type": "GotoPrinter", "gotoPrinterPPD": custom_ppd_file}
                if printer_cn is not None:
                    query["not_"] = {"cn": printer_cn}
                res = index.search(query, {"dn": 1})
                if len(res) == 0:
                    # delete file
                    os.unlink(custom_ppd_file)

            with open(new_file, "w") as f:
                f.write(result)

            return {"gotoPrinterPPD": [new_file]}

        except Exception as e:
            self.log.error(str(e))
            return {}
        finally:
            os.unlink(temp_file.name)
            if server_ppd is not None:
                os.unlink(server_ppd)

    @Command(__help__=N_("Get a list of all available printer manufacturers"))
    def getPrinterManufacturers(self):
        return list(self.__get_printer_list().keys())

    @Command(__help__=N_("Get a list of all available printer models for one manufacturer"))
    def getPrinterModels(self, *args):
        printers = self.__get_printer_list()
        res = {}
        if len(args):
            if isinstance(args[0], dict):
                manufacturer = args[0]["maker"]
            elif isinstance(args[0], str):
                manufacturer = args[0]

        if manufacturer is not None:
            if manufacturer in printers:
                for entry in printers[manufacturer]:
                    res[entry["ppd"]] = {"value": entry["model"]}

        return res

    @Command(__help__=N_("Get a GUI template from a PPD file"))
    def getConfigurePrinterTemplate(self, data):
        """
        Generates a GUI template from a PPD file.
        """
        ppd_file = None
        name = None
        delete = True
        # extract name from data
        if isinstance(data, str):
            name = data
        elif isinstance(data, dict):
            if "gotoPrinterPPD" in data and data["gotoPrinterPPD"] is not None and os.path.exists(data["gotoPrinterPPD"]):
                ppd_file = data["gotoPrinterPPD"]
                delete = False
            else:
                name = data["serverPPD"]
        else:
            name = str(data)

        template = {
            "type": "widget",
            "class": "gosa.ui.tabview.TabView",
            "addOptions": {
                "flex": 1
            },
            "properties": {
                "width": 800,
                "height": 600,
                "windowTitle": "tr('Configure printer')",
                "dialogName": "configurePrinter",
                "cancelable": True
            },
            "children": []
        }

        try:
            if ppd_file is None:
                ppd_file = self.client.getServerPPD(name)
            if not os.path.exists(ppd_file):
                raise CupsException(C.make_error('PPD_NOT_FOUND', ppd=ppd_file))
            ppd = cups.PPD(ppd_file)
            ppd.localize()
            model_attr = ppd.findAttr("ModelName")
            if model_attr:
                template["properties"]["windowTitle"] = N_("Configure printer: %s" % model_attr.value)
            for group in ppd.optionGroups:
                template["children"].append(self.__read_group(group))
            return template
        except cups.IPPError as e:
            raise CupsException(C.make_error('ERROR_GETTING_SERVER_PPD', str(e)))
        finally:
            if delete is True and ppd_file and os.access(ppd_file, os.F_OK):
                os.unlink(ppd_file)

    def __read_group(self, group):
        row = 0
        col = 0
        tab = 1
        template = {
            "class": "qx.ui.tabview.Page",
            "layout": "qx.ui.layout.Grid",
            "properties": {
                "label": group.text
            },
            "layoutConfig": {
                "spacingX": "CONST_SPACING_X",
                "spacingY": "CONST_SPACING_Y"
            },
            "extensions": {
                "layoutOptions": {
                    "columnFlex": {
                        "column": 1,
                        "flex": 1
                    }
                }
            },
            "children": []
        }
        for option in group.options:
            label = {
                "addOptions": {
                    "row": row,
                    "column": col
                },
                "properties": {
                    "text": option.text
                },
                "class": "gosa.ui.widgets.QLabelWidget"
            }

            template["children"].append(label)

            widget = {
                "widgetName": option.keyword,
                "addOptions": {
                    "row": row,
                    "column": col+1
                },
                "properties": {
                    "tabIndex": tab,
                    "sortBy": "value",
                    "values": {},
                    "value": [option.defchoice]
                },
                "class": "gosa.ui.widgets.QComboBoxWidget"
            }
            for choice in option.choices:
                widget["properties"]["values"][choice["choice"]] = {"value": choice["text"]}

            template["children"].append(widget)
            row += 1
            tab += 1

        return template

    def get_attributes_from_ppd(self, ppd_file, attributes):
        res = {}
        try:
            ppd = cups.PPD(ppd_file)
            ppd.localize()
            for name in attributes:
                attr = ppd.findAttr(name)
                if attr is not None:
                    res[name] = attr.value

        except cups.IPPError as e:
            self.log.error(str(e))

        finally:
            return res


class CupsException(Exception):
    pass


class PPDException(Exception):
    pass
