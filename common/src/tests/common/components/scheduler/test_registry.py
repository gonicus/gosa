#!/usr/bin/python3

import unittest
from gosa.common.components.registry import *

class RegistryTestCase(unittest.TestCase):
    def test_PluginRegistry(self):
        
        pr = PluginRegistry()
        PluginRegistry.shutdown()
