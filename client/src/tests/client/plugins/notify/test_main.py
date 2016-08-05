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
from gosa.client.plugins.notify.main import *


class ClientNotifyTestCase(dbusmock.DBusTestCase):

    @classmethod
    def setUpClass(klass):
        klass.start_system_bus()
        klass.dbus_con = klass.get_dbus(system_bus=True)

    def setUp(self):
        self.inv_mock = self.spawn_server('org.gosa',
                                           '/org/gosa/notify',
                                           'org.gosa',
                                           system_bus=True,
                                           stdout=subprocess.PIPE)

        # Get a proxy for the object's Mock interface
        self.dbus_mock = dbus.Interface(self.dbus_con.get_object(
                                        'org.gosa', '/org/gosa/notify'),
                                        dbusmock.MOCK_IFACE)

        self.dbus_mock.AddMethod('', '_notify', 'sssis', 'i', 'ret = %s' % 1)
        self.dbus_mock.AddMethod('', '_notify_all', 'ssis', 'i', 'ret = %s' % 1)

    def tearDown(self):
        self.inv_mock.terminate()
        self.inv_mock.wait()

    def test_notify(self):
        mo = mock.mock_open()
        with mock.patch("gosa.client.plugins.notify.main.DBusRunner.get_instance") as m,\
                mock.patch("gosa.client.plugins.notify.main.open", mo, create=True):
            m.return_value.get_system_bus.return_value = self.dbus_con
            inv = Notify()
            time.sleep(0.1)
            assert inv.notify("admin", "Title", "message") is 1
            self.assertRegex(self.inv_mock.stdout.readline(), b'^[0-9.]+ _notify "admin" "Title" "message" 0 "dialog-information"\n?$')

            assert inv.notify("admin", "Title", "message", 0, "base64:%s" % base64.b64encode(b"test").decode()) is 1
            handle = mo()
            handle.write.assert_called_once_with(b"test")
            self.assertRegex(self.inv_mock.stdout.readline(), b'^[0-9.]+ _notify "admin" "Title" "message" 0 "/var/spool/gosa/['
                                                              b'^\.]+.png"\n?$')

            mo.reset_mock()
            mo.return_value.__enter__.side_effect = OSError("test")
            assert inv.notify("admin", "Title", "message", 0, "base64:%s" % base64.b64encode(b"test").decode()) is 1
            self.assertRegex(self.inv_mock.stdout.readline(), b'^[0-9.]+ _notify "admin" "Title" "message" 0 "dialog-information"\n?$')


    def test_notify_all(self):
        with mock.patch("gosa.client.plugins.notify.main.DBusRunner.get_instance") as m:
            m.return_value.get_system_bus.return_value = self.dbus_con
            inv = Notify()
            time.sleep(0.1)
            assert inv.notify_all("Title", "message")