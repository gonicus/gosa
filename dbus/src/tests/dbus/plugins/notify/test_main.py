# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

from unittest import TestCase, mock
from gosa.dbus.plugins.notify.main import DBusNotifyHandler


class DBusNotifyHandlerTestCase(TestCase):

    def test_notify(self):
        handler = DBusNotifyHandler()
        with mock.patch("gosa.dbus.plugins.notify.main.subprocess.call") as m_call:
            handler._notify("user", "title", "message", 10000, "icon")
            m_call.assert_called_with(['notify-user', 'title', 'message', '--user', 'user', '--icon', 'icon', '--timeout', '10000'])
            m_call.reset_mock()

            handler._notify_all("title", "message", 10000, "icon")
            m_call.assert_called_with(['notify-user', 'title', 'message', '--broadcast','--icon', 'icon', '--timeout', '10000'])
            m_call.reset_mock()

            handler.call( "message", "title", user="user", actions="actions")
            m_call.assert_called_with(['notify-user', 'title', 'message', '--user', 'user', '--icon',
                                       'dialog-information', '--actions', 'actions', '--timeout','120'])

            with mock.patch("gosa.dbus.plugins.notify.main.traceback.print_exc") as m_print_exc:
                m_call.side_effect = Exception("test error")
                handler.call( "message", "title")
                assert m_print_exc.called