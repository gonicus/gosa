# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

from unittest import TestCase, mock
import pytest
try:
    from gi.repository import GLib
    from gosa.common.components.dbus_runner import *
    has_glib = True
except ImportError:
    has_glib = False


@pytest.mark.skipif(has_glib is False, reason="requires gi package")
class DBusRunnerTestCase(TestCase):

    @mock.patch("gosa.common.components.dbus_runner.GLib.MainLoop")
    def test_runner(self, m_mainloop):
        runner = DBusRunner()
        assert not runner.is_active()

        runner.start()
        assert runner.is_active()
        time.sleep(0.1)

        runner.stop()
        assert not runner.is_active()