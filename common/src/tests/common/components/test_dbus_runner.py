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
from gosa.common.components.dbus_runner import *


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