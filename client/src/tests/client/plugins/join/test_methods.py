# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.
import pytest
from unittest import mock, TestCase
from gosa.client.plugins.join.methods import *


class ClientJoinTestCase(TestCase):

    def test_login(self):
        join = join_method()

        with mock.patch.object(join, "key", new_callable=mock.PropertyMock, return_value="fake_key"),\
                mock.patch("gosa.client.plugins.join.methods.JSONServiceProxy") as mocked_proxy, \
                mock.patch.object(join, "show_error") as mocked_show_error:
            mocked_proxy.return_value.login.return_value = False
            assert join.test_login() is False

            mocked_proxy.return_value.login.side_effect = HTTPError(None, 401, "Test error", None, None)
            assert join.test_login() is False
            assert mocked_show_error.called

            mocked_show_error.reset_mock()
            with mock.patch("gosa.client.plugins.join.methods.sys.exit") as mocked_exit:
                mocked_proxy.return_value.login.side_effect = HTTPError(None, 500, "Test error", None, None)
                join.test_login()
                assert not mocked_show_error.called
                assert mocked_exit.called

                mocked_exit.reset_mock()
                mocked_proxy.return_value.login.side_effect = Exception("Test error")
                join.test_login()
                assert not mocked_show_error.called
                assert mocked_exit.called

                mocked_proxy.return_value.login.side_effect = None
                mocked_proxy.return_value.login.return_value = True
                assert join.test_login() is True

    def test_join(self):
        join = join_method()

        with mock.patch("gosa.client.plugins.join.methods.JSONServiceProxy") as mocked_proxy, \
                mock.patch.object(join, "show_error") as mocked_show_error:
            mocked_proxy.return_value.login.return_value = False
            assert join.join("admin", "tester") is False
            assert mocked_show_error.called

            mocked_show_error.reset_mock()
            mocked_proxy.return_value.login.side_effect = HTTPError(None, 401, "Test error", None, None)
            assert join.join("admin", "tester") is False
            assert mocked_show_error.called

            mocked_show_error.reset_mock()
            mocked_proxy.return_value.login.side_effect = HTTPError(None, 500, "Test error", None, None)
            with pytest.raises(SystemExit):
                join.join("admin", "tester")
            assert not mocked_show_error.called

            with pytest.raises(SystemExit):
                mocked_proxy.return_value.login.side_effect = Exception("Test error")
                join.join("admin", "tester")
            assert not mocked_show_error.called

            mocked_proxy.return_value.login.side_effect = None
            mocked_proxy.return_value.login.return_value = True

            mocked_proxy.return_value.joinClient.side_effect = JSONRPCException("test exception")
            assert join.join("admin", "tester") is None
            assert mocked_show_error.called

            mocked_proxy.return_value.joinClient.side_effect = None
            mocked_proxy.return_value.joinClient.return_value = "fake_key", "fake_uuid"

            with mock.patch("gosa.client.plugins.join.methods.open", mock.mock_open()) as mocked_open:
                assert join.join("admin", "tester") == "fake_key"
                handle = mocked_open()
                assert handle.write.called

    @mock.patch("gosa.client.plugins.join.methods.join_method.show_error")
    def test_get_mac_address(self, mocked_show_error):
        join = join_method()
        with mock.patch("gosa.client.plugins.join.methods.netifaces.interfaces", return_value=[]) as mocked_ifaces, \
                mock.patch("gosa.client.plugins.join.methods.netifaces.ifaddresses", return_value=[]) as mocked_ifaddresses:
            assert join.get_mac_address() is None

            mocked_ifaces.return_value = ['loop0', 'loop1', 'loop2']
            mocked_ifaddresses.side_effect = [{
                netifaces.AF_LINK: [
                    {'addr': '00:00:00:00:00:00'}
                ]
            }, {
                netifaces.AF_LINK: [
                    {'addr': '00:00:00:00:00:01'}
                ]
            }, {
                netifaces.AF_LINK: [
                    {'addr': '00:00:00:00:00:02'}
                ],
                netifaces.AF_INET: []
            }]
            assert join.get_mac_address() is '00:00:00:00:00:02'