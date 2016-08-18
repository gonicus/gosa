# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

from unittest import mock, TestCase
from gosa.backend.objects import ObjectFactory
from tests.GosaTestCase import *
from gosa.backend.objects.object import *


@slow
class ObjectTestCase(TestCase):

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

    def test_update_refs(self):
        object = ObjectFactory.getInstance().getObject('User', '78475884-c7f2-1035-8262-f535be14d43a')
        with mock.patch.object(object, "get_references",
                               return_value=[('memberUid', 'uid', 'freich',
                                             ['78475884-c7f2-1035-8262-f535be14d43a'], False)]) as m, \
             mock.patch.object(object, "_delattr_"), \
             mock.patch("gosa.backend.objects.object.ObjectProxy") as c_obj:

            c_obj.return_value.memberUid = 'Test'
            c_obj.return_value.sn = 'Test'
            object.update_refs({'sn': {'value': ['Tester'], 'orig': ['Reich']}})
            assert c_obj.return_value.sn == 'Test'

            object.update_refs({'uid': {'value': ['frank'], 'orig': ['freich']}})
            assert c_obj.return_value.memberUid == 'frank'

            c_obj.return_value.memberUid = ['Test']
            object.update_refs({'uid': {'value': ['frank'], 'orig': ['freich']}})
            assert 'Test' in c_obj.return_value.memberUid
            assert 'frank' in c_obj.return_value.memberUid

            c_obj.return_value.memberUid = ['Test']
            object.update_refs({'uid': {'value': ['frank'], 'orig': 'freich'}})
            assert 'Test' in c_obj.return_value.memberUid
            assert 'frank' in c_obj.return_value.memberUid

            # multivalue
            m.return_value = [('memberUid', 'uid', 'freich',
                               ['78475884-c7f2-1035-8262-f535be14d43a'], True)]
            c_obj.return_value.memberUid = ['Test']
            object.update_refs({'uid': {'value': ['frank', 'more'], 'orig': ['freich']}})
            assert 'Test' in c_obj.return_value.memberUid
            assert 'frank' in c_obj.return_value.memberUid
            assert 'more' in c_obj.return_value.memberUid

    def test_remove_refs(self):
        object = ObjectFactory.getInstance().getObject('User', '78475884-c7f2-1035-8262-f535be14d43a')
        with mock.patch.object(object, "get_references",
                               return_value=[('memberUid', 'uid', 'freich',
                                              ['78475884-c7f2-1035-8262-f535be14d43a'], False)]) as m, \
                mock.patch.object(object, "_delattr_"), \
                mock.patch("gosa.backend.objects.object.ObjectProxy") as c_obj:
            c_obj.return_value.memberUid = 'Test'
            object.remove_refs()
            assert c_obj.return_value.memberUid is None
            assert c_obj.return_value.commit.called

            c_obj.return_value.memberUid = ['Test', 'freich']
            object.remove_refs()
            assert c_obj.return_value.memberUid == ['Test']

            m.return_value = [('memberUid', 'uid', ['freich'],
                               ['78475884-c7f2-1035-8262-f535be14d43a'], True)]
            c_obj.return_value.memberUid = ['Test', 'freich']
            object.remove_refs()
            assert c_obj.return_value.memberUid == ['Test']

    def test_get_dn_references(self):
        object = ObjectFactory.getInstance().getObject('User', '78475884-c7f2-1035-8262-f535be14d43a')
        res = object.get_dn_references()
        assert len(res) == 1
        assert 'member' in res[0]

        mocked_index = mock.MagicMock()
        mocked_index.search.return_value = [{'dn': b'dn1'}, {'dn': b'dn2'}]
        with mock.patch.dict(PluginRegistry.modules, {'ObjectIndex': mocked_index}):
            res = object.get_dn_references()
            assert len(res) == 1
            assert 'member' in res[0]
            assert 'dn1' in res[0][1]
            assert 'dn2' in res[0][1]

    def test_update_dn_refs(self):
        object = ObjectFactory.getInstance().getObject('User', '78475884-c7f2-1035-8262-f535be14d43a')
        with mock.patch.object(object, "get_dn_references",
                               return_value=[('member', ['78475884-c7f2-1035-8262-f535be14d43a'])]) as m, \
                mock.patch.object(object, "_delattr_"), \
                mock.patch("gosa.backend.objects.object.ObjectProxy") as c_obj:

            c_obj.return_value.member = 'old dn'
            object.update_dn_refs('new dn')
            assert c_obj.return_value.member == 'new dn'

            c_obj.return_value.member = ['old dn']
            object.update_dn_refs('new dn')
            assert 'new dn' in c_obj.return_value.member
            assert 'old dn' in c_obj.return_value.member

            assert c_obj.return_value.commit.called

    def test_remove_dn_refs(self):
        object = ObjectFactory.getInstance().getObject('User', '78475884-c7f2-1035-8262-f535be14d43a')
        with mock.patch.object(object, "get_dn_references",
                               return_value=[('member', ['78475884-c7f2-1035-8262-f535be14d43a'])]) as m, \
                mock.patch.object(object, "_delattr_"), \
                mock.patch("gosa.backend.objects.object.ObjectProxy") as c_obj:

            c_obj.return_value.member = 'old dn'
            object.remove_dn_refs()
            assert c_obj.return_value.member is None

            c_obj.return_value.member = ['old dn', object.dn]
            object.remove_dn_refs()
            assert c_obj.return_value.member == ['old dn']

            c_obj.return_value.member = [object.dn]
            object.remove_dn_refs()
            assert c_obj.return_value.member == []

            assert c_obj.return_value.commit.called

    def test_remove(self):
        object = ObjectFactory.getInstance().getObject('PosixUser', '78475884-c7f2-1035-8262-f535be14d43a')

        with pytest.raises(ObjectException):
            object.remove()

        object = ObjectFactory.getInstance().getObject('User', '78475884-c7f2-1035-8262-f535be14d43a')

        with mock.patch("gosa.backend.objects.object.ObjectBackendRegistry.getBackend") as mb, \
            mock.patch("zope.event.notify") as me:
            object.remove()

            assert mb.return_value.remove.called
            assert me.called

    def test_simulate_move(self):
        object = ObjectFactory.getInstance().getObject('PosixUser', '78475884-c7f2-1035-8262-f535be14d43a')

        with pytest.raises(ObjectException):
            object.simulate_move('orig_dn')

        object = ObjectFactory.getInstance().getObject('User', '78475884-c7f2-1035-8262-f535be14d43a')
        with mock.patch("zope.event.notify") as me, \
                mock.patch.object(object, "get_dn_references",
                                  return_value=[('member', ['78475884-c7f2-1035-8262-f535be14d43a'])]), \
                mock.patch.object(object, "_delattr_"), \
                mock.patch("gosa.backend.objects.object.ObjectProxy") as c_obj:

            c_obj.return_value.member = 'old dn'
            object.simulate_move('orig_dn')

            assert me.called
            assert c_obj.return_value.member == object.dn

    def test_move(self):
        object = ObjectFactory.getInstance().getObject('PosixUser', '78475884-c7f2-1035-8262-f535be14d43a')

        with pytest.raises(ObjectException):
            object.move('orig_dn')

        object = ObjectFactory.getInstance().getObject('User', '78475884-c7f2-1035-8262-f535be14d43a')
        with mock.patch("zope.event.notify") as me, \
                mock.patch.object(object, "get_dn_references",
                                  return_value=[('member', ['78475884-c7f2-1035-8262-f535be14d43a'])]), \
                mock.patch.object(object, "_delattr_"), \
                mock.patch("gosa.backend.objects.object.ObjectBackendRegistry.getBackend") as mb, \
                mock.patch("gosa.backend.objects.object.ObjectProxy") as c_obj:
            mb.return_value.uuid2dn.return_value = 'new dn'
            c_obj.return_value.member = 'old dn'
            object.move('new base')

            assert me.called
            mb.return_value.move.assert_called_with(object.uuid, 'new base')
            assert c_obj.return_value.member == 'new dn'

    def test_retract(self):
        object = ObjectFactory.getInstance().getObject('User', '78475884-c7f2-1035-8262-f535be14d43a')

        with pytest.raises(ObjectException):
            object.retract()

        object = ObjectFactory.getInstance().getObject('PosixUser', '78475884-c7f2-1035-8262-f535be14d43a')
        with mock.patch("zope.event.notify") as me, \
                mock.patch.object(object, "remove_dn_refs") as mdn, \
                mock.patch.object(object, "remove_refs") as mrem, \
                mock.patch.object(object, "_delattr_"), \
                mock.patch("gosa.backend.objects.object.ObjectBackendRegistry.getBackend") as mb, \
                mock.patch("gosa.backend.objects.object.ObjectProxy") as c_obj:

            object.retract()

            assert me.called
            assert mdn.called
            assert mrem.called
            assert mb.return_value.retract.called

    def test_is_attr_set(self):
        object = ObjectFactory.getInstance().getObject('User', '78475884-c7f2-1035-8262-f535be14d43a')
        assert object.is_attr_set('uid') is True
        assert object.is_attr_set('pager') is False

    def test_is_attr_using_default(self):
        object = ObjectFactory.getInstance().getObject('User', '78475884-c7f2-1035-8262-f535be14d43a')
        assert object.is_attr_using_default('uid') is False
        assert object.is_attr_using_default('autoDisplayName') is True

    def test_commit(self):
        object = ObjectFactory.getInstance().getObject('PosixUser', '78475884-c7f2-1035-8262-f535be14d43a')
        with mock.patch("gosa.backend.objects.object.ObjectBackendRegistry.getBackend") as mb, \
                mock.patch("zope.event.notify") as me:

            object.homePhone = '023456'
            object.autoIDs = False
            object.uidNumber = 999

            res = object.commit()
            assert mb.return_value.update.called
            assert me.called

            assert res['homePhone']['value'][0] == '023456'
            assert res['uidNumber']['value'][0] == 999
