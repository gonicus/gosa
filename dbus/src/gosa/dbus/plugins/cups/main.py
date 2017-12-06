# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

"""
.. _dbus-cups:

GOsa D-Bus CUPS Plugin
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This plugin allows to configure cups printers.

"""
import logging
import tempfile
import os
import cups
import dbus.service
from requests import get, utils

from gosa.common import Environment
from gosa.common.components import Plugin
from gosa.dbus import get_system_bus


class DBusCupsHandler(dbus.service.Object, Plugin):
    """
    This dbus plugin is able to add / delete printers and set a default printer.

    """

    def __init__(self):
        conn = get_system_bus()
        dbus.service.Object.__init__(self, conn, '/org/gosa/cups')
        self.env = Environment.getInstance()
        self.log = logging.getLogger(__name__)

    @dbus.service.method('org.gosa', in_signature='', out_signature='')
    def deleteAllPrinters(self):
        connection = cups.Connection()
        for printer in connection.getPrinters():
            connection.deletePrinter(printer)

    @dbus.service.method('org.gosa', in_signature='a{ss}', out_signature='b')
    def addPrinter(self, config):
        """
        Add a printer to CUPS
        """
        connection = cups.Connection()
        temp_file = tempfile.NamedTemporaryFile(delete=False)
        with open(temp_file.name, "w") as tf:
            response = get(utils.quote(config["gotoPrinterPPD"], safe=":/"))
            tf.write(response.content.decode('utf-8'))
        try:
            connection.addPrinter(
                config["cn"],
                info=config["description"],
                filename=temp_file.name,
                location=config["l"],
                device=config["labeledURI"])
            connection.enablePrinter(config["cn"])
            connection.acceptJobs(config["cn"])
            return True
        except cups.IPPError as e:
            self.log.error(str(e))
            return False
        finally:
            os.unlink(temp_file.name)

    @dbus.service.method('org.gosa', in_signature='s', out_signature='b')
    def defaultPrinter(self, name):
        """
        Set the default printer
        """
        try:
            connection = cups.Connection()
            connection.setDefault(name)
            return True
        except cups.IPPError as e:
            self.log.error(str(e))
            return False


