import unittest
import crypt
from gosa.backend.plugins.password.manager import *

class PasswordMethodCryptTestCase(unittest.TestCase):

    def setUp(self):
        self.obj = PasswordManager()

    def test_listPasswordMethods(self):
        res = self.obj.listPasswordMethods()

        # the hash methods from the crypt module must be available
        for method in crypt.methods:
            assert method in res

    def test_detect_method_by_hash(self):
        assert self.obj.detect_method_by_hash("{UNKNOWN}$0$md") is None

        methods = self.obj.list_methods()
        for method in methods:
            pwd = methods[method].generate_password_hash("test", method)
            assert self.obj.detect_method_by_hash(pwd) == methods[method]

    def test_get_method_by_method_type(self):
        assert self.obj.get_method_by_method_type("Unknown") is None

        methods = self.obj.list_methods()
        for method in methods:
            assert self.obj.get_method_by_method_type(method) == methods[method]