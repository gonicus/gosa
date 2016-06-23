# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

import unittest
import pytest
from gosa.backend.plugins.samba.domain import *

class SambaGuiMethodsTestCase(unittest.TestCase):

    @unittest.mock.patch.object(Environment, "getInstance")
    @unittest.mock.patch.object(PluginRegistry, 'getInstance')
    def test_getSambaPassword(self, mockedRegistry, mockedEnv):

        # mockup ACL resolver
        MyResolver = type('MyResolver', (object,), {})
        resolver = MyResolver()
        def check(user, topic, flags, base):
            return True
        resolver.check = check
        mockedRegistry.return_value = resolver

        # mockup the environment
        mockedEnv.return_value.domain = "testdomain"

        with unittest.mock.patch('gosa.backend.plugins.samba.domain.ObjectProxy', autoSpec=True, create=True) as m:
            # run the test
            user = m.return_value
            methods = SambaGuiMethods()
            methods.setSambaPassword("username", "dn", "password")
            assert user.sambaNTPassword is not None
            assert user.sambaLMPassword is not None
            assert user.commit.called is True
            assert m.called is True

        # test with ACL.check for sambaNTPassword is False
        resolver = MyResolver()
        def check(user, topic, flags, base):
            return False
        resolver.check = check
        mockedRegistry.return_value = resolver

        with unittest.mock.patch('gosa.backend.plugins.samba.domain.ObjectProxy', autoSpec=True, create=True) as m:
            # run the test
            methods = SambaGuiMethods()
            with pytest.raises(ACLException):
                methods.setSambaPassword("username", "dn", "password")

        # test with ACL.check for sambaLMPassword is False
        resolver = MyResolver()
        def check(user, topic, flags, base):
            return not topic == "testdomain.objects.User.attributes.sambaLMPassword"
        resolver.check = check
        mockedRegistry.return_value = resolver

        with unittest.mock.patch('gosa.backend.plugins.samba.domain.ObjectProxy', autoSpec=True, create=True) as m:
            # run the test
            methods = SambaGuiMethods()
            with pytest.raises(ACLException):
                methods.setSambaPassword("username", "dn", "password")

    @unittest.mock.patch.object(PluginRegistry, 'getInstance')
    def test_getSambaDomainInformation(self, mockedInstance):
        # mock the whole lookup in the ObjectIndex to return True
        MyObject = type('MyObject', (object,), {})
        index = MyObject()
        def search(param1, param2):
            return unittest.mock.MagicMock(autoSpec=True, create=True)
        index.search = search
        mockedInstance.return_value = index

        methods = SambaGuiMethods()
        target = unittest.mock.MagicMock(autoSpec=True, create=True)
        res = methods.getSambaDomainInformation("username", target)
        # this is just a check that the method is callable so we do not really check the output here
        assert len(res) > 0


@unittest.mock.patch.object(PluginRegistry, 'getInstance')
def test_IsValidSambaDomainName(mockedInstance):
    # mock the whole lookup in the ObjectIndex to return True
    MyObject = type('MyObject', (object,), {})
    index = MyObject()
    def search(param1, param2):
        res = MyObject()
        res.count = lambda: True
        return res
    index.search = search

    mockedInstance.return_value = index

    check = IsValidSambaDomainName(None)

    (res, errors) = check.process(None, None, ["test"])
    assert res == True
    assert len(errors) == 0

    # mockup everything to return False
    index = MyObject()

    def search(param1, param2):
        res = MyObject()
        res.count = lambda: False
        return res

    index.search = search
    mockedInstance.return_value = index

    (res, errors) = check.process(None, None, ["test"])
    assert res == False
    assert len(errors) == 1