import unittest
import crypt
from gosa.backend.plugins.password.crypt_password import PasswordMethodCrypt
from gosa.backend.plugins.password.filter.detect_method import *

class DetectPasswordMethodTestCase(unittest.TestCase):

    def test_filter(self):
        filter = DetectPasswordMethod(None)
        testDict = {
            "userPassword":{
                "in_value": ["{CRYPT}$0$md"]
            },
            "attr": {
                "value": [None]
            }
        }

        pwdCrypt = PasswordMethodCrypt()

        # test all available methods
        for method in pwdCrypt.get_hash_names():
            testDict["userPassword"]["in_value"] = [pwdCrypt.generate_password_hash("test", method)]
            (new_key, newDict) = filter.process(None, "attr", testDict)
            assert list(newDict["attr"]["value"])[0] == method