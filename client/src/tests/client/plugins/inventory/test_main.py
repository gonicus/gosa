# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.
import subprocess
import dbus
import dbusmock
import time
import pytest
from unittest import mock
from gosa.client.plugins.dbus.inventory import *


class ClientDbusProxyTestCase(dbusmock.DBusTestCase):

    @classmethod
    def setUpClass(klass):
        klass.start_system_bus()
        klass.dbus_con = klass.get_dbus(system_bus=True)

    def setUp(self):
        self.p_mock = self.spawn_server('org.gosa',
                                        '/org/gosa/inventory',
                                        'org.gosa.inventory',
                                        system_bus=True,
                                        stdout=subprocess.PIPE)

        # Get a proxy for the UPower object's Mock interface
        self.dbus_upower_mock = dbus.Interface(self.dbus_con.get_object(
            'org.gosa', '/org/gosa/inventory'),
            dbusmock.MOCK_IFACE)

        self.dbus_upower_mock.AddMethod('', 'request_inventory', 's', '', '')

    def tearDown(self):
        self.p_mock.terminate()
        self.p_mock.wait()
