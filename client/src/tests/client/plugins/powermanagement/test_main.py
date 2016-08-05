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
from unittest import mock
from gosa.client.plugins.powermanagement.main import *


class ClientPowermanagementTestCase(dbusmock.DBusTestCase):

    @classmethod
    def setUpClass(klass):
        klass.start_system_bus()
        klass.dbus_con = klass.get_dbus(system_bus=True)

    def setUp(self):
        self.inv_mock = self.spawn_server('org.freedesktop.login1',
                                           '/org/freedesktop/login1',
                                           'org.freedesktop.login1',
                                           system_bus=True,
                                           stdout=subprocess.PIPE)

        # Get a proxy for the object's Mock interface
        self.dbus_mock = dbus.Interface(self.dbus_con.get_object(
                                        'org.freedesktop.login1', '/org/freedesktop/login1'),
                                        dbusmock.MOCK_IFACE)

        self.dbus_mock.AddMethod('org.freedesktop.login1.Manager', 'PowerOff', 'b', '', '')
        self.dbus_mock.AddMethod('org.freedesktop.login1.Manager', 'Reboot', 'b', '', '')
        self.dbus_mock.AddMethod('org.freedesktop.login1.Manager', 'Suspend', 'b', '', '')
        self.dbus_mock.AddMethod('org.freedesktop.login1.Manager', 'Hibernate', 'b', '', '')

    def tearDown(self):
        self.inv_mock.terminate()
        self.inv_mock.wait()

    def test_shutdown(self):
        with mock.patch("gosa.client.plugins.notify.main.DBusRunner.get_instance") as m:
            m.return_value.get_system_bus.return_value = self.dbus_con
            inv = PowerManagement()
            time.sleep(0.1)
            inv.shutdown()
            self.assertRegex(self.inv_mock.stdout.readline(), b'^[0-9.]+ PowerOff True\n?$')

    def test_reboot(self):
        with mock.patch("gosa.client.plugins.notify.main.DBusRunner.get_instance") as m:
            m.return_value.get_system_bus.return_value = self.dbus_con
            inv = PowerManagement()
            time.sleep(0.1)
            inv.reboot()
            self.assertRegex(self.inv_mock.stdout.readline(), b'^[0-9.]+ Reboot True\n?$')

    def test_suspend(self):
        with mock.patch("gosa.client.plugins.notify.main.DBusRunner.get_instance") as m:
            m.return_value.get_system_bus.return_value = self.dbus_con
            inv = PowerManagement()
            time.sleep(0.1)
            inv.suspend()
            self.assertRegex(self.inv_mock.stdout.readline(), b'^[0-9.]+ Suspend True\n?$')

    def test_hibernate(self):
        with mock.patch("gosa.client.plugins.notify.main.DBusRunner.get_instance") as m:
            m.return_value.get_system_bus.return_value = self.dbus_con
            inv = PowerManagement()
            time.sleep(0.1)
            inv.hibernate()
            self.assertRegex(self.inv_mock.stdout.readline(), b'^[0-9.]+ Hibernate True\n?$')
