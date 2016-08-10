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
from gosa.client.plugins.dbus.proxy import *
from tests.dbus_test_case import ClientDBusTestCase


class ClientDbusProxyTestCase(ClientDBusTestCase):

    def setUp(self):
        self.p_mock = self.spawn_server('org.gosa',
                                        '/org/gosa',
                                        'org.gosa',
                                        system_bus=True,
                                        stdout=subprocess.PIPE)

        # Get a proxy for the object's Mock interface
        self.dbus_mock = dbus.Interface(self.dbus_con.get_object(
            'org.gosa', '/org/gosa'),
            dbusmock.MOCK_IFACE)

        self.dbus_mock.AddMethod('', 'test_method', 's', '', '')

    def tearDown(self):
        self.p_mock.terminate()
        self.p_mock.wait()

    def test_proxy(self):
        with mock.patch("gosa.client.plugins.dbus.proxy.DBusRunner.get_instance") as m:
            m.return_value.get_system_bus.return_value = self.dbus_con
            proxy = DBUSProxy()
            proxy.serve()
            time.sleep(0.3)
            res = proxy.listDBusMethods()
            assert 'dbus_test_method' in res
            assert res['dbus_test_method']['path'] == "/org/gosa"
            assert res['dbus_test_method']['service'] == "org.gosa"
            assert res['dbus_test_method']['args'] == (('arg1', 's'),)

    def test_callDBusMethod(self):
        with mock.patch("gosa.client.plugins.dbus.proxy.DBusRunner.get_instance") as m:
            m.return_value.get_system_bus.return_value = self.dbus_con
            proxy = DBUSProxy()
            proxy.serve()
            time.sleep(0.3)

            with pytest.raises(TypeError):
                proxy.callDBusMethod("dbus_test_method", 1)

            proxy.callDBusMethod("dbus_test_method", "test")
            self.assertRegex(self.p_mock.stdout.readline(), b'^[0-9.]+ test_method "test"\n?$')

            with pytest.raises(DBusProxyException):
                proxy.gosa_dbus = None
                proxy.callDBusMethod("dbus_test_method", "test")