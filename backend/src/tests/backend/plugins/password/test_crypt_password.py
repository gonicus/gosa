import unittest
from gosa.backend.plugins.password.crypt_password import *

class PasswordMethodCryptTestCase(unittest.TestCase):

    def setUp(self):
        self.obj = PasswordMethodCrypt()

    def test_isLockable(self):
        assert self.obj.isLockable("") == False
        assert self.obj.isLockable(b"{CRYPT}uw8er0hjewofh") == True
        assert self.obj.isLockable(b"{CRYPT}!uw8er0hjewofh") == False

    def test_isUnlockable(self):
        assert self.obj.isUnlockable("") == False
        assert self.obj.isUnlockable(b"{CRYPT}uw8er0hjewofh") == False
        assert self.obj.isUnlockable(b"{CRYPT}!uw8er0hjewofh") == True

    def test_isLocked(self):
        assert self.obj.is_locked(b"{CRYPT}uw8er0hjewofh") == False
        assert self.obj.is_locked(b"{CRYPT}!uw8er0hjewofh") == True


    def test_is_responsible_for_password_hash(self):
        assert self.obj.is_responsible_for_password_hash(b"{CRYPT}uw8er0hjewofh") == True
        assert self.obj.is_responsible_for_password_hash(b"{UNKNOWN}uw8er0hjewofh") == False

    def test_detect_hash_method(self):
        assert self.obj.detect_hash_method(b"test") is None

        assert self.obj.detect_hash_method(b"{CRYPT}$0$md") is None

        pwd = self.obj.generate_password_hash("test",crypt.METHOD_MD5)
        assert self.obj.detect_hash_method(pwd) == crypt.METHOD_MD5

        pwd = self.obj.generate_password_hash("test", crypt.METHOD_CRYPT)
        assert self.obj.detect_hash_method(pwd) == crypt.METHOD_CRYPT

        pwd = self.obj.generate_password_hash("test", crypt.METHOD_SHA256)
        assert self.obj.detect_hash_method(pwd) == crypt.METHOD_SHA256

        pwd = self.obj.generate_password_hash("test", crypt.METHOD_SHA512)
        assert self.obj.detect_hash_method(pwd) == crypt.METHOD_SHA512

    def test_get_hash_names(self):
        # crypt method must be available on every system
        assert crypt.METHOD_CRYPT in self.obj.get_hash_names()

    def test_lock_account(self):
        assert self.obj.lock_account(b"{CRYPT}uw8er0hjewofh") == "{CRYPT}!uw8er0hjewofh"
        assert self.obj.lock_account(b"{CRYPT}!uw8er0hjewofh") == "{CRYPT}!uw8er0hjewofh"

    def test_unlock_account(self):
        assert self.obj.unlock_account(b"{CRYPT}uw8er0hjewofh") == "{CRYPT}uw8er0hjewofh"
        assert self.obj.unlock_account(b"{CRYPT}!uw8er0hjewofh") == "{CRYPT}uw8er0hjewofh"