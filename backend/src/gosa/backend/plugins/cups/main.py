import logging
import pprint
import cups
import os

from zope.interface import implementer
from gosa.common.error import GosaErrorHandler as C
from gosa.common import Environment
from gosa.common.components import Plugin, Command
from gosa.common.handler import IInterfaceHandler
from gosa.common.utils import N_

conn = cups.Connection()

pp = pprint.PrettyPrinter()

C.register_codes(dict(
    ERROR_GETTING_SERVER_PPD=N_("Server PPD file could not be retrieved: '%(type)s'")
))

# for name, data in conn.getPrinters().items():
#     print("Printer: %s"  % name)
#     print("\tModel: %s" % data["printer-make-and-model"])
#     print("\tLocation: %s" % data["printer-location"])


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
        Generates a GUI template from a PPD file. Please not that this is not the same template
        syntax as the object/workflow templates.
        """
        # extract name from data
        if isinstance(data, str):
            name = data
        elif isinstance(data, dict):
            name = data["gotoPrinterPPD"]
        else:
            name = str(data)

        template = {
            "layout": "qx.ui.layout.VBox",
            "type": "widget",
            "class": "qx.ui.container.Composite",
            "addOptions": {
                "flex": 1
            },
            "layoutConfig": {
                "spacing": "CONST_SPACING_Y"
            },
            "properties": {
                "width": 800,
                "height": 600,
                "windowTitle": "tr('Configure printer')",
                "dialogName": "configurePrinter"
            },
            "children": []
        }
        ppd_file = None
        try:
            ppd_file = self.client.getServerPPD(name)
            ppd = cups.PPD(ppd_file)
            ppd.localize()
            for group in ppd.optionGroups:
                template["children"].append(self.__read_group(group))
            return template
        except cups.IPPError as e:
            raise CupsException(C.make_error('ERROR_GETTING_SERVER_PPD', str(e)))
        finally:
            if ppd_file and os.access(ppd_file, os.F_OK):
                os.unlink(ppd_file)

    def __read_group(self, group):
        row = 0
        col = 0
        tab = 1
        template = {
            "class": "gosa.ui.widgets.GroupBox",
            "layout": "qx.ui.layout.Grid",
            "properties": {
                "legend": group.text
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
                "buddyModelPath": option.keyword,
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
                "modelPath": option.keyword,
                "addOptions": {
                    "row": row,
                    "column": col+1
                },
                "properties": {
                    "tabIndex": tab,
                    "sortBy": "value",
                    "value": [option.defchoice],
                    "values": []
                },
                "class": "gosa.ui.widgets.QComboBoxWidget"
            }
            for choice in option.choices:
                widget["properties"]["values"].append({
                    choice["choice"]: {"value": choice["text"]}
                })

            template["children"].append(widget)
            row += 1
            tab += 1

        # for subgroup in group.subgroups:
        #     res["subgroups"] = self.__read_group(subgroup)
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
            raise CupsException(C.make_error('ERROR_GETTING_SERVER_PPD', str(e)))
        finally:
            return res


class CupsException(Exception):
    pass

# ppd_file = conn.getPPD("uberdruck")
# # attrs = conn.getPrinterAttributes("unterdruck")
#
# try:
#     for name, ppd in conn.getPPDs().items():
#         print("Name %s: " % name)
#         pp.pprint(ppd)

    # ppd = cups.PPD(ppd_file)
    # ppd.localize()
    # slot = ppd.findOption("InputSlot")
    # print(str(slot))
    # pp.pprint(slot.choices)
    # print(slot.defchoice)

    # for attr in ppd.attributes:
    #     print("%s/%s: %s" % (attr.name, attr.text, attr.value))
    #
    # for group in ppd.optionGroups:
    #     print("-----------------------------")
    #     print("Option group: %s/%s" % (group.name, group.text))
    #     for option in group.options:
    #         print("\toption %s/%s: %s (%s)" % (option.keyword, option.text, option.defchoice, option.choices))
    #
    #     for subgroup in group.subgroups:
    #         print("\tOption group: %s/%s" % (subgroup.name, subgroup.text))

    # with open(ppd_file) as f:
    #     content = f.read()
    #     print(content)
#
# finally:
#     if ppd_file and os.access(ppd_file, os.F_OK):
#         os.unlink(ppd_file)
