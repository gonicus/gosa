#!/usr/bin/python3

import unittest
import pytest
from gosa.common.components.objects import *

class ObjectsTestCase(unittest.TestCase):
    def test_ObjectRegistry(self):
        # Agent term is used in code comment
        registry = ObjectRegistry.getInstance()
        obj = object()
        registry.register("object:identifier", obj)
        with pytest.raises(ValueError):
            registry.register("object:identifier", obj)
        assert {"object": obj, "signature": None} == registry.objects["object:identifier"]
