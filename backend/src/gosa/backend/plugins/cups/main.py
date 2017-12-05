# This file is part of the GOsa project.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.
import functools
import hashlib
import logging
import cups
import os
import tempfile

import time

import requests
from zope.interface import implementer

from gosa.backend.exceptions import EntryNotFound
from gosa.backend.objects import ObjectProxy
from gosa.common.error import GosaErrorHandler as C
from gosa.common import Environment
from gosa.common.components import Plugin, Command, PluginRegistry
from gosa.common.gjson import loads
from gosa.common.handler import IInterfaceHandler
from gosa.common.utils import N_


C.register_codes(dict(
    ERROR_GETTING_SERVER_PPD=N_("Server PPD file could not be retrieved: '%(type)s'"),
    PPD_NOT_FOUND=N_("PPD file '%(ppd)s' not found"),
    OPTION_CONFLICT=N_("Setting option '%(option)s' to '%(value)s' caused %(conflicts)s"),
    OPTION_NOT_FOUND=N_("Option '%(option)s' not found in PPD"),
    COULD_NOT_READ_SOURCE_PPD=N_("Could not read source PPD file"),
    USER_NOT_FOUND=N_("User '%(topic)s' not found")
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
        try:
            server = self.env.config.get("cups.server")
            port = self.env.config.get("cups.port")
            user = self.env.config.get("cups.user")
            password = self.env.config.get("cups.password")
            encryption_policy = getattr(cups, "HTTP_ENCRYPT_%s" % self.env.config.get("cups.encryption-policy",
                                                                                      default="IF_REQUESTED").upper())
            if server is not None:
                cups.setServer(server)
            if port is not None:
                cups.setPort(int(port))
            if user is not None:
                cups.setUser(user)
            if encryption_policy is not None:
                cups.setEncryption(encryption_policy)

            if password is not None:
                def pw_callback(prompt):
                    return password

                cups.setPasswordCB(pw_callback)

            self.client = cups.Connection()

            sched = PluginRegistry.getInstance("SchedulerService").getScheduler()
            sched.add_interval_job(self.__gc, minutes=60, tag='_internal', jobstore="ram")

        except RuntimeError as e:
            self.log.error(str(e))

    def __get_printer_list(self):
        if self.__printer_list is None:
            res = {}
            for name, ppd in self.client.getPPDs().items():
                if ppd["ppd-make"] not in res:
                    res[ppd["ppd-make"]] = []
                res[ppd["ppd-make"]].append({"model": ppd["ppd-make-and-model"], "ppd": name})
            self.__printer_list = res
        return self.__printer_list

    def __gc(self):
        """ garbage collection for unused temporary PPD files in spool directory """
        index = PluginRegistry.getInstance("ObjectIndex")

        dir = self.env.config.get("cups.spool", default="/tmp/spool")
        for file in os.listdir(dir):
            if os.path.isfile(os.path.join(dir, file)) and file.split(".")[-1:][0].lower() == "ppd":
                ppd_file = os.path.join(dir, file)
                res = index.search({"_type": "GotoPrinter", "gotoPrinterPPD": ppd_file}, {"dn": 1})
                if len(res) == 0 and os.path.getmtime(ppd_file) < time.time()-3600:
                    # no entry -> delete file if it has not been changed in the last hour
                    self.log.debug("deleting obsolete PPD file: %s" % ppd_file)
                    os.unlink(ppd_file)

    @Command(__help__=N_("Write settings to PPD file"))
    def writePPD(self, printer_cn, server_ppd_file, custom_ppd_file, data):
        if self.client is None:
            return

        server_ppd = None
        dir = self.env.config.get("cups.spool", default="/tmp/spool")
        if not os.path.exists(dir):
            os.makedirs(dir)
        try:
            server_ppd = self.client.getServerPPD(server_ppd_file)
            is_server_ppd = True
            ppd = cups.PPD(server_ppd)
        except Exception as e:
            self.log.error(str(e))
            is_server_ppd = False

            if custom_ppd_file is not None:
                ppd = cups.PPD(os.path.join(dir, custom_ppd_file))
            else:
                raise PPDException(C.make_error('COULD_NOT_READ_SOURCE_PPD'))

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
                query = {"_type": "GotoPrinter", "gotoPrinterPPD": "%s.ppd" % hash}
                if printer_cn is not None:
                    query["not_"] = {"cn": printer_cn}
                res = index.search(query, {"dn": 1})
                if len(res) == 0:
                    # delete file
                    os.unlink(custom_ppd_file)

            with open(new_file, "w") as f:
                f.write(result)

            return {"gotoPrinterPPD": ["%s.ppd" % hash]}

        except Exception as e:
            self.log.error(str(e))
            return {}
        finally:
            os.unlink(temp_file.name)
            if server_ppd is not None:
                os.unlink(server_ppd)

    @Command(__help__=N_("Get a list of all available printer manufacturers"))
    def getPrinterManufacturers(self):
        if self.client is None:
            return []
        return list(self.__get_printer_list().keys())

    @Command(__help__=N_("Get a list of all available printer models for one manufacturer"))
    def getPrinterModels(self, *args):
        if self.client is None:
            return []
        printers = self.__get_printer_list()
        res = {}
        manufacturer = None
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

    @Command(__help__=N_("Return all printer PPD files associated to a user"))
    def getUserPPDs(self, user):
        index = PluginRegistry.getInstance("ObjectIndex")
        res = index.search({"_type": "User", "uid": user}, {"dn": 1})
        if len(res) == 0:
            raise EntryNotFound(C.make_error("USER_NOT_FOUND", topic=user))

        object = ObjectProxy(res[0]["dn"])
        printer_cns = []
        if object.is_extended_by("GotoEnvironment"):
            printer_cns.append(object.gotoPrinters)
        if object.is_extended_by("PosixUser"):
            for group_cn in object.groupMembership:
                group = ObjectProxy(group_cn)
                if group.is_extended_by("GotoEnvironment"):
                    printer_cns.append(group.gotoPrinters)
        # collect all PPDs
        res = index.search({"_type": "GotoPrinter", "cn": {"in_": printer_cns}}, {"gotoPrinterPPD": 1})
        ppds = []
        for r in res:
            ppds.append(r["gotoPrinterPPD"])
        return ppds

    @Command(__help__=N_("Get a GUI template from a PPD file"))
    def getConfigurePrinterTemplate(self, data):
        """
        Generates a GUI template from a PPD file.
        """
        if self.client is None:
            return
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
            "extensions": {
                "validator": {
                    "target": "form",
                    "name": "Constraints",
                    "properties": {}
                }
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

            constraints = {}
            for constraint in ppd.constraints:
                if constraint.option1 not in constraints:
                    constraints[constraint.option1] = {}
                choice1 = constraint.choice1 if constraint.choice1 is not None else "__choice__"
                if choice1 not in constraints[constraint.option1]:
                    constraints[constraint.option1][choice1] = []
                option2 = ppd.findOption(constraint.option2)

                # find choice
                choice_title = constraint.choice2
                for choice in option2.choices:
                    if choice["choice"] == constraint.choice2:
                        choice_title = choice["text"]

                constraints[constraint.option1][choice1].append({
                    "option": constraint.option2,
                    "optionTitle": option2.text,
                    "choice": constraint.choice2,
                    "choiceTitle": choice_title
                })

            template["extensions"]["validator"]["properties"]["constraints"] = constraints

            for group in sorted(ppd.optionGroups, key=functools.cmp_to_key(self.__compare_group)):
                template["children"].append(self.__read_group(group))

            return template
        except cups.IPPError as e:
            raise CupsException(C.make_error('ERROR_GETTING_SERVER_PPD', str(e)))
        finally:
            if delete is True and ppd_file and os.access(ppd_file, os.F_OK):
                os.unlink(ppd_file)

    def __compare_group(self, group1, group2):
        if group1.name == "General":
            return -1
        elif group2.name == "General":
            return 1
        elif group1.text < group2.text:
            return -1
        elif group1.text > group2.text:
            return 1
        else:
            return 0

    def __read_group(self, group):
        row = 0
        col = 0
        tab = 1
        template = {
            "class": "qx.ui.tabview.Page",
            "layout": "qx.ui.layout.Grow",
            "properties": {
                "label": group.text
            },
            "children": [{
                "class": "qx.ui.container.Scroll",
                "children": []
            }]
        }
        scroll_container = {
            "class": "qx.ui.container.Composite",
            "layout": "qx.ui.layout.Grid",
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
        template["children"][0]["children"].append(scroll_container)
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

            scroll_container["children"].append(label)

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
                    "value": [option.defchoice],
                    "multivalue": option.ui == cups.PPD_UI_PICKMANY
                },
                "class": "gosa.ui.widgets.QComboBoxWidget"
            }
            for choice in option.choices:
                widget["properties"]["values"][choice["choice"]] = {"value": choice["text"]}

            scroll_container["children"].append(widget)
            row += 1
            tab += 1

        return template

    def get_attributes_from_ppd(self, ppd_file, attributes):
        res = {}
        temp_file = tempfile.NamedTemporaryFile(delete=False)
        try:
            if ppd_file[0:4] == "http":
                # fetch remote file and copy it to a temporary local one
                r = requests.get(ppd_file)
                with open(temp_file.name, "w") as tf:
                    tf.write(r.content)
                local_file = tf
            else:
                local_file = ppd_file

            ppd = cups.PPD(local_file)
            ppd.localize()
            for name in attributes:
                attr = ppd.findAttr(name)
                if attr is not None:
                    res[name] = attr.value

        except Exception as e:
            self.log.error(str(e))

        finally:
            os.unlink(temp_file.name)
            return res


class CupsException(Exception):
    pass


class PPDException(Exception):
    pass
