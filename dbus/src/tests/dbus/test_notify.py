# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

import pytest
import getpass
from unittest import TestCase, mock
from gosa.dbus.notify import *


@mock.patch("gosa.dbus.notify.dbus.Interface")
class NotifyTestCase(TestCase):

    def test_send(self, m_service):
        notify = Notify()
        m_service.return_value.GetCapabilities.return_value = []
        assert notify.send("title", "message", None) == RETURN_ABORTED
        assert notify.send("title", "message", "unknown_session") == RETURN_ABORTED

        with mock.patch("gosa.dbus.notify.dbus.connection.Connection._new_for_bus") as m_bus:
            m_bus.return_value = mock.MagicMock()

            notify.send("Title", "Message", "unix:abstract=/tmp/dbus-4G8ZUWpvcY")
            m_service.return_value.Notify.assert_called_with("Gosa Client", 0, "", "Title", "Message", [], {}, 5000)

        del notify

    @pytest.mark.skipif('TRAVIS' in os.environ and os.environ['TRAVIS'] == "true", reason="DBUS test do not work on Travis CI")
    def test_main(self, m_service):
        m_service.return_value.GetCapabilities.return_value = []

        sys.argv = ['notify', '-t', '2', '-v', 'Title', 'Message']

        with mock.patch("gosa.dbus.notify.os.fork", return_value=0):
            with pytest.raises(SystemExit):
                main()
            m_service.return_value.Notify.assert_called_with("Gosa Client", 0, "dialog-information", "Title", "Message", [], {}, 2000)
            m_service.reset_mock()

            sys.argv = ['notify', '-b', '-u', 'tester', 'Title', 'Message']
            with pytest.raises(PermissionError):
                main()
            assert not m_service.return_value.Notify.called

    def test_send_to_user(self, m_service):
        notify = Notify()
        assert notify.send_to_user("title", "message", "unknown_user") == RETURN_ABORTED