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
from gosa.backend.objects.index import ObjectInfoIndex
from gosa.common.env import make_session


class LdapBackendTestCase(TestCase):

    def setUp(self):
        self.ldap = LDAP()
        with make_session() as session:
            res = session.query(ObjectInfoIndex.uuid).filter(ObjectInfoIndex.dn == "cn=Frank Reich,ou=people,dc=example,dc=net").one()
            self.user_uuid = res[0]

    def tearDown(self):
        del self.ldap

    def test_load(self):
        res = self.ldap.load(self.user_uuid, {'uid':'string','dateOfBirth':'string','uidNumber':'integer'})
        assert 'uid' in res
        assert 'dateOfBirth' in res
        assert 'uidNumber' in res
        assert res['uid'] == ['freich']
        assert res['uidNumber'] == [1001]
        assert res['dateOfBirth'] == ["1995-01-05"]

    def test_identify_by_uuid(self):
        assert self.ldap.identify_by_uuid(None, None) is False

    def test_exists(self):
        assert self.ldap.exists(self.user_uuid) is True
        assert self.ldap.exists('cn=Frank Reich,ou=people,dc=example,dc=net') is True
        assert self.ldap.exists('cn=Frank Reich,ou=people,dc=example,dc=de') is False

    def test_remove(self):
        with self.ldap.lh.get_handle() as con:
            with mock.patch.object(self.ldap.lh, 'get_handle') as m:
                m.return_value.__enter__.return_value.search_s = con.search_s
                self.ldap.remove(self.user_uuid, None, None)
                m.return_value.__enter__.return_value.delete_s.assert_called_with('cn=Frank Reich,ou=people,dc=example,dc=net')

    def test_retract(self):
        with self.ldap.lh.get_handle() as con:
            with mock.patch.object(self.ldap.lh, 'get_handle') as m,\
                 mock.patch.dict(self.ldap._LDAP__i_cache_ttl, {'cn=Frank Reich,ou=people,dc=example,dc=net': 'dummy'}),\
                 mock.patch.dict(self.ldap._LDAP__i_cache, {'cn=Frank Reich,ou=people,dc=example,dc=net': 'dummy'}):
                m.return_value.__enter__.return_value.search_s = con.search_s
                self.ldap.retract(self.user_uuid, {'gender':True}, {'objectClasses':'shadowAccount,sambaSamAccount'})
                assert m.return_value.__enter__.return_value.modify_s.called
                args, kwargs = m.return_value.__enter__.return_value.modify_s.call_args_list[0]
                assert args[0] == 'cn=Frank Reich,ou=people,dc=example,dc=net'
                assert (ldap.MOD_DELETE, 'objectClass', [b'shadowAccount', b'sambaSamAccount']) in args[1]
                assert (ldap.MOD_DELETE, 'gender', None) in args[1]
                assert 'cn=Frank Reich,ou=people,dc=example,dc=net' not in self.ldap._LDAP__i_cache_ttl
                assert 'cn=Frank Reich,ou=people,dc=example,dc=net' not in self.ldap._LDAP__i_cache

    def test_extend(self):
        with mock.patch.object(self.ldap, 'create') as m:
            self.ldap.extend(self.user_uuid,{'data':'test'},{'params':'test'},{'foreign_keys':'test'})
            m.assert_called_with('cn=Frank Reich,ou=people,dc=example,dc=net',{'data':'test'},{'params':'test'},{'foreign_keys':'test'})

    def test_move(self):
        with self.ldap.lh.get_handle() as con:
            with mock.patch.object(self.ldap.lh, 'get_handle') as m:
                m.return_value.__enter__.return_value.search_s = con.search_s
                self.ldap.move(self.user_uuid, 'ou=people,dc=test,dc=de')
                m.return_value.__enter__.return_value.rename_s.assert_called_with('cn=Frank Reich,ou=people,dc=example,dc=net','cn=Frank Reich', 'ou=people,dc=test,dc=de')

    def test_create(self):

        with pytest.raises(RDNNotSpecified):
            self.ldap.create('dc=example,dc.net',{'attr':{'value':['test'],'type':'string'}},{'objectClasses': 'top,person,organizationalPerson'})

        with mock.patch.object(self.ldap.lh, 'get_handle'), \
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
        with self.ldap.lh.get_handle() as con:
            with mock.patch.object(self.ldap.lh, 'get_handle') as m:
                m.return_value.__enter__.return_value.search_s = con.search_s
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
                args, kwargs = m.return_value.__enter__.return_value.add_s.call_args_list[0]
                assert 'cn=Test User,ou=people,dc=example,dc=net' == args[0]
                assert ('objectClass', [b'top', b'person', b'organizationalPerson']) in args[1]
                assert ('attr', [b'test']) in args[1]
                assert ('cn', [b'Test User']) in args[1]
                assert len(args[1]) == 3

            # with foreign keys
            with mock.patch.object(self.ldap.lh, 'get_handle') as m:
                m.return_value.__enter__.return_value.search_s = con.search_s
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
                args, kwargs = m.return_value.__enter__.return_value.modify_s.call_args_list[0]
                assert 'ou=people,dc=example,dc=net' == args[0]
                assert (ldap.MOD_ADD, 'objectClass', [b'top', b'person', b'organizationalPerson']) in args[1]
                assert (ldap.MOD_ADD, 'cn', [b'Test User']) in args[1]
                assert len(args[1]) == 2

    def test_update(self):
        with self.ldap.lh.get_handle() as con:
            with mock.patch.object(self.ldap.lh, 'get_handle') as m:
                m.return_value.__enter__.return_value.search_s = con.search_s
                self.ldap.update(self.user_uuid, {
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
                assert m.return_value.__enter__.return_value.modify_s.called
                args, kwargs = m.return_value.__enter__.return_value.modify_s.call_args_list[0]
                assert args[0] == 'cn=Frank Reich,ou=people,dc=example,dc=net'
                assert (ldap.MOD_DELETE, 'gender', None) in args[1]
                assert (ldap.MOD_ADD, 'attr', [b'new']) in args[1]
                assert (ldap.MOD_REPLACE, 'description', [b'changed']) in args[1]

                #with changed rdn part
                m.return_value.__enter__.return_value.modify_s.reset_mock()
                self.ldap.update(self.user_uuid, {
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
                        'value': ['Frank Möller'],
                        'orig': ['Frank Reich'],
                        'type': 'unicodestring'
                    }
                }, None)
                assert m.return_value.__enter__.return_value.rename_s.called
                args, kwargs = m.return_value.__enter__.return_value.rename_s.call_args_list[0]
                assert args[0] == 'cn=Frank Reich,ou=people,dc=example,dc=net'
                assert args[1] == 'cn=Frank Möller'

                assert m.return_value.__enter__.return_value.modify_s.called
                args, kwargs = m.return_value.__enter__.return_value.modify_s.call_args_list[0]
                assert args[0] == 'cn=Frank Möller,ou=people,dc=example,dc=net'
                assert (ldap.MOD_DELETE, 'gender', None) in args[1]
                assert (ldap.MOD_ADD, 'attr', [b'new']) in args[1]
                assert (ldap.MOD_REPLACE, 'description', [b'changed']) in args[1]
                assert (ldap.MOD_REPLACE, 'cn', [bytes('Frank Möller', 'utf-8')]) in args[1]

    def test_uuid2dn(self):
        assert self.ldap.dn2uuid('cn=Frank Reich,ou=people,dc=example,dc=net') == self.user_uuid
        assert self.ldap.dn2uuid('cn=Frank Reich,ou=people,dc=example,dc=de') is False

    def test_get_uniq_dn(self):
        assert self.ldap.get_uniq_dn(['cn'], 'ou=people,dc=example,dc=net', {
            'cn': {'value': ['Frank Reich']}
        }, None) is None
        assert self.ldap.get_uniq_dn(['cn'], 'ou=people,dc=example,dc=net', {
            'cn': {'value': ['Frank Möller']}
        }, None) == 'cn=Frank Möller,ou=people,dc=example,dc=net'

    def test_is_uniq(self):
        assert self.ldap.is_uniq('entryUUID',self.user_uuid,'string') is False
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

        with mock.patch.object(self.ldap.lh, 'get_handle') as m, \
                pytest.raises(EntryNotFound):
            m.return_value.__enter__.return_value.search_s.return_value = [['dn', {'uid': [1]}],['dn', {'uid': [1]}]]
            self.ldap.get_next_id('uid')

        # as there is currenty no example in the test-ldap we mock what we need
        with self.ldap.lh.get_handle() as con:
            with mock.patch.object(self.ldap.lh, 'get_handle') as m:
                m.return_value.__enter__.return_value.search_s.return_value = [['dn', {'uid': ["1"]}]]

                assert self.ldap.get_next_id('uid') == 1
                args, kwargs = m.return_value.__enter__.return_value.modify_s.call_args_list[0]
                assert args[0] == 'dn'
                assert (ldap.MOD_DELETE, 'uid', ["1"]) in args[1]
                assert (ldap.MOD_ADD, 'uid', [b"2"]) in args[1]
                assert len(args[1]) == 2

    def test__check_res(self):
        with pytest.raises(EntryNotFound):
            self.ldap._LDAP__check_res('uuid', None)

        with pytest.raises(EntryNotFound):
            self.ldap._LDAP__check_res('uuid', [1, 2])

    def test__delete_children(self):
        with self.ldap.lh.get_handle() as con:
            with mock.patch.object(self.ldap.lh, 'get_handle') as m:
                m_con = m.return_value.__enter__.return_value
                m_con.search_s = con.search_s
                self.ldap._LDAP__delete_children('ou=people,dc=example,dc=net')
                m_con.delete_s.assert_any_call('cn=Frank Reich,ou=people,dc=example,dc=net')
                m_con.delete_s.assert_any_call('cn=System Administrator,ou=people,dc=example,dc=net')

    def test_convert_from_boolean(self):
        assert self.ldap._convert_from_boolean("TRUE") is True
        assert self.ldap._convert_from_boolean("True") is False
        assert self.ldap._convert_from_boolean("FALSE") is False

    def test_convert_to_boolean(self):
        assert self.ldap._convert_to_boolean(True) == bytes("TRUE", "ascii")
        assert self.ldap._convert_to_boolean(False) == bytes("FALSE", "ascii")

    def test_convert_to_unicodestring(self):
        assert self.ldap._convert_to_unicodestring(1) == bytes("1", "utf-8")
        assert self.ldap._convert_to_unicodestring("foobar") == bytes("foobar", "utf-8")
        assert self.ldap._convert_to_unicodestring("möller") == bytes("möller", "utf-8")

    def test_convert_to_integer(self):
        assert self.ldap._convert_to_integer(1) == bytes("1", "ascii")

    def test_convert_from_integer(self):
        assert self.ldap._convert_from_integer("1") == 1

    def test_convert_from_date(self):
        date = datetime.date(2016, 1, 1)
        assert self.ldap._convert_from_date(b"20160101000000Z") == date

    def test_convert_to_date(self):
        date = datetime.date(2016, 1, 1)
        assert self.ldap._convert_to_date(date) == bytes("20160101000000Z", "ascii")

    def test_convert_to_timestamp(self):
        date = datetime.date(2016, 1, 1)
        assert self.ldap._convert_to_timestamp(date) == bytes("20160101000000Z", "ascii")

    def test_convert_from_binary(self):
        assert self.ldap._convert_from_binary("10") == Binary("10")

    def test_convert_to_binary(self):
        assert self.ldap._convert_to_binary(Binary("10")) == "10"
