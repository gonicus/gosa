# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.
import logging
from zope.interface import implementer

from gosa.common import Environment
from gosa.common.components import Plugin, Command, PluginRegistry
from gosa.common.components.dbus_runner import DBusRunner
from gosa.common.handler import IInterfaceHandler


@implementer(IInterfaceHandler)
class PrinterConfiguration(Plugin):
    _priority_ = 99
    bus = None
    gosa_dbus = None
    _target_ = 'configuration'

    def __init__(self):
        self.env = Environment.getInstance()
        self.log = logging.getLogger(__name__)

    def serve(self):
        # Register ourselfs for bus changes on org.gosa
        dr = DBusRunner.get_instance()
        self.bus = dr.get_system_bus()
        self.bus.watch_name_owner("org.gosa", self.__dbus_proxy_monitor)
        self.log.info("dbus connection established")

    def __dbus_proxy_monitor(self, bus_name):
        """
        This method monitors the DBus service 'org.gosa' and whenever there is a
        change in the status (dbus closed/started) we will take notice.
        And can register or unregister methods to the dbus
        """
        if "org.gosa" in self.bus.list_names():
            if self.gosa_dbus:
                del self.gosa_dbus
            self.gosa_dbus = self.bus.get_object('org.gosa', '/org/gosa/cups')
            ccr = PluginRegistry.getInstance('ClientCommandRegistry')
            ccr.register("configureHostPrinters", 'PrinterConfiguration.configureHostPrinters', [],
                         ['config'],
                         'Configure the printers for this client')
            mqtt = PluginRegistry.getInstance('MQTTClientService')
            mqtt.reAnnounce()
            self.log.info("established dbus connection")

        else:
            if self.gosa_dbus:
                del self.gosa_dbus

                # Trigger resend of capapability event
                ccr = PluginRegistry.getInstance('ClientCommandRegistry')
                ccr.unregister("configureHostPrinters")
                mqtt = PluginRegistry.getInstance('MQTTClientService')
                mqtt.reAnnounce()
                self.log.info("lost dbus connection")
            else:
                self.log.info("no dbus connection")

    @Command()
    def configureUserPrinters(self, user, ppds):
        """ configure a users printers """
        pass

    def configureHostPrinters(self, config):
        """ configure the printers for this client via dbus. """

        if "printers" in config:
            self.gosa_dbus.deleteAllPrinters(dbus_interface="org.gosa")
            for p_conf in config["printers"]:
                self.gosa_dbus.addPrinter(p_conf, dbus_interface="org.gosa")

        if "defaultPrinter" in config and config["defaultPrinter"] is not None:
            self.gosa_dbus.defaultPrinter(config["defaultPrinter"], dbus_interface="org.gosa")
