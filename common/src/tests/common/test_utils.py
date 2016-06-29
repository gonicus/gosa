#!/usr/bin/python3

import unittest
import re
from gosa.common.utils import *
import xml.etree.ElementTree as ET

class CommonUtilsTestCase(unittest.TestCase):
    def test_stripNs(self):
        # Required xml scheme unknown. Following won't work.
        full_xml = """<?xml version="1.0"?><a><p>TESTING</p></a>"""
        expected = """
            <xml xmlns="http://example.com/xmlns">
                <p>TESTING</p>
            </xml>
        """
        
        return True
        self.assertEqual(stripNs(full_xml), expected)
    
    def test_makeAuthURL(self):
        url = "https://hostname.org:1234/example"
        username = "peter"
        password = "secret"
        
        expected = "https://peter:secret@hostname.org:1234/example"
        
        self.assertEqual(makeAuthURL(url, username, password), expected)
    
    def test_parseURL(self):
        url = ""
        self.assertEqual(parseURL(url), None)
        
        url = """https://peter:secret@hostname.org/example/test"""
        expected = {"source": url,
            "scheme": "https",
            "user": "peter",
            "password": "secret",
            "host": "hostname.org",
            "port": 443,
            "path": "example/test",
            "transport": "tcp+ssl",
            "url": "https://peter:secret@hostname.org:443/example/test"
            }
        self.assertEqual(parseURL(url), expected)
        
        return True
        # Does the implementation need to handle urls without extra information at all?
        # Right now it can't.
        url = """http://hostname.org"""
        expected = {"source": url,
            "scheme": "http",
            "user": None,
            "password": None,
            "host": "hostname.org",
            "port": 80,
            "path": "rpc",
            "transport": "tcp",
            "url": "http://hostname.org"
            }
        self.assertEqual(parseURL(url), expected)
        
        
        url = """https://hostname.org:1234"""
        expected = {"source": url,
            "scheme": "https",
            "user": None,
            "password": None,
            "host": "hostname.org",
            "port": 1234,
            "path": "rpc",
            "transport": "tcp+ssl",
            "url": "https://hostname.org:1234"
            }
        self.assertEqual(parseURL(url), expected)
    
    def test_N_(self):
        self.assertEqual(N_("Not yet translated"), "Not yet translated")
    
    def test_is_uuid(self):
        import uuid
        self.assertFalse(is_uuid("".join([str(x) for x in range(36)])))
        self.assertFalse(is_uuid("-".join([str(x) for x in range(36)])))
        self.assertFalse(is_uuid("anything"))
        for i in range(1000):
            self.assertTrue(is_uuid(str(uuid.uuid1())))
            self.assertTrue(is_uuid(str(uuid.uuid4())))
    
    def test_get_timezone_delta(self):
        delta = get_timezone_delta()
        self.assertRegex(delta, """([-+])(\d+):(\d+)$""")
    
    def test_locate(self):
        # Strict unit test not possible without further investigation
        # on system (which would be the same as "locate" does anyway).
        # Testing some most likely conditions.
        import os
        here = os.path.dirname(os.path.realpath(__file__))
        
        exe = "notexistanttool"
        self.assertEqual(locate(exe), None)
        exe = "cp"
        self.assertEqual(locate(exe), "/bin/cp")
        exe = "python"
        self.assertIn(locate(exe), ("/usr/bin/python", os.path.expandvars("$VIRTUAL_ENV/bin/python")))
        
        exe = "/usr/bin/notexistanttool"
        self.assertEqual(locate(exe), None)
        exe = "/bin/cp"
        self.assertEqual(locate(exe), "/bin/cp")
        
        exe = "/bin"
        self.assertEqual(locate(exe), None)
        
        # Untested condition: There is a not executable file given.
        # Is there any ordinary file that is present on any unix/linux system?
        
    def test_f_print(self):
        # f_print only works if data is a string or an iterable longer than 1 (indexes 0 and 1).
        
        # Following implementation would be more idiomatic and robust:
        # def f_print(basestr, *values):
        #     return basestr % values
        data = "Testing"
        self.assertEqual(f_print(data), "Testing")
        
        data = ("A %s string with %s.", "short", "variables")
        self.assertEqual(f_print(data), "A short string with variables.")
        
        data = ("A %s string with %s.", "short", "too", "many", "variables")
        self.assertRaises(TypeError, f_print, data)
        
        data = ("A %s string with %s %s.", "long", "variables")
        self.assertRaises(TypeError, f_print, data)
    
    # Unused
    def test_repr2json(self):
        # ???
        
        obj = {"err": ReferenceError(), "list": [12.00, 12, "12"]}
        print(obj.__repr__())
        print(repr2json(obj.__repr__()))
        print(repr2json("""{"json": 2}"""))
        
        # Impementation does not handle tuples correctly: 
        # As there are no tuples in JSON, these may be turned to lists.
    
    # Unused
    def test_downloadFile(self):
        pass
    
    # Unused
    def test_xml2dict(self):
        pass
