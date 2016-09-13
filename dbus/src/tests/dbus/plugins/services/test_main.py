# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.
import pytest
from unittest import TestCase, mock
from gosa.dbus.plugins.services.main import *


class DBusUnixServiceHandlerTestCase(TestCase):

    def setUp(self):
        super(DBusUnixServiceHandlerTestCase, self).setUp()
        with mock.patch("gosa.dbus.plugins.services.main.dbus.Interface") as m_if:
            self.handler = DBusUnixServiceHandler()
            self.m_systemd = m_if.return_value

    def tearDown(self):
        super(DBusUnixServiceHandlerTestCase, self).tearDown()
        self.handler.remove_from_connection()
        del self.handler

    def test_start_service(self):
        with pytest.raises(NotAServiceException):
            self.handler.start_service("unknown")
        self.handler.start_service("test.service")
        self.m_systemd.StartUnit.assert_called_with("test.service", "replace")

    def test_stop_service(self):
        with pytest.raises(NotAServiceException):
            self.handler.stop_service("unknown")
        self.handler.stop_service("test.service")
        self.m_systemd.StopUnit.assert_called_with("test.service", "replace")

    def test_reload_service(self):
        with pytest.raises(NotAServiceException):
            self.handler.reload_service("unknown")
        self.handler.reload_service("test.service")
        self.m_systemd.ReloadUnit.assert_called_with("test.service", "replace")

    def test_restart_service(self):
        with pytest.raises(NotAServiceException):
            self.handler.restart_service("unknown")
        self.handler.restart_service("test.service")
        self.m_systemd.RestartUnit.assert_called_with("test.service", "replace")

    def test_reload_or_restart_service(self):
        with pytest.raises(NotAServiceException):
            self.handler.reload_or_restart_service("unknown")
        self.handler.reload_or_restart_service("test.service")
        self.m_systemd.ReloadOrRestartUnit.assert_called_with("test.service", "replace")

    def test_reload_or_try_restart_service(self):
        with pytest.raises(NotAServiceException):
            self.handler.reload_or_try_restart_service("unknown")
        self.handler.reload_or_try_restart_service("test.service")
        self.m_systemd.ReloadOrTryRestartUnit.assert_called_with("test.service", "replace")

    def test_kill_service(self):
        with pytest.raises(NotAServiceException):
            self.handler.kill_service("unknown", "tester", 1010)
        self.handler.kill_service("test.service", "tester", 1010)
        self.m_systemd.KillUnit.assert_called_with("test.service", "tester", 1010)

    def test_get_service(self):
        with pytest.raises(NotAServiceException):
            self.handler.get_service("unknown")

        with pytest.raises(NoSuchServiceException):
            self.handler.get_service("test.service")

        self.m_systemd.ListUnits.return_value = [
            ("test.service", "", "", "active", "running"),
            ("test.other", "", "", "active", "running")
        ]
        assert self.handler.get_service("test.service") == {
            "active": ["True"],
            "running": ["True"]
        }

    def test_reboot(self):
        self.handler.reboot()
        assert self.m_systemd.Reboot.called

    def test_poweroff(self):
        self.handler.poweroff()
        assert self.m_systemd.PowerOff.called

    def test_halt(self):
        self.handler.halt()
        assert self.m_systemd.Halt.called