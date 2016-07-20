# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

"""
.. _client-power:

Power management
================

To. Do.
"""

import logging
from gosa.common.components import Plugin
from gosa.common.components import PluginRegistry
from gosa.common.components.dbus_runner import DBusRunner
from gosa.common import Environment


class PowerManagement(Plugin):
    """
    Utility class that contains methods needed to handle shutdown
    functionality.
    """
    _target_ = 'powermanagement'

    bus = None
    hal_dbus = None

    def __init__(self):
        env = Environment.getInstance()
        self.env = env
        self.log = logging.getLogger(__name__)

        # Register ourselfs for bus changes on org.freedesktop.Hal
        dr = DBusRunner.get_instance()
        self.bus = dr.get_system_bus()
        self.bus.watch_name_owner("org.freedesktop.Hal", self.__dbus_proxy_monitor)

    def __dbus_proxy_monitor(self, bus_name):
        """
        This method monitors the DBus service 'org.gosa' and whenever there is a
        change in the status (dbus closed/startet) we will take notice.
        And can register or unregister methods to the dbus
        """
        if "org.freedesktop.Hal" in self.bus.list_names():
            if self.hal_dbus:
                del(self.hal_dbus)

            # Trigger resend of capapability event
            self.hal_dbus = self.bus.get_object('org.freedesktop.Hal', '/org/freedesktop/Hal/devices/computer')
            ccr = PluginRegistry.getInstance('ClientCommandRegistry')
            ccr = PluginRegistry.getInstance('ClientCommandRegistry')
            ccr.register("shutdown", 'PowerManagement.shutdown', [], [], 'Execute a shutdown of the client.')
            ccr.register("reboot", 'PowerManagement.reboot', [], [], 'Execute a reboot of the client.')
            ccr.register("suspend", 'PowerManagement.suspend', [], [], 'Execute a suspend of the client.')
            ccr.register("hibernate", 'PowerManagement.hibernate', [], [], 'Execute a hibernation of the client.')
            ccr.register("setpowersave", 'PowerManagement.setpowersave', [], [], 'Set powersave mode of the client.')
            amcs = PluginRegistry.getInstance('AMQPClientService')
            amcs.reAnnounce()
            self.log.info("established dbus connection")
        else:
            if self.hal_dbus:
                del(self.hal_dbus)

                # Trigger resend of capapability event
                ccr = PluginRegistry.getInstance('ClientCommandRegistry')
                ccr.unregister("shutdown")
                ccr.unregister("reboot")
                ccr.unregister("suspend")
                ccr.unregister("hibernate")
                ccr.unregister("setpowersave")
                amcs = PluginRegistry.getInstance('AMQPClientService')
                amcs.reAnnounce()
                self.log.info("lost dbus connection")
            else:
                self.log.info("no dbus connection")

    def shutdown(self):
        """ Execute a shutdown of the client. """
        self.hal_dbus.Shutdown(dbus_interface="org.freedesktop.Hal.Device.SystemPowerManagement")
        return True

    def reboot(self):
        """ Execute a reboot of the client. """
        self.hal_dbus.Reboot(dbus_interface="org.freedesktop.Hal.Device.SystemPowerManagement")
        return True

    def suspend(self):
        """ Execute a suspend of the client. """
        self.hal_dbus.Suspend(dbus_interface="org.freedesktop.Hal.Device.SystemPowerManagement")
        return True

    def hibernate(self):
        """ Execute a hibernation of the client. """
        self.hal_dbus.Hibernate(dbus_interface="org.freedesktop.Hal.Device.SystemPowerManagement")
        return True

    def setpowersave(self, enable):
        """ Set powersave mode of the client. """
        self.hal_dbus.SetPowerSave(enable, dbus_interface="org.freedesktop.Hal.Device.SystemPowerManagement")
        return True
