# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

from unittest import TestCase, mock
from gosa.dbus.plugins.wakeonlan.main import DBusWakeOnLanHandler


class DBusWakeOnLanHandlerTestCase(TestCase):

    def test_wake_on_lan(self):
        wol = DBusWakeOnLanHandler()
        with mock.patch("gosa.dbus.plugins.wakeonlan.main.subprocess.Popen") as m_popen:
            wol.wake_on_lan("00:00:00:00:00:01")
            m_popen.assert_called_with(['wakeonlan', '00:00:00:00:00:01'])