#!/usr/bin/python3

import unittest
from gosa.common.components.command import *

class CommandTestCase(unittest.TestCase):
    @Command(__help__="TEST")
    def test_command(self):
        pass
    
    @Command()
    def test_command2(self):
        """Docs"""
        pass
    
    # agent and client terms still in use in command.py
