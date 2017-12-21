import unittest
from gosa.backend.objects.renderer.extensions import *


class ExtensionRendererTestCase(unittest.TestCase):

    def test_getName(self):
        name = ExtensionRenderer.getName()
        assert name == "extensions"

    def test_render(self):
        assert ExtensionRenderer.render({}) == ""
        assert ExtensionRenderer.render({
            "_extensions": ["ext1"],
            "dn": "dn"}) == "<a href='web+gosa://dn/ext1?edit'>ext1</a>"
