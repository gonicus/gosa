# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

from unittest import mock,TestCase
import pytest
from gosa.backend.objects.backend.back_ldap import *

class LdapBackendTestCase(TestCase):

    def setUp(self):
        self.ldap = LDAP()

    def tearDown(self):
        del self.ldap

    def test_load(self):
        res = self.ldap.load('78475884-c7f2-1035-8262-f535be14d43a', {'uid':'string','dateOfBirth':'string','uidNumber':'integer'})
        assert 'uid' in res
        assert 'dateOfBirth' in res
        assert 'uidNumber' in res
        assert res['uid'] == ['freich']
        assert res['uidNumber'] == [1001]
        assert res['dateOfBirth'] == ["1995-01-05"]

    def test_identify_by_uuid(self):
        assert self.ldap.identify_by_uuid(None, None) is False

    def test_exists(self):
        assert self.ldap.exists('78475884-c7f2-1035-8262-f535be14d43a') is True
        assert self.ldap.exists('cn=Frank Reich,ou=people,dc=example,dc=net') is True
        assert self.ldap.exists('cn=Frank Reich,ou=people,dc=example,dc=de') is False

    def test_remove(self):
        with mock.patch.object(self.ldap.con,'delete_s') as m:
            self.ldap.remove('78475884-c7f2-1035-8262-f535be14d43a', None, None)
            m.assert_called_with('cn=Frank Reich,ou=people,dc=example,dc=net')

    def test_retract(self):
        with mock.patch.object(self.ldap.con, 'modify_s') as m,\
             mock.patch.dict(self.ldap._LDAP__i_cache_ttl, {'cn=Frank Reich,ou=people,dc=example,dc=net': 'dummy'}),\
             mock.patch.dict(self.ldap._LDAP__i_cache, {'cn=Frank Reich,ou=people,dc=example,dc=net': 'dummy'}):
            self.ldap.retract('78475884-c7f2-1035-8262-f535be14d43a', {'gender':True}, {'objectClasses':'shadowAccount,sambaSamAccount'})
            assert m.called
            args, kwargs = m.call_args_list[0]
            assert args[0] == 'cn=Frank Reich,ou=people,dc=example,dc=net'
            assert (ldap.MOD_DELETE, 'objectClass', ['shadowAccount', 'sambaSamAccount']) in args[1]
            assert (ldap.MOD_DELETE, 'gender', None) in args[1]
            assert 'cn=Frank Reich,ou=people,dc=example,dc=net' not in self.ldap._LDAP__i_cache_ttl
            assert 'cn=Frank Reich,ou=people,dc=example,dc=net' not in self.ldap._LDAP__i_cache

    def test_extend(self):
        with mock.patch.object(self.ldap, 'create') as m:
            self.ldap.extend('78475884-c7f2-1035-8262-f535be14d43a',{'data':'test'},{'params':'test'},{'foreign_keys':'test'})
            m.assert_called_with('cn=Frank Reich,ou=people,dc=example,dc=net',{'data':'test'},{'params':'test'},{'foreign_keys':'test'})

    def test_move(self):
        with mock.patch.object(self.ldap.con, 'rename_s') as m:
            self.ldap.move('78475884-c7f2-1035-8262-f535be14d43a', 'ou=people,dc=test,dc=de')
            m.assert_called_with('cn=Frank Reich,ou=people,dc=example,dc=net','cn=Frank Reich', 'ou=people,dc=test,dc=de')

    def test_create(self):
        with pytest.raises(RDNNotSpecified):
            self.ldap.create('dc=example,dc.net',{'attr':{'value':['test'],'type':'string'}},{'objectClasses': 'top,person,organizationalPerson'})

        with mock.patch.object(self.ldap.con, 'modify_s'), \
                mock.patch.object(self.ldap.con, 'add_s'), \
                mock.patch.object(self.ldap, 'get_uniq_dn', return_value=None),\
                pytest.raises(DNGeneratorError):
            self.ldap.create('ou=people,dc=example,dc=de', {
                'attr': {
                    'value': ['test'],
                    'type': 'string'
                },
                'cn': {
                    'value': ['Test User'],
                    'type': 'string'
                }
            }, {
                'objectClasses': 'top,person,organizationalPerson',
                'RDN': 'cn'
            })

        with mock.patch.object(self.ldap.con, 'modify_s'),\
                mock.patch.object(self.ldap.con, 'add_s') as ma:
            self.ldap.create('ou=people,dc=example,dc=net', {
                'attr': {
                    'value': ['test'],
                    'type': 'string'
                },
                'cn': {
                    'value': ['Test User'],
                    'type': 'string'
                }
            }, {
                'objectClasses': 'top,person,organizationalPerson',
                'RDN': 'cn'
            })
            args, kwargs = ma.call_args_list[0]
            assert 'cn=Test User,ou=people,dc=example,dc=net' == args[0]
            assert ('objectClass', ['top', 'person', 'organizationalPerson']) in args[1]
            assert ('attr', ['test']) in args[1]
            assert ('cn', ['Test User']) in args[1]
            assert len(args[1]) == 3

        # with foreign keys
        with mock.patch.object(self.ldap.con, 'modify_s') as mm, \
                mock.patch.object(self.ldap.con, 'add_s'):
            self.ldap.create('ou=people,dc=example,dc=net', {
                'attr': {
                    'value': ['test'],
                    'type': 'string'
                },
                'cn': {
                    'value': ['Test User'],
                    'type': 'string'
                }
            }, {
                'objectClasses': 'top,person,organizationalPerson',
                'RDN': 'cn'
            }, ['attr'])
            args, kwargs = mm.call_args_list[0]
            assert 'ou=people,dc=example,dc=net' == args[0]
            assert (ldap.MOD_ADD, 'objectClass', ['top', 'person', 'organizationalPerson']) in args[1]
            assert (ldap.MOD_ADD, 'cn', ['Test User']) in args[1]
            assert len(args[1]) == 2

    def test_update(self):

        with mock.patch.object(self.ldap.con, 'modify_s') as mm, \
                mock.patch.object(self.ldap.con, 'rename_s') as mr:
            self.ldap.update('78475884-c7f2-1035-8262-f535be14d43a', {
                'attr': {
                    'value': ['new'],
                    'orig': None,
                    'type': 'string'
                },
                'description': {
                    'value': ['changed'],
                    'orig': ['Example'],
                    'type': 'String'
                },
                'gender': {
                    'orig': ['M'],
                    'value': None,
                    'type': 'string'
                }
            }, None)
            assert mm.called
            args, kwargs = mm.call_args_list[0]
            assert args[0] == 'cn=Frank Reich,ou=people,dc=example,dc=net'
            assert (ldap.MOD_DELETE, 'gender', None) in args[1]
            assert (ldap.MOD_ADD, 'attr', ['new']) in args[1]
            assert (ldap.MOD_REPLACE, 'description', ['changed']) in args[1]

            #with changed rdn part
            mm.reset_mock()
            self.ldap.update('78475884-c7f2-1035-8262-f535be14d43a', {
                'attr': {
                    'value': ['new'],
                    'orig': None,
                    'type': 'string'
                },
                'description': {
                    'value': ['changed'],
                    'orig': ['Example'],
                    'type': 'String'
                },
                'gender': {
                    'orig': ['M'],
                    'value': None,
                    'type': 'string'
                },
                'cn': {
                    'value': ['Frank Reich-Ranitzki'],
                    'orig': ['Frank Reich'],
                    'type': 'string'
                }
            }, None)
            assert mr.called
            args, kwargs = mr.call_args_list[0]
            assert args[0] == 'cn=Frank Reich,ou=people,dc=example,dc=net'
            assert args[1] == 'cn=Frank Reich-Ranitzki'

            assert mm.called
            args, kwargs = mm.call_args_list[0]
            assert args[0] == 'cn=Frank Reich-Ranitzki,ou=people,dc=example,dc=net'
            assert (ldap.MOD_DELETE, 'gender', None) in args[1]
            assert (ldap.MOD_ADD, 'attr', ['new']) in args[1]
            assert (ldap.MOD_REPLACE, 'description', ['changed']) in args[1]
            assert (ldap.MOD_REPLACE, 'cn', ['Frank Reich-Ranitzki']) in args[1]

    def test_uuid2dn(self):
        assert self.ldap.dn2uuid('cn=Frank Reich,ou=people,dc=example,dc=net') == '78475884-c7f2-1035-8262-f535be14d43a'
        assert self.ldap.dn2uuid('cn=Frank Reich,ou=people,dc=example,dc=de') is False

    def test_get_uniq_dn(self):
        assert self.ldap.get_uniq_dn(['cn'], 'ou=people,dc=example,dc=net', {
            'cn': {'value': ['Frank Reich']}
        }, None) is None
        assert self.ldap.get_uniq_dn(['cn'], 'ou=people,dc=example,dc=net', {
            'cn': {'value': ['Frank Reich-Ranitzki']}
        }, None) == 'cn=Frank Reich-Ranitzki,ou=people,dc=example,dc=net'

    def test_is_uniq(self):
        assert self.ldap.is_uniq('entryUUID','78475884-c7f2-1035-8262-f535be14d43a','string') is False
        assert self.ldap.is_uniq('entryUUID','78475884-c7f2-1035-8262-f535be14d43b','string') is True

    def test_build_dn_list(self):
        res = self.ldap.build_dn_list(['cn','ou'],'dc=example,dc=net', {
            'cn': {
                'value': ['Frank Reich'],
                'type': 'string'
            },
            'ou': {
                'value': ['people'],
                'type': 'string'
            }
        }, None)

        assert 'cn=Frank Reich,dc=example,dc=net' in res
        assert 'cn=Frank Reich+ou=people,dc=example,dc=net' in res
        assert len(res) == 2

        res = self.ldap.build_dn_list(['cn','ou'],'dc=example,dc=net', {
            'cn': {
                'value': ['Frank Reich'],
                'type': 'string'
            },
            'ou': {
                'value': ['people'],
                'type': 'string'
            }
        }, 'cn=Frank Reich,ou=people')
        assert 'cn=Frank Reich,ou=people,dc=example,dc=net' in res
        assert len(res) == 1

        with pytest.raises(DNGeneratorError):
            self.ldap.build_dn_list(['cn','ou'],'dc=example,dc=net', {
                'ou': {
                    'value': ['people'],
                    'type': 'string'
                }
            }, None)

    def test_get_next_id(self):
        with pytest.raises(EntryNotFound):
            self.ldap.get_next_id('uid')

        with mock.patch.object(self.ldap.con, 'search_s') as ms, \
                pytest.raises(EntryNotFound):
            ms.return_value = [['dn', {'uid': [1]}],['dn', {'uid': [1]}]]
            self.ldap.get_next_id('uid')

        # as there is currenty no example in the test-ldap we mock what we need
        with mock.patch.object(self.ldap.con, 'modify_s') as mm,\
                mock.patch.object(self.ldap.con, 'search_s') as ms:
            ms.return_value = [['dn', {'uid': ["1"]}]]

            assert self.ldap.get_next_id('uid') == 2
            args, kwargs = mm.call_args_list[0]
            assert args[0] == 'dn'
            assert (ldap.MOD_DELETE, 'uid', ["1"]) in args[1]
            assert (ldap.MOD_ADD, 'uid', ["2"]) in args[1]
            assert len(args[1]) == 2

    def test__check_res(self):
        with pytest.raises(EntryNotFound):
            self.ldap._LDAP__check_res('uuid', None)

        with pytest.raises(EntryNotFound):
            self.ldap._LDAP__check_res('uuid', [1, 2])

    def test__delete_children(self):
        with mock.patch.object(self.ldap.con, 'delete_s') as m:
            self.ldap._LDAP__delete_children('ou=people,dc=example,dc=net')
            m.assert_called_with('cn=Frank Reich,ou=people,dc=example,dc=net')

    def test_convert_from_boolean(self):
        assert self.ldap._convert_from_boolean("TRUE") is True
        assert self.ldap._convert_from_boolean("True") is False
        assert self.ldap._convert_from_boolean("FALSE") is False

    def test_convert_to_boolean(self):
        assert self.ldap._convert_to_boolean(True) == "TRUE"
        assert self.ldap._convert_to_boolean(False) == "FALSE"

    def test_convert_to_unicodestring(self):
        assert self.ldap._convert_to_unicodestring(1) == "1"
        assert self.ldap._convert_to_unicodestring("test") == "test"

    def test_convert_to_integer(self):
        assert self.ldap._convert_to_integer(1) == "1"

    def test_convert_from_integer(self):
        assert self.ldap._convert_from_integer("1") == 1

    def test_convert_from_date(self):
        date = datetime.date(2016, 1, 1)
        assert self.ldap._convert_from_date(b"20160101000000Z") == date

    def test_convert_to_date(self):
        date = datetime.date(2016, 1, 1)
        assert self.ldap._convert_to_date(date) == "20160101000000Z"

    def test_convert_to_timestamp(self):
        date = datetime.date(2016, 1, 1)
        assert self.ldap._convert_to_timestamp(date) == "20160101000000Z"

    def test_convert_from_binary(self):
        assert self.ldap._convert_from_binary("10") == Binary("10")

    def test_convert_to_binary(self):
        assert self.ldap._convert_to_binary(Binary("10")) == "10"
