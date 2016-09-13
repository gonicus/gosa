# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

"""
.. _dbus-wakeonlan:

GOsa D-Bus Wake on LAN
^^^^^^^^^^^^^^^^^^^^^^^^

This GOsa-DBus plugin provides wake on lan functionality.

>>> proxy.clientDispatch("49cb1287-db4b-4ddf-bc28-5f4743eac594", "dbus_wake_on_lan", "<mac>")
"""


import dbus.service
import subprocess
from gosa.common import Environment
from gosa.common.components import Plugin
from gosa.dbus import get_system_bus


class DBusWakeOnLanHandler(dbus.service.Object, Plugin):
    """
    This GOsa-DBus plugin provides wake on lan functionality.
    """
    def __init__(self):
        conn = get_system_bus()
        dbus.service.Object.__init__(self, conn, '/org/gosa/wol')
        self.env = Environment.getInstance()

    @dbus.service.method('org.gosa', in_signature='s', out_signature='')
    def wake_on_lan(self, mac):
        p = subprocess.Popen([r"wakeonlan", mac])
        p.wait()
        # return exit code, unfortunately wakeonlan returns 0
        # even when an error occurs :(
        return p.returncode
