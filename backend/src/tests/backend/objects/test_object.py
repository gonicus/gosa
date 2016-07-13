# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

import pytest
from unittest import mock, TestCase

from gosa.backend.objects import ObjectFactory
from tests.GosaTestCase import *
from gosa.backend.objects.object import *


#@slow
class ObjectTestCase(GosaTestCase):

    def test_listProperties(self):
        obj = ObjectFactory.getInstance().getObject('User', '78475884-c7f2-1035-8262-f535be14d43a')
        res = obj.listProperties()
        # just test if something is there
        assert 'uid' in res
        assert 'gender' in res

    def test_getProperties(self):
        obj = ObjectFactory.getInstance().getObject('User', '78475884-c7f2-1035-8262-f535be14d43a')
        res = obj.getProperties()
        # just test if something is there
        assert res['uid']['value'][0] == "freich"

    def test_listMethods(self):
        obj = ObjectFactory.getInstance().getObject('User', '78475884-c7f2-1035-8262-f535be14d43a')
        res = obj.listMethods()
        # just test if something is there
        assert 'lock' in res
        assert 'unlock' in res

    def test_listMethods(self):
        obj = ObjectFactory.getInstance().getObject('User', '78475884-c7f2-1035-8262-f535be14d43a')
        res = obj.listMethods()
        # just test if something is there
        assert obj.hasattr('uid') is True
        assert obj.hasattr('gender') is True

    def test_getTemplate(self):
        obj = ObjectFactory.getInstance().getObject('User', '78475884-c7f2-1035-8262-f535be14d43a')
        res = obj.getTemplate()
        assert res[0][0:3] == "<ui"

    def test_getNamedTemplate(self):
        assert Object.getNamedTemplate({}, []) == []

        obj = ObjectFactory.getInstance().getObject('User', '78475884-c7f2-1035-8262-f535be14d43a')
        res = Object.getNamedTemplate(obj.env, obj._templates)
        assert res[0][0:3] == "<ui"

        with mock.patch('os.path.exists', return_value=False):
            assert Object.getNamedTemplate(obj.env, obj._templates) is None

    def test_getAttrType(self):
        obj = ObjectFactory.getInstance().getObject('User', '78475884-c7f2-1035-8262-f535be14d43a')
        assert obj.getAttrType('uid') == "String"

        with pytest.raises(AttributeError):
            obj.getAttrType('unknown')

    def test_attributes(self):
        obj = ObjectFactory.getInstance().getObject('User', '78475884-c7f2-1035-8262-f535be14d43a')
        assert obj.gender == 'M'

        # just test the change
        obj.gender = 'F'
        assert obj.gender == 'F'

        # cannot delete mandatory attribute
        with pytest.raises(AttributeError):
            del obj.uid
        # cannot delete readonly attribute
        with pytest.raises(AttributeError):
            del obj.passwordMethod
        # cannot delete blockedBy attribute
        with pytest.raises(AttributeError):
            del obj.displayName
        # cannot delete unknown attribute
        with pytest.raises(AttributeError):
            del obj.unknown
        # cannot get unknown attribute
        with pytest.raises(AttributeError):
            obj.unknown

        del obj.gender
        assert obj.gender is None

        # try to set some wrong types
        with pytest.raises(TypeError):
            obj.gender = True
        with pytest.raises(TypeError):
            obj.gender = "T"

        obj.gender = 'M'
        assert obj.gender == 'M'

        # delete by setting None
        obj.gender = None
        assert obj.gender is None

        # cannot change readonly attribute
        with pytest.raises(AttributeError):
            obj.passwordMethod = 'MD5'
        # cannot change blockedBy attribute
        with pytest.raises(AttributeError):
            obj.displayName = "Name"
        # cannot change unknown attribute
        with pytest.raises(AttributeError):
            obj.unknown = "Test"
        # multivalue (no list)
        with pytest.raises(TypeError):
            obj.mail = "test@tester.de"
        # validation error
        with pytest.raises(ValueError):
            obj.telephoneNumber = ["wrong"]

    def test_check(self):
        # wrong mode for base object
        obj = ObjectFactory.getInstance().getObject('User', '78475884-c7f2-1035-8262-f535be14d43a', 'delete')
        with pytest.raises(ObjectException):
            obj.check()

        # remove a non base object
        obj = ObjectFactory.getInstance().getObject('PosixUser', '78475884-c7f2-1035-8262-f535be14d43a', 'remove')
        with pytest.raises(ObjectException):
            obj.check()

        # update base object
        obj = ObjectFactory.getInstance().getObject('User', '78475884-c7f2-1035-8262-f535be14d43a')
        res = obj.check()
        # just test if something is there
        assert 'uid' in res
        assert 'gender' in res

        # create new object with wrong dn
        obj = ObjectFactory.getInstance().getObject('User', 'cn=Test User,ou=people,dc=example,dc=net', 'create')
        with pytest.raises(ObjectException):
            obj.check()

        # create new SambaDomain object with base dn for User
        obj = ObjectFactory.getInstance().getObject('SambaDomain', 'ou=people,dc=example,dc=net', 'create')
        with pytest.raises(ObjectException):
            obj.check()

        # create new user object, missing mandatory attributes
        obj = ObjectFactory.getInstance().getObject('User', 'ou=people,dc=example,dc=net', 'create')
        with pytest.raises(ObjectException):
            obj.check()

        # add mandatory values
        obj.givenName = "Test"
        obj.sn = "User"
        obj.uid = "tuser"

        res = obj.check()
        assert 'uid' in res
        assert res['uid']['value'][0] == "tuser"

    def test_revert(self):
        obj = ObjectFactory.getInstance().getObject('User', '78475884-c7f2-1035-8262-f535be14d43a')
        obj.uid = 'frank'
        obj.revert()
        assert obj.uid == 'freich'

    def test_getExclusiveProperties(self):
        obj = ObjectFactory.getInstance().getObject('PosixUser', '78475884-c7f2-1035-8262-f535be14d43a')
        res = obj.getExclusiveProperties()
        assert 'uid' not in res
        assert 'groupMembership' in res

    def test_getForeignProperties(self):
        obj = ObjectFactory.getInstance().getObject('PosixUser', '78475884-c7f2-1035-8262-f535be14d43a')
        res = obj.getForeignProperties()
        assert 'uid' in res
        assert 'groupMembership' not in res

    def test_object_type_by_dn(self):
        obj = ObjectFactory.getInstance().getObject('User', '78475884-c7f2-1035-8262-f535be14d43a')
        assert obj.get_object_type_by_dn("ou=people,dc=example,dc=net") == "PeopleContainer"
        assert obj.get_object_type_by_dn("ou=people,dc=example,dc=de") is None

    def test_get_references(self):
        obj = ObjectFactory.getInstance().getObject('PosixUser', '78475884-c7f2-1035-8262-f535be14d43a')
        res = obj.get_references()
        assert res[0] == ('memberUid', 'uid', 'freich', [], False)




