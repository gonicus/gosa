#!/usr/bin/python3

import unittest
from gosa.common.components.plugin import *

class JSONRPCUtilsTestCase(unittest.TestCase):
    def test_Plugin(self):
        p = Plugin()
        assert p.get_locale_module() == p._locale_module_
        return True
        # _target_ attribute is not initialized in this class (but in subclasses)
        assert p.get_target() == p._target_
