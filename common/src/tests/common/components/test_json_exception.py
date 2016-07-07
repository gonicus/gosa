#!/usr/bin/python3

import unittest
import base64
from gosa.common.components.json_exception import *

class JSONRPCExceptionTestCase(unittest.TestCase):
    def test_JSONRPCException(self):
        o = "TEST"
        e = JSONRPCException(o)
        assert e.error == o
