import unittest
from gosa.backend.objects.renderer.extensions import *


class ExtensionRendererTestCase(unittest.TestCase):

    def test_getName(self):
        name = ExtensionRenderer.getName()
        assert name == "extensions"

    def test_render(self):
        assert ExtensionRenderer.render({}) == ""
        assert ExtensionRenderer.render({
            "Extension":["ext1"],
            "DN": ["dn"]}) == "Extensions: <a href='gosa://dn/ext1?edit'>ext1</a>"
