# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

import pytest
import crypt
from unittest import mock
from gosa.backend.components.jsonrpc_objects import JSONRPCObjectMapper, ObjectRegistry
from gosa.common.components import PluginRegistry
from tests.GosaTestCase import GosaTestCase

def getPlugin(name):
    if name == "ACLResolver":
        mockedResolver = mock.MagicMock()
        mockedResolver.return_value.check.return_value = True
        return mockedResolver
    else:
        return

class JSONRPCObjectMapperTestCase(GosaTestCase):

    def setUp(self):
        super(JSONRPCObjectMapperTestCase, self).setUp()
        self.mapper = JSONRPCObjectMapper()

    def test_listObjectOIDs(self):
        res = self.mapper.listObjectOIDs()
        assert 'object' in res
        assert len(res) == 1

    def test_openObject(self):
        res = self.mapper.openObject('admin','object','dc=example,dc=net')
        assert res['dc'] == "example"

        with pytest.raises(Exception):
            self.mapper.openObject('admin', 'object', 'dc=example,dc=net')


    def test_closeObject(self):
        res = self.mapper.openObject('admin', 'object', 'dc=example,dc=net')

        with pytest.raises(ValueError):
            self.mapper.closeObject('admin','unknown')

        with pytest.raises(ValueError):
            self.mapper.closeObject('someone else', res["__jsonclass__"][1][1])

        self.mapper.closeObject('admin', res["__jsonclass__"][1][1])

        # as a workaround for checking if its not loaded anymore we try to reload it
        with pytest.raises(ValueError):
            self.mapper.reloadObject('admin', res["__jsonclass__"][1][1])


    def test_getObjectProperty(self):
        res = self.mapper.openObject('admin', 'object', 'dc=example,dc=net')
        ref = res["__jsonclass__"][1][1]

        with pytest.raises(ValueError):
            self.mapper.getObjectProperty('admin', 'unknown', 'prop')

        with pytest.raises(ValueError):
            self.mapper.getObjectProperty('admin', ref, 'prop')

        with pytest.raises(ValueError):
            self.mapper.getObjectProperty('someone else', ref, 'description')

        assert self.mapper.getObjectProperty('admin', ref, 'description') == "Example"


    def test_setObjectProperty(self):
        res = self.mapper.openObject('admin', 'object', 'dc=example,dc=net')
        ref = res["__jsonclass__"][1][1]

        with pytest.raises(ValueError):
            self.mapper.setObjectProperty('admin', 'unknown', 'prop', 'val')

        with pytest.raises(ValueError):
            self.mapper.setObjectProperty('admin', ref, 'prop', 'val')

        with pytest.raises(ValueError):
            self.mapper.setObjectProperty('someone else', ref, 'description', 'val')

        self.mapper.setObjectProperty('admin', ref, 'description', 'val')
        assert self.mapper.getObjectProperty('admin', ref, 'description') == "val"

        #undo
        self.mapper.setObjectProperty('admin', ref, 'description', 'Example')
        assert self.mapper.getObjectProperty('admin', ref, 'description') == "Example"

    def test_reloadObjectProperty(self):
        res = self.mapper.openObject('admin', 'object', 'dc=example,dc=net')
        uuid = res['uuid']
        ref = res["__jsonclass__"][1][1]

        with pytest.raises(ValueError):
            self.mapper.reloadObject('someone else', ref)

        res = self.mapper.reloadObject('admin', ref)
        assert uuid == res['uuid']
        assert ref != res["__jsonclass__"][1][1]

    def test_dispatchObjectMethod(self):
        res = self.mapper.openObject('admin', 'object', 'cn=Frank Reich,ou=people,dc=example,dc=net')
        ref = res["__jsonclass__"][1][1]

        with pytest.raises(ValueError):
            self.mapper.dispatchObjectMethod('admin','wrong_ref','lock')

        with pytest.raises(ValueError):
            self.mapper.dispatchObjectMethod('admin', ref, 'wrong_method')

        with pytest.raises(ValueError):
            self.mapper.dispatchObjectMethod('someone_else', ref, 'lock')

        # mock a method in the object
        mockedResolver = mock.MagicMock()
        mockedResolver.return_value.check.return_value = True
        with mock.patch.dict(PluginRegistry.modules, {'ACLResolver': mockedResolver}), mock.patch('gosa.backend.plugins.password.manager.ObjectProxy') as m:
            user = m.return_value
            user.passwordMethod = crypt.METHOD_MD5
            self.mapper.dispatchObjectMethod('admin', ref, 'changePassword','Test')
            assert user.userPassword
            assert user.commit.called

    def test_diffObject(self):
        assert self.mapper.diffObject('admin','unkown_ref') is None

        res = self.mapper.openObject('admin', 'object', 'dc=example,dc=net')
        ref = res["__jsonclass__"][1][1]

        with pytest.raises(ValueError):
            self.mapper.diffObject('someone_else', ref)

        self.mapper.setObjectProperty('admin', ref, 'description', 'val')
        delta = self.mapper.diffObject('admin', ref)
        assert 'description' in delta['attributes']['changed']


    def test_removeObject(self):
        res = self.mapper.openObject('admin', 'object', 'cn=Frank Reich,ou=people,dc=example,dc=net')
        ref = res["__jsonclass__"][1][1]

        with pytest.raises(Exception):
            self.mapper.removeObject('admin','object', 'cn=Frank Reich,ou=people,dc=example,dc=net')

        self.mapper.closeObject('admin', ref)

        with mock.patch.dict(ObjectRegistry.objects['object'], {'object': mock.MagicMock()}):
            mockedObject = ObjectRegistry.objects['object']['object'].return_value
            self.mapper.removeObject('admin', 'object', 'cn=Frank Reich,ou=people,dc=example,dc=net')
            assert mockedObject.remove.called
