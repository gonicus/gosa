# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

import unittest
from gosa.backend.plugins.samba.logonhours import *

class SambaLogonHoursTestCase(unittest.TestCase):

    def setUp(self):
        self.obj = SambaLogonHoursAttribute()

    def test_values_match(self):
        assert self.obj.values_match("test", "test") is True
        assert self.obj.values_match("test", "test1") is False
        assert self.obj.values_match("1", 1) is True

    def test_is_valid_value(self):
        val = "0" * 168
        assert self.obj.is_valid_value([val]) is True
        assert self.obj.is_valid_value([1]) is False

    def test_convert_to_unicodestring(self):
        assert self.obj._convert_to_unicodestring(["1" * 168]) == ['F' * 42]

    def test_convert_from_string(self):
        assert self.obj._convert_from_string(['F' * 42]) == ["1" * 168]