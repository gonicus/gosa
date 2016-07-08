# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

from unittest import mock, TestCase
from gosa.shell.main import *


class GosaServiceTestCase(TestCase):

    def test_connect(self):
        with mock.patch("gosa.shell.main.JSONServiceProxy") as m:
            m.return_value.login.return_value = True
            service = GosaService()
            (connection, username, password) = service.connect('http://localhost:8000/rpc', 'admin', 'secret')
            assert connection == 'http://localhost:8000/rpc'
            assert username == 'admin'
            assert password == 'secret'
            m.return_value.login.assert_called_with('admin', 'secret')

