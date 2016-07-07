#!/usr/bin/python3

import unittest
import base64
from gosa.common.components.jsonrpc_utils import *

class JSONRPCUtilsTestCase(unittest.TestCase):
    def test_JSONDataHandler(self):
        self.assertRaises(NotImplementedError, JSONDataHandler.encode, None)
        self.assertRaises(NotImplementedError, JSONDataHandler.decode, None)
        self.assertRaises(NotImplementedError, JSONDataHandler.isinstance, None)
        self.assertRaises(NotImplementedError, JSONDataHandler.canhandle)
    def test_DateTimeDateHandler(self):
        data = "TESTING"
        assert DateTimeDateHandler.isinstance(data) == False
        encoded = DateTimeDateHandler.encode(data)
        assert encoded == {'object': data, '__jsonclass__': 'datetime.date'}
        self.assertRaises(ValueError, DateTimeDateHandler.decode, encoded)
        
        data = {"a": "dict"}
        assert DateTimeDateHandler.isinstance(data) == False
        encoded = DateTimeDateHandler.encode(data)
        assert encoded == {'object': str(data), '__jsonclass__': 'datetime.date'}
        self.assertRaises(ValueError, DateTimeDateHandler.decode, encoded)
        
        # isinstance checks if data is a datetime.date.
        # Properly decoded is datetime.datetime.
        data = datetime.datetime(2016, 1, 1, 12, 12)
        assert DateTimeDateHandler.isinstance(data.date())
        encoded = DateTimeDateHandler.encode(data)
        assert encoded == {'object': str(data.date()), '__jsonclass__': 'datetime.date'}
        assert DateTimeDateHandler.decode(encoded) == data.date()
    def test_BinaryHandler(self):
        # BinaryHandler encodes to b"", but decodes from base64?
        # json.Binary does not exist in stdlib
        pass
