# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

"""

.. _client-notify:

GOsa Client Notification Plugin
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This plugin allows to send notification to a user or a list of users.

e.g.:

>>> proxy.clientDispatch("49cb1287-db4b-4ddf-bc28-5f4743eac594", "notify", "user1", "Hallo", "This is a message")

>>> proxy.clientDispatch("49cb1287-db4b-4ddf-bc28-5f4743eac594", "notify_all", "Hallo", "This is a message")

"""

# -*- coding: utf-8 -*-
import os
import logging
import base64
import hashlib
from gosa.common import Environment
from gosa.common.components.dbus_runner import DBusRunner
from gosa.common.components import PluginRegistry, Plugin


class Notify(Plugin):
    _target_ = 'notify'
    bus = None
    gosa_dbus = None

    def __init__(self):
        env = Environment.getInstance()
        self.env = env
        self.log = logging.getLogger(__name__)

        # Register ourselfs for bus changes on org.gosa
        dr = DBusRunner.get_instance()
        self.bus = dr.get_system_bus()
        self.bus.watch_name_owner("org.gosa", self.__dbus_proxy_monitor)

        # Create icon cache directory
        self.spool = env.config.get("client.spool", default="/var/spool/gosa")

    def __dbus_proxy_monitor(self, bus_name):
        """
        This method monitors the DBus service 'org.gosa' and whenever there is a
        change in the status (dbus closed/started) we will take notice.
        And can register or unregister methods to the dbus
        """
        if "org.gosa" in self.bus.list_names():
            if self.gosa_dbus:
                del self.gosa_dbus
            self.gosa_dbus = self.bus.get_object('org.gosa', '/org/gosa/notify')
            ccr = PluginRegistry.getInstance('ClientCommandRegistry')
            ccr.register("notify", 'Notify.notify', [],
                         ['user', 'title', 'message', 'timeout', 'icon'],
                         'Sent a notification to a given user')
            ccr.register("notify_all", 'Notify.notify_all', [],
                         ['title', 'message', 'timeout', 'icon'],
                         'Sent a notification to a given user')
            mqtt = PluginRegistry.getInstance('MQTTClientService')
            mqtt.reAnnounce()
            self.log.info("established dbus connection")

        else:
            if self.gosa_dbus:
                del self.gosa_dbus

                # Trigger resend of capapability event
                ccr = PluginRegistry.getInstance('ClientCommandRegistry')
                ccr.unregister("notify")
                ccr.unregister("notify_all")
                mqtt = PluginRegistry.getInstance('MQTTClientService')
                mqtt.reAnnounce()
                self.log.info("lost dbus connection")
            else:
                self.log.info("no dbus connection")

    def notify(self, user, title, message, timeout=0, icon="dialog-information"):

        # If the icon is base64 encoded, save it as a hash filename to
        # our home directory
        if icon.startswith("base64:"):
            data = base64.b64decode(icon[7:])
            m = hashlib.md5()
            m.update(data)
            icon = os.path.join(self.spool, m.hexdigest() + ".png")

            try:
                with open(icon, "w") as f:
                    f.write(data)

            except OSError:
                icon = "dialog-information"

        # Send notification and keep return code
        o = self.gosa_dbus._notify(user, title, message, timeout,
                                   icon, dbus_interface="org.gosa")
        return int(o)

    def notify_all(self, title, message, timeout=0, icon="dialog-information"):
        """ Send a notification to all users on a machine """

        # Send notification and keep return code
        o = self.gosa_dbus._notify_all(title, message, timeout,
                                       icon, dbus_interface="org.gosa")
        return int(o)
