# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.
import cups
from colorlog import logging
from zope.interface import implementer

from gosa.common import Environment
from gosa.common.components import Plugin, Command
from gosa.common.handler import IInterfaceHandler


@implementer(IInterfaceHandler)
class PrinterConfiguration(Plugin):
    _priority_ = 99
    _target_ = 'session'

    def __init__(self):
        self.env = Environment.getInstance()
        self.log = logging.getLogger(__name__)

    @Command()
    def configureUserPrinters(self, user, ppds):
        """ configure a users printers """
        pass

    @Command()
    def configureHostPrinters(self, config):
        """ configure the printers for this client """
        connection = cups.Connection()

        if "printers" in config:
            for p_conf in config["printers"]:
                self.__addPrinter(p_conf, connection)

        if "defaultPrinter" in config and config["defaultPrinter"] is not None:
            connection.setDefault(config["defaultPrinter"])

    def __addPrinter(self, config, connection):
        connection.addPrinter(
            config["cn"],
            info=config["description"],
            filename=config["gotoPrinterPPD"],
            location=config["l"],
            device=config["labeledURI"])
        connection.enablePrinter(config["cn"])
        connection.acceptJobs(config["cn"])