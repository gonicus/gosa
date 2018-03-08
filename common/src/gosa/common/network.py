# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

import dbus
from gosa.common.components.dbus_runner import DBusRunner
from logging import getLogger


NM_STATE_UNKNOWN = 0
NM_STATE_ASLEEP = 10
NM_STATE_DISCONNECTED = 20
NM_STATE_DISCONNECTING = 30
NM_STATE_CONNECTING = 40
NM_STATE_CONNECTED_LOCAL = 50
NM_STATE_CONNECTED_SITE = 60
NM_STATE_CONNECTED_GLOBAL = 70


class Monitor(object):

    def __init__(self, callback=None):
        self.__callback = callback
        self.log = getLogger(__name__)
        self.__running = False
        self.__thread = None

        self.log.info("Initializing network state monitor")

        # Initialize DBUS
        dr = DBusRunner.get_instance()
        self.__bus = dr.get_system_bus()

        # Register actions to detect the network state
        self.__upower_actions()
        self.__network_actions()

        # Get current state
        try:
            proxy = self.__bus.get_object('org.freedesktop.NetworkManager', '/org/freedesktop/NetworkManager')
            iface = dbus.Interface(proxy, 'org.freedesktop.DBus.Properties')

            version = str(iface.Get("org.freedesktop.NetworkManager", "Version"))
            if tuple(version.split(".")) < ("0", "9"):
                self.log.warning("network-manager is too old: defaulting to state 'online'")
                self.__state = True

            else:
                # Register actions to detect the network state
                self.__upower_actions()
                self.__network_actions()

                self.__state = iface.Get("org.freedesktop.NetworkManager", "State") in [NM_STATE_CONNECTED_SITE, NM_STATE_CONNECTED_GLOBAL]

        except:
            self.log.warning("no network-manager detected: defaulting to state 'online'")
            self.__state = True

    def is_online(self):
        return self.__state

    def __upower_actions(self):
        try:
            proxy = self.__bus.get_object('org.freedesktop.UPower', '/org/freedesktop/UPower')
            iface = dbus.Interface(proxy, 'org.freedesktop.UPower')

            iface.connect_to_signal("Sleeping", self.__upower_sleeping)
        except:
            self.log.warning("no UPower detected: will not be able to suspend network")

    def __network_actions(self):
        try:
            proxy = self.__bus.get_object('org.freedesktop.NetworkManager', '/org/freedesktop/NetworkManager')
            iface = dbus.Interface(proxy, 'org.freedesktop.NetworkManager')

            iface.connect_to_signal("StateChanged", self.__network_state)
        except:
            self.log.warning("no network-manager detected: will not be able to suspend or activate network")

    def __upower_sleeping(self):
        self.log.info("network down")
        self.__state = False

        if self.__callback:
            self.__callback(False)

    def __network_state(self, state):
        if state in [NM_STATE_CONNECTED_SITE, NM_STATE_CONNECTED_GLOBAL]:
            if self.__state is False:
                self.log.info("network up")
                self.__state = True

                if self.__callback:
                    self.__callback(True)

        elif self.__state is True:
            self.log.info("network down")
            self.__state = False

            if self.__callback:
                self.__callback(False)
