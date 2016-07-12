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
        assert res[0][0:3] == b"<ui"

    def test_getNamedTemplate(self):
        assert Object.getNamedTemplate({}, []) == []

        obj = ObjectFactory.getInstance().getObject('User', '78475884-c7f2-1035-8262-f535be14d43a')
        res = Object.getNamedTemplate(obj.env, obj._templates)
        assert res[0][0:3] == b"<ui"

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
        obj = ObjectFactory.getInstance().getObject('User', '78475884-c7f2-1035-8262-f535be14d43a')
        res = obj.check()

        # just test if something is there
        assert 'uid' in res
        assert 'gender' in res

