# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.
import subprocess
import time
from unittest import mock
from gosa.client.plugins.sessions.main import *
from tests.dbus_test_case import ClientDBusTestCase


class ClientSessionTestCase(ClientDBusTestCase):

    def setUp(self):
        (self.inv_mock, self.dbus_mock) = self.spawn_server_template('logind', stdout=subprocess.PIPE)

        self.dbus_mock.AddMethod('org.freedesktop.login1.Manager', 'ListUsers', '', 'a(iss)', 'ret = [(1010, "tester", "/home/tester")]')

    def tearDown(self):
        self.inv_mock.terminate()
        self.inv_mock.wait()

    def test_signal(self):
        with mock.patch("gosa.client.plugins.notify.main.DBusRunner.get_instance") as m:
            m.return_value.get_system_bus.return_value = self.dbus_con
            inv = SessionKeeper()
            inv.serve()
            time.sleep(0.3)

            self.dbus_mock.EmitSignal("org.freedesktop.login1.Manager", "SessionNew", "", [])
            time.sleep(0.2)

            assert '1010' in inv.getSessions()

            inv.stop()

    def test_resume(self):
        with mock.patch("gosa.client.plugins.notify.main.DBusRunner.get_instance") as m:
            m.return_value.get_system_bus.return_value = self.dbus_con
            inv = SessionKeeper()
            inv.serve()
            time.sleep(0.3)

            with mock.patch.object(inv, "sendSessionNotification") as m:
                zope.event.notify(Resume())
                assert m.called

            inv.stop()