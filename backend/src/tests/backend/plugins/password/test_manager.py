# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

import unittest
import crypt
import pytest
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

    @unittest.mock.patch.object(Environment, "getInstance")
    @unittest.mock.patch.object(PluginRegistry, 'getInstance')
    def test_lockAccountPassword(self, mockedResolver, mockedEnv):
        # mockup ACL resolver
        mockedResolver.return_value.check.return_value = False

        # mockup the environment
        mockedEnv.return_value.domain = "testdomain"

        with pytest.raises(ACLException):
            self.obj.lockAccountPassword("Test", "dn")

        mockedResolver.return_value.check.return_value = True

        with unittest.mock.patch('gosa.backend.plugins.password.manager.ObjectProxy', autoSpec=True, create=True) as m:
            # run the test
            user = m.return_value
            with pytest.raises(PasswordException):
                self.obj.lockAccountPassword("Test", "dn")
            user.userPassword = None
            user.get_attributes.return_value = ['userPassword']
            with pytest.raises(PasswordException):
                self.obj.lockAccountPassword("Test", "dn")
            user.userPassword = "{UNKNOWN}$0$md"
            with pytest.raises(PasswordException):
                self.obj.lockAccountPassword("Test", "dn")
            user.userPassword = "{CRYPT}uw8er0hjewofh"
            self.obj.lockAccountPassword("Test", "dn")
            # account should be locked
            assert user.userPassword == "{CRYPT}!uw8er0hjewofh"
            assert user.commit.called is True

    @unittest.mock.patch.object(Environment, "getInstance")
    @unittest.mock.patch.object(PluginRegistry, 'getInstance')
    def test_unlockAccountPassword(self, mockedResolver, mockedEnv):
        # mockup ACL resolver
        mockedResolver.return_value.check.return_value = False

        # mockup the environment
        mockedEnv.return_value.domain = "testdomain"

        with pytest.raises(ACLException):
            self.obj.unlockAccountPassword("Test", "dn")

        mockedResolver.return_value.check.return_value = True

        with unittest.mock.patch('gosa.backend.plugins.password.manager.ObjectProxy', autoSpec=True, create=True) as m:
            # run the test
            user = m.return_value
            with pytest.raises(PasswordException):
                self.obj.unlockAccountPassword("Test", "dn")
            user.userPassword = None
            user.get_attributes.return_value = ['userPassword']
            with pytest.raises(PasswordException):
                self.obj.unlockAccountPassword("Test", "dn")
            user.userPassword = "{UNKNOWN}$0$md"
            with pytest.raises(PasswordException):
                self.obj.unlockAccountPassword("Test", "dn")
            user.userPassword = "{CRYPT}!uw8er0hjewofh"
            self.obj.unlockAccountPassword("Test", "dn")
            # account should be locked
            assert user.userPassword == "{CRYPT}uw8er0hjewofh"
            assert user.commit.called is True

    @unittest.mock.patch.object(Environment, "getInstance")
    @unittest.mock.patch.object(PluginRegistry, 'getInstance')
    def test_accountLockable(self, mockedRegistry, mockedEnv):
        # mockup ACL resolver
        resolver = unittest.mock.MagicMock(autoSpec=True, create=True)
        resolver.check.side_effect = [False, True, True, True]

        index = unittest.mock.MagicMock()
        found = unittest.mock.MagicMock()
        index.search.return_value = found

        def sideEffect(key):
            if key == "ObjectIndex":
                return index
            elif key == "ACLResolver":
                return resolver

        mockedRegistry.return_value.check.return_value = False
        mockedRegistry.side_effect = sideEffect

        # mockup the environment
        mockedEnv.return_value.domain = "testdomain"

        # mockup the found user
        found.__getitem__.return_value = {
            "userPassword": ["{UNKNOWN}uw8er0hjewofh"]
        }

        with pytest.raises(ACLException):
            self.obj.accountLockable("Test", "dn")

        found.count.return_value = 0
        assert self.obj.accountLockable("Test","dn") is False

        found.count.return_value = 1
        assert self.obj.accountLockable("Test", "dn") is False

        found.__getitem__.return_value = {
            "userPassword": ["{CRYPT}uw8er0hjewofh"]
        }
        assert self.obj.accountLockable("Test", "dn") is True

    @unittest.mock.patch.object(Environment, "getInstance")
    @unittest.mock.patch.object(PluginRegistry, 'getInstance')
    def test_accountUnlockable(self, mockedRegistry, mockedEnv):
        # mockup ACL resolver
        resolver = unittest.mock.MagicMock()
        resolver.check.side_effect = [False, True, True, True]

        index = unittest.mock.MagicMock()
        found = unittest.mock.MagicMock()
        index.search.return_value = found

        def sideEffect(key):
            if key == "ObjectIndex":
                return index
            elif key == "ACLResolver":
                return resolver

        mockedRegistry.side_effect = sideEffect

        # mockup the environment
        mockedEnv.return_value.domain = "testdomain"

        # mockup the found user
        found.__getitem__.return_value = {
            "userPassword": ["{UNKNOWN}uw8er0hjewofh"]
        }

        with pytest.raises(ACLException):
            self.obj.accountUnlockable("Test", "dn")

        found.count.return_value = 0
        assert self.obj.accountUnlockable("Test", "dn") is False

        found.count.return_value = 1
        assert self.obj.accountUnlockable("Test", "dn") is False

        found.__getitem__.return_value = {
            "userPassword": ["{CRYPT}!uw8er0hjewofh"]
        }
        assert self.obj.accountUnlockable("Test", "dn") is True

    @unittest.mock.patch.object(Environment, "getInstance")
    @unittest.mock.patch.object(PluginRegistry, 'getInstance')
    def test_setUserPasswordMethod(self, mockedRegistry, mockedEnv):
        # mockup ACL resolver
        resolver = unittest.mock.MagicMock(autoSpec=True, create=True)
        resolver.check.side_effect = [False, True, True]
        mockedRegistry.return_value = resolver

        # mockup the environment
        mockedEnv.return_value.domain = "testdomain"


        with pytest.raises(ACLException):
            self.obj.setUserPasswordMethod("Test", "dn", crypt.METHOD_MD5, "pwd")

        with pytest.raises(PasswordException):
            self.obj.setUserPasswordMethod("Test", "dn", "UNKNOWN", "pwd")

        with unittest.mock.patch('gosa.backend.plugins.password.manager.ObjectProxy', autoSpec=True, create=True) as m:
            # run the test
            user = m.return_value
            self.obj.setUserPasswordMethod("Test", "dn", crypt.METHOD_MD5, "pwd")
            assert user.userPassword
            assert user.commit.called

    @unittest.mock.patch.object(Environment, "getInstance")
    @unittest.mock.patch.object(PluginRegistry, 'getInstance')
    def test_setUserPassword(self, mockedRegistry, mockedEnv):
        # mockup ACL resolver
        resolver = unittest.mock.MagicMock(autoSpec=True, create=True)
        resolver.check.side_effect = [False, True, True]
        mockedRegistry.return_value = resolver

        # mockup the environment
        mockedEnv.return_value.domain = "testdomain"

        with pytest.raises(ACLException):
            self.obj.setUserPassword("Test", "dn", "pwd")

        with unittest.mock.patch('gosa.backend.plugins.password.manager.ObjectProxy', autoSpec=True, create=True) as m:
            # run the test
            user = m.return_value
            user.passwordMethod = "UNKOWN"

            with pytest.raises(PasswordException):
                self.obj.setUserPassword("Test", "dn", "pwd")

            user.passwordMethod = crypt.METHOD_MD5
            self.obj.setUserPassword("Test", "dn", "pwd")
            assert user.userPassword
            assert user.commit.called