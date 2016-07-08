# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

import unittest
from gosa.backend.utils.ldap import *


class LdapUtilsTestCase(unittest.TestCase):

    def setUp(self):
        self.handler = LDAPHandler()
        self.con = self.handler.get_connection()

    def tearDown(self):
        self.handler.free_connection(self.con)
        self.con = None
        self.handler = None

    def test_get_base(self):
        assert self.handler.get_base() == "dc=example,dc=net"


def test_map_ldap_value():
    assert map_ldap_value(True) == "TRUE"
    assert map_ldap_value(False) == "FALSE"
    assert list(map_ldap_value(["Test", True, False])) == ["Test", "TRUE", "FALSE"]


def test_normalize_ldap():
    assert normalize_ldap(True) == [True]
    assert normalize_ldap("Test") == ["Test"]
    assert normalize_ldap(["Test", True, False]) == ["Test", True, False]