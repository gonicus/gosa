#!/usr/bin/python3

import unittest
from gosa.common.components.plugin import *

class TestPlugin(Plugin):
    _target_ = "noncore"

class JSONRPCUtilsTestCase(unittest.TestCase):
    def test_Plugin(self):
        p = TestPlugin()
        assert p.get_locale_module() == p._locale_module_
        # _target_ attribute is not initialized in this class (but in subclasses)
        assert p.get_target() == p._target_
