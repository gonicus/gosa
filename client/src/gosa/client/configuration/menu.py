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
from gosa.common.components import Plugin, PluginRegistry
from gosa.common.components.dbus_runner import DBusRunner
from gosa.common.handler import IInterfaceHandler


@implementer(IInterfaceHandler)
class MenuConfiguration(Plugin):
    _priority_ = 99
    _target_ = 'session'

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
            self.gosa_dbus = self.bus.get_object('org.gosa', '/org/gosa/environment')
            ccr = PluginRegistry.getInstance('ClientCommandRegistry')
            ccr.register("configureUserMenu", 'MenuConfiguration.configureUserMenu', [],
                         ['user', 'config'],
                         'Configure the printers for the user on this client')
            mqtt = PluginRegistry.getInstance('MQTTClientService')
            mqtt.reAnnounce()
            self.log.info("established dbus connection")

        else:
            if self.gosa_dbus:
                del self.gosa_dbus

                # Trigger resend of capapability event
                ccr = PluginRegistry.getInstance('ClientCommandRegistry')
                ccr.unregister("configureUserMenu")
                mqtt = PluginRegistry.getInstance('MQTTClientService')
                mqtt.reAnnounce()
                self.log.info("lost dbus connection")
            else:
                self.log.info("no dbus connection")

    def configureUserMenu(self, user, config):
        self.gosa_dbus.configureUserMenu(user, config, dbus_interface="org.gosa")
