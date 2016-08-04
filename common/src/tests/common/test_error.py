#!/usr/bin/python3

import unittest, re, uuid
from gosa.common.error import *

class ExceptionsTestCase(unittest.TestCase):
    def parseGosaExceptionArgs(self, to_match):
        regex = re.compile("""\<(.*)\> (.*)""")
        m = regex.match(to_match)
        error_uuid = m.group(1)
        error_code = m.group(2)
        return error_uuid, error_code
    
    def test_make_error(self):
        err = GosaErrorHandler.make_error("NOT_IMPLEMENTED", method="test")
        self.parseGosaExceptionArgs(err)
        
        err = GosaErrorHandler.make_error("NO_SUCH_RESOURCE", topic="asdfg", resource="test")
        self.parseGosaExceptionArgs(err)
        
        
        # What behaviour is expected? Return same code or raise Exception?
        #if not "NOT_EXISTANT_ERROR_CODE1234" in GosaErrorHandler._codes:
            #self.assertRaises(KeyError, GosaErrorHandler.make_error, "NOT_EXISTANT_ERROR_CODE1234", resource="test")
        
        if not "TEST_ERROR" in GosaErrorHandler._codes:
            assert GosaErrorHandler.make_error("TEST_ERROR") == "TEST_ERROR"
            
            GosaErrorHandler.register_codes({"TEST_ERROR": N_("Message without further variables")})
        err = GosaErrorHandler.make_error("TEST_ERROR")
        self.parseGosaExceptionArgs(err)

    def test_GosaException(self):
        exc = GosaException("NO_SUCH_RESOURCE", resource="test")

    def test_getError(self):
        # Method does not use the user parameter
        
        # Test locale flag
        error_uuid, error_code = self.parseGosaExceptionArgs(
            GosaException("NO_SUCH_RESOURCE",
                resource="test", 
                details=[{"detail": "not known"}, {"detail": "unknown"}]
            ).args[0])
        error_handler = GosaErrorHandler()
        got_error = error_handler.getError(None, error_uuid, locale="en_EN.UTF-8")
        assert got_error["text"] == error_code
        
        # Test trace flag
        error_uuid, error_code = self.parseGosaExceptionArgs(
            GosaException("NO_SUCH_RESOURCE",
                resource="test", 
                details=[{"detail": "not known"}, {"detail": "unknown"}]
            ).args[0])
        error_handler = GosaErrorHandler()
        got_error = error_handler.getError(None, error_uuid, trace=True)
        assert got_error["text"] == error_code
