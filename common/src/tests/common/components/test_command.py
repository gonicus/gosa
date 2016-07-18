#!/usr/bin/python3

import unittest
from gosa.common.components.command import *

def add_help():
    def decorate(f):
        setattr(f, "__help__", "Help string")
        return f
    return decorate

class CommandTestCase(unittest.TestCase):
    def test_command(self):
        @Command()
        @add_help()
        def test():
            """Docstring\nInfo"""
            pass
        assert test.__doc__ == """.. command:: backend test

    Help string

.. note::
    **This method will be exported by the CommandRegistry.**

Docstring
Info"""
    
    def test_command2(self):
        @Command()
        def test():
            """Docstring\nInfo"""
            pass
        assert test.__doc__ == """.. command:: client test

    
Docstring
Info

..  note::
    **This method will be exported by the CommandRegistry.**

Docstring
Info"""
