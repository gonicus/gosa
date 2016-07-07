# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

from unittest import mock
import pytest
from tests.GosaTestCase import GosaTestCase
from gosa.backend.objects.factory import *


class ObjectBackendTestCase(GosaTestCase):

    def setUp(self):
        self.obj = ObjectFactory()

    def tearDown(self):
        del self.obj

    def test_getAttributeTypes(self):
        res = self.obj.getAttributeTypes()
        # check if some type are available
        assert 'String' in res
        assert 'AnyType' in res
        assert 'Timestamp' in res
        assert 'Boolean' in res
        assert 'Binary' in res
        assert 'Integer' in res
        assert 'AclRole' in res
        assert 'AclSet' in res

    def test_getObjectBackendProperties(self):
        res = self.obj.getObjectBackendProperties('User')
        assert 'JSON' in res
        assert res['JSON']['type'] == 'User'
        assert 'LDAP' in res
        assert res['LDAP']['RDN'] == 'cn,uid'
        assert False