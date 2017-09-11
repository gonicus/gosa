# This file is part of the GOsa project.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

from pkg_resources import Environment

from gosa.common.components import PluginRegistry
from gosa.common.hsts_request_handler import HSTSStaticFileHandler


class PPDHandler(HSTSStaticFileHandler):

    def initialize(self):
        env = Environment.getInstance()
        dir = env.config.get("cups.spool", default="/tmp/spool")
        super(PPDHandler, self).initialize(dir)

    def get(self, path, include_body=True):

        parts = path.split("/")
        host = parts[:-3]
        manufacturer = parts[:-2]
        model = parts[:-1]
        cups_client = PluginRegistry.getInstance("CupsClient")
        index = PluginRegistry.getInstance("ObjectIndex")


        for ppd, entry in cups_client.getPrinterModels(manufacturer).items():
            if entry["value"] == model:
                res = index.search({"_type": "gotoPrinter", "maker": manufacturer, "serverPPD": ppd}, {'gotoPrinterPPD': 1})
                return super(PPDHandler, self).get(res[0]["gotoPrinterPPD"], include_body)
