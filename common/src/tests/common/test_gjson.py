#!/usr/bin/python3

import unittest, json
from gosa.common.gjson import *
from gosa.common.components.jsonrpc_utils import PObjectEncoder, PObjectDecoder

class GJSONTestCase(unittest.TestCase):
    def test_dumps(self):
        obj = {"TEST": 1, "TEST2": {"t": "t"}, "TEST3": [1, 2, 3], "TEST4": (1, 2, 3)}
        assert dumps(obj) == json.dumps(obj, cls=PObjectEncoder)
    def test_loads(self):
        obj = {"TEST": 1, "TEST2": {"t": "t"}, "TEST3": [1, 2, 3], "TEST4": (1, 2, 3)}
        json_str = json.dumps(obj, cls=PObjectEncoder)
        obj["TEST4"] = [1, 2, 3]
        assert loads(json_str.encode()) == obj
