#!/usr/bin/python3

import unittest
import inspect
import gosa.common.exceptions

class ExceptionsTestCase(unittest.TestCase):
    def test_Exceptions(self):
        # Note: This test relies on gosa.common.exceptions to only contain
        # classes which are Exceptions (and other attributes starting with "__").
        i = 0
        for name, exc in inspect.getmembers(gosa.common.exceptions):
            if name.startswith("__"): continue
            if inspect.isclass(exc):
                assert issubclass(exc, Exception)
                i += 1
        assert i == 19
