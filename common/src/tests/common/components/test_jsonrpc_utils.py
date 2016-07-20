#!/usr/bin/python3

import unittest
import base64
import json
import pytest
from io import StringIO
from gosa.common.components.jsonrpc_utils import *

class ProxyDummy:
    new_proxy = unittest.mock.MagicMock()
    def __call__(self):
        return FactoryHandler.decode({"object": "data", "__jsonclass__": ["json.FactoryHandler", ["json.FactoryHandler"]]})
    def getProxy(self, *args, **kwargs):
        return ProxyDummy.new_proxy

class JSONRPCUtilsTestCase(unittest.TestCase):
    def test_JSONRPCException(self):
        error = "error details"
        e = JSONRPCException(error)
        assert e.error == error
        assert isinstance(e, Exception)
    def test_JSONDataHandler(self):
        self.assertRaises(NotImplementedError, JSONDataHandler.encode, None)
        self.assertRaises(NotImplementedError, JSONDataHandler.decode, None)
        self.assertRaises(NotImplementedError, JSONDataHandler.isinstance, None)
        self.assertRaises(NotImplementedError, JSONDataHandler.canhandle)
    def handlerTest(self, handlerClass, handlerType, testData):
        assert issubclass(handlerClass, JSONDataHandler)
        assert handlerClass.canhandle() == handlerType
        
        # Handlers are not checking for passed type
        data = object()
        assert handlerClass.isinstance(data) == False
        encoded = handlerClass.encode(data)
        assert encoded == {'object': str(data), '__jsonclass__': handlerType}
        self.assertRaises(ValueError, handlerClass.decode, encoded)
        
        assert handlerClass.isinstance(testData)
        encoded = handlerClass.encode(testData)
        assert encoded == {'object': str(testData), '__jsonclass__': handlerType}
        assert handlerClass.decode(encoded) == testData
    def test_DateTimeDateHandler(self):
        self.handlerTest(DateTimeDateHandler, "datetime.date", datetime.date(2016, 12, 12))
        
        # DateTimeDateHandler will convert datetimes to dates
        dtTest = datetime.datetime(2016, 12, 12, 1, 1)
        assert DateTimeDateHandler.encode(dtTest) == DateTimeDateHandler.encode(dtTest.date())
    def test_DateTimeHandler(self):
        self.handlerTest(DateTimeHandler, "datetime.datetime", datetime.datetime(2016, 12, 12, 1, 1))
    def test_BinaryHandler(self):
        assert issubclass(BinaryHandler, JSONDataHandler)
        
        # json.Binary looks like a top level identifier but refers to Binary in this package.
        assert BinaryHandler.canhandle() == "json.Binary"
        
        # BinaryHandler behaves slightly different compared to the others:
        # It relies on the passed by object to have the "encode" method.
        b = Binary(b"TEST")
        assert BinaryHandler.isinstance(b)
        encoded = BinaryHandler.encode(b)
        assert encoded == {'object': b.encode(), '__jsonclass__': 'json.Binary'}
        assert BinaryHandler.decode(encoded) == b
    def test_Binary(self):
        data1 = b"DATA1"
        b1 = Binary(data1)
        assert b1.__eq__(b1)
        assert b1.data == data1
        assert b1.get() == data1
        
        data2 = b"DATA2"
        b1.set(data2)
        assert b1.data == data2
        assert b1.get() == data2
        assert b1.encode() == base64.b64encode(data2)
        
        b2 = Binary(data2)
        assert b1.__eq__(b2)
        b2.set(data1)
        assert b1.__ne__(b2)
        
        assert b1.__ne__(data1) == NotImplemented
        assert b1.__eq__(data1) == NotImplemented
    def test_FactoryHandler(self):
        assert issubclass(FactoryHandler, JSONDataHandler)
        
        assert FactoryHandler.canhandle() == "json.JSONObjectFactory"
        assert FactoryHandler.encode("anything") == "anything"
        assert FactoryHandler.isinstance("anything") == False
        
        with unittest.mock.patch("gosa.common.components.jsonrpc_proxy.JSONObjectFactory") as jsonOF:
            pd = ProxyDummy()
            factory = pd()()
            assert jsonOF.get_instance.call_args_list == [unittest.mock.call(ProxyDummy.new_proxy, "json.FactoryHandler", {"object": "data"})]
        
        with pytest.raises(NotImplementedError):
            FactoryHandler.decode({"any": "thing"})

    @unittest.mock.patch.dict("gosa.common.components.jsonrpc_utils.json_handlers", {"datetime.date": DateTimeDateHandler}, clear=True)
    def test_PObjectEncoder(self):
        poe = PObjectEncoder()
        
        with unittest.mock.patch("sys.stdout", new=StringIO()) as stdoutMock:
            data = datetime.date(2016, 12, 12)
            poe.default(data) == DateTimeDateHandler.encode(data)
            
            data = "TESTING"
            with pytest.raises(TypeError):
                poe.default(data)
            assert stdoutMock.getvalue().strip() == "no TESTING <class 'str'>"
    @unittest.mock.patch.dict("gosa.common.components.jsonrpc_utils.json_handlers", {"datetime.date": DateTimeDateHandler}, clear=True)
    def test_PObjectDecoder(self):
        dt = datetime.date(2016, 12, 12)
        dct = {'object': str(dt), '__jsonclass__': "datetime.date"}
        assert dt == PObjectDecoder(dct)
        dct = {'object': str(dt), '__jsonclass__': ["datetime.date", "datetime.datetime"]}
        assert dt == PObjectDecoder(dct)
        with pytest.raises(NotImplementedError):
            dct = {'object': str(datetime.datetime(2016,12,12)), '__jsonclass__': ["datetime.datetime"]}
            PObjectDecoder(dct)
