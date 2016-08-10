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

        # Register ourselfs for bus changes on org.freedesktop.login1
        dr = DBusRunner.get_instance()
        self.bus = dr.get_system_bus()
        self.bus.watch_name_owner("org.freedesktop.login1", self.__dbus_proxy_monitor)

    def __dbus_proxy_monitor(self, bus_name):
        """
        This method monitors the DBus service 'org.freedesktop.login1' and whenever there is a
        change in the status (dbus closed/startet) we will take notice.
        And can register or unregister methods to the dbus
        """
        if "org.freedesktop.login1" in self.bus.list_names():
            if self.hal_dbus:
                del(self.hal_dbus)

            # Trigger resend of capability event
            self.hal_dbus = self.bus.get_object('org.freedesktop.login1', '/org/freedesktop/login1')
            ccr = PluginRegistry.getInstance('ClientCommandRegistry')
            ccr.register("shutdown", 'PowerManagement.shutdown', [], [], 'Execute a shutdown of the client.')
            ccr.register("reboot", 'PowerManagement.reboot', [], [], 'Execute a reboot of the client.')
            ccr.register("suspend", 'PowerManagement.suspend', [], [], 'Execute a suspend of the client.')
            ccr.register("hibernate", 'PowerManagement.hibernate', [], [], 'Execute a hibernation of the client.')
            mqtt = PluginRegistry.getInstance('MQTTClientService')
            mqtt.reAnnounce()
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
                mqtt = PluginRegistry.getInstance('MQTTClientService')
                mqtt.reAnnounce()
                self.log.info("lost dbus connection")
            else:
                self.log.info("no dbus connection")

    def shutdown(self):
        """ Execute a shutdown of the client. """
        self.hal_dbus.PowerOff(True, dbus_interface="org.freedesktop.login1.Manager")
        return True

    def reboot(self):
        """ Execute a reboot of the client. """
        self.hal_dbus.Reboot(True, dbus_interface="org.freedesktop.login1.Manager")
        return True

    def suspend(self):
        """ Execute a suspend of the client. """
        self.hal_dbus.Suspend(True, dbus_interface="org.freedesktop.login1.Manager")
        return True

    def hibernate(self):
        """ Execute a hibernation of the client. """
        self.hal_dbus.Hibernate(True, dbus_interface="org.freedesktop.login1.Manager")
        return True
