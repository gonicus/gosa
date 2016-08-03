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
from gosa.client.join import *


class ClientJoinTestCase(TestCase):

    def test_main(self):
        mo = mock.mock_open()
        with mock.patch("gosa.client.join.os.geteuid", return_value=1100) as m, \
                mock.patch("gosa.client.plugins.join.methods.sys") as mocked_sys, \
                mock.patch('gosa.client.plugins.join.methods.open', return_value=m),\
                mock.patch("gosa.client.plugins.join.cli.input", return_value="test_user"),\
                mock.patch("gosa.client.plugins.join.methods.JSONServiceProxy") as mocked_proxy, \
                mock.patch("gosa.client.join.os.chown") as mocked_chown, \
                mock.patch("gosa.client.join.os.chmod") as mocked_chmod, \
                mock.patch("gosa.client.plugins.join.cli.getpass.getpass", return_value="test_pwd"):
            mocked_sys.argv = ['join', 'http://localhost:8000/rpc']
            mocked_proxy.return_value.joinClient.return_value = ('fake-key', 'fake_uuid')
            with pytest.raises(SystemExit):
                main()

            m.return_value = 0
            with pytest.raises(SystemExit):
                # no group
                main()

            with mock.patch("gosa.client.join.grp") as mocked_grp:
                mocked_grp.getgrname.return_value.gr_gid = 1000
                main()

                with mock.patch("gosa.client.join.Environment.getInstance", side_effect=[ConfigNoFile(), Environment.getInstance(), Environment.getInstance()]),\
                     mock.patch("gosa.client.join.open", return_value=m):
                    main()

