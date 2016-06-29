#!/usr/bin/python3

import unittest, sys
from gosa.common.config import *
from io import TextIOWrapper, BytesIO

class ConfigTestCase(unittest.TestCase):
    def setUp(self):
        self._org_stdout = sys.stdout
    def checkStdOut(self, expected):
        # http://stackoverflow.com/a/12683001
        if not hasattr(sys.stdout, "getvalue"):
            self.fail("no buffer mode")
        self.assertEqual(sys.stdout.getvalue().strip(), expected)
    def test___parseCmdOptions(self):
        # Help message is not tested
        from gosa import __version__ as gosa_version
        #sys.argv.append("--version")
        #with TextIOWrapper(BytesIO(), sys.stdout.encoding, "rw") as sys.stdout:
            #with self.assertRaises(SystemExit):
                #config = Config()
        #sys.stdout = sys.__stdout__
        #print(sys.stdout)
        #self.checkStdOut(gosa_version)
        #del sys.argv[-1]
        
