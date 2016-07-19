import unittest
from gosa.backend.plugins.password.crypt_password import *

class PasswordMethodCryptTestCase(unittest.TestCase):

    def setUp(self):
        self.obj = PasswordMethodCrypt()

    def test_isLockable(self):
        assert self.obj.isLockable("") == False
        assert self.obj.isLockable("{CRYPT}uw8er0hjewofh") == True
        assert self.obj.isLockable("{CRYPT}!uw8er0hjewofh") == False

    def test_isUnlockable(self):
        assert self.obj.isUnlockable("") == False
        assert self.obj.isUnlockable("{CRYPT}uw8er0hjewofh") == False
        assert self.obj.isUnlockable("{CRYPT}!uw8er0hjewofh") == True

    def test_isLocked(self):
        assert self.obj.is_locked("{CRYPT}uw8er0hjewofh") == False
        assert self.obj.is_locked("{CRYPT}!uw8er0hjewofh") == True


    def test_is_responsible_for_password_hash(self):
        assert self.obj.is_responsible_for_password_hash("{CRYPT}uw8er0hjewofh") == True
        assert self.obj.is_responsible_for_password_hash("{UNKNOWN}uw8er0hjewofh") == False

    def test_detect_hash_method(self):
        assert self.obj.detect_hash_method("test") is None

        assert self.obj.detect_hash_method("{CRYPT}$0$md") is None

        pwd = self.obj.generate_password_hash("test", "MD5")
        assert self.obj.detect_hash_method(pwd) == "MD5"

        pwd = self.obj.generate_password_hash("test", "CRYPT")
        assert self.obj.detect_hash_method(pwd) == "CRYPT"

        pwd = self.obj.generate_password_hash("test", "SHA256")
        assert self.obj.detect_hash_method(pwd) == "SHA256"

        pwd = self.obj.generate_password_hash("test", "SHA512")
        assert self.obj.detect_hash_method(pwd) == "SHA512"

    def test_get_hash_names(self):
        # crypt method must be available on every system
        assert "CRYPT" in self.obj.get_hash_names()

    def test_lock_account(self):
        assert self.obj.lock_account("{CRYPT}uw8er0hjewofh") == "{CRYPT}!uw8er0hjewofh"
        assert self.obj.lock_account("{CRYPT}!uw8er0hjewofh") == "{CRYPT}!uw8er0hjewofh"

    def test_unlock_account(self):
        assert self.obj.unlock_account("{CRYPT}uw8er0hjewofh") == "{CRYPT}uw8er0hjewofh"
        assert self.obj.unlock_account("{CRYPT}!uw8er0hjewofh") == "{CRYPT}uw8er0hjewofh"
