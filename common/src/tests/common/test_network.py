# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

from unittest import mock, TestCase
import dbusmock
import subprocess
import pytest
import dbus
try:
    from gosa.common.network import Monitor, NM_STATE_DISCONNECTED, NM_STATE_CONNECTED_GLOBAL, NM_STATE_CONNECTED_SITE
    from gi.repository import GLib
    has_glib = True
except ImportError:
    has_glib = False
from tests.helper import slow


@slow
@pytest.mark.skipif(has_glib is False, reason="requires gi package")
class MonitorTestCase(dbusmock.DBusTestCase):

    @classmethod
    def setUpClass(klass):
        klass.start_system_bus()
        klass.dbus_con = klass.get_dbus(system_bus=True)

    def setUp(self):
        (self.nm_mock, self.obj_network) = self.spawn_server_template('networkmanager', stdout=subprocess.PIPE)
        (self.up_mock, self.obj_upower) = self.spawn_server_template('upower', stdout=subprocess.PIPE)
        self.dbus_props = dbus.Interface(self.obj_network, dbus.PROPERTIES_IFACE)

    def tearDown(self):
        self.nm_mock.terminate()
        self.nm_mock.wait()
        self.up_mock.terminate()
        self.up_mock.wait()

    def emit_signal(self, object, signal, signature, args):
        ml = GLib.MainLoop()

        def do_emit():
            object.EmitSignal('', signal, signature, args)

        GLib.timeout_add(200, do_emit)
        # ensure that the loop quits even when we catch nothing
        GLib.timeout_add(3000, ml.quit)
        ml.run()

    def test_old_version(self):
        self.dbus_props.Set("org.freedesktop.NetworkManager", "Version", "0.8.7.0")
        self.dbus_props.Set("org.freedesktop.NetworkManager", "State", dbus.UInt32(NM_STATE_DISCONNECTED, variant_level=1))

        monitor = Monitor()
        assert monitor.is_online()

    def test_is_online(self):
        self.dbus_props.Set("org.freedesktop.NetworkManager", "Version", "0.9.7.0")
        self.dbus_props.Set("org.freedesktop.NetworkManager", "State", dbus.UInt32(NM_STATE_CONNECTED_GLOBAL, variant_level=1))

        callback = mock.MagicMock()
        monitor = Monitor(callback)

        assert monitor.is_online()

        # test signals
        self.emit_signal(self.obj_network, 'StateChanged', 'u', [NM_STATE_DISCONNECTED])
        assert not monitor.is_online()
        callback.assert_called_with(False)

    def test_network_offline(self):
        self.dbus_props.Set("org.freedesktop.NetworkManager", "Version", "0.9.7.0")
        self.dbus_props.Set("org.freedesktop.NetworkManager", "State", dbus.UInt32(NM_STATE_CONNECTED_GLOBAL, variant_level=1))

        callback = mock.MagicMock()
        monitor = Monitor(callback)

        assert monitor.is_online()

        self.emit_signal(self.obj_network, 'StateChanged', 'u', [NM_STATE_CONNECTED_SITE])
        assert monitor.is_online()
        callback.assert_called_with(True)

    # @skip(msg="emitting events without arguments does not seem to work in dbusmock")
    # def test_upower_sleep(self):
    #     self.dbus_props.Set("org.freedesktop.NetworkManager", "Version", "0.9.7.0")
    #     self.dbus_props.Set("org.freedesktop.NetworkManager", "State", dbus.UInt32(NM_STATE_CONNECTED_SITE, variant_level=1))
    #
    #     callback = mock.MagicMock()
    #     monitor = Monitor(callback)
    #
    #     assert monitor.is_online()
    #     print(self.obj_upower)
    #     self.emit_signal(self.obj_upower, 'Sleeping', '', [])
    #     assert not monitor.is_online()
    #     callback.assert_called_with(False)

@pytest.mark.skipif(has_glib is False, reason="requires gi package")
class MonitorWithoutDbusTestCase(TestCase):

    def test_init(self):
        with mock.patch("gosa.common.network.DBusRunner.get_instance") as m_runner,\
                mock.patch("gosa.common.network.getLogger") as m_logger:
            m_runner.return_value.get_system_bus.return_value.get_object.side_effect = Exception("test error")
            monitor = Monitor()

            # default value is 'online'
            assert monitor.is_online()
            m_logger.return_value.warning.assert_called_with("no network-manager detected: defaulting to state 'online'")

