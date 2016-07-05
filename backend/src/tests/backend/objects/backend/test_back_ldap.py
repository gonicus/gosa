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
from gosa.backend.objects.backend.back_ldap import *

class LdapBackendTestCase(unittest.TestCase):

    def setUp(self):
        self.ldap = LDAP()

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
        with unittest.mock.patch.object(self.ldap.con,'delete_s') as m:
            self.ldap.remove('78475884-c7f2-1035-8262-f535be14d43a', None, None)
            m.assert_called_with('cn=Frank Reich,ou=people,dc=example,dc=net')

    def test_retract(self):
        with unittest.mock.patch.object(self.ldap.con, 'modify_s') as m,\
             unittest.mock.patch.dict(self.ldap._LDAP__i_cache_ttl, {'cn=Frank Reich,ou=people,dc=example,dc=net': 'dummy'}),\
             unittest.mock.patch.dict(self.ldap._LDAP__i_cache, {'cn=Frank Reich,ou=people,dc=example,dc=net': 'dummy'}):
            self.ldap.retract('78475884-c7f2-1035-8262-f535be14d43a', {'gender':True}, {'objectClasses':'shadowAccount,sambaSamAccount'})
            assert m.called
            args, kwargs = m.call_args_list[0]
            assert args[0] == 'cn=Frank Reich,ou=people,dc=example,dc=net'
            assert (ldap.MOD_DELETE, 'objectClass', ['shadowAccount', 'sambaSamAccount']) in args[1]
            assert (ldap.MOD_DELETE, 'gender', None) in args[1]
            assert 'cn=Frank Reich,ou=people,dc=example,dc=net' not in self.ldap._LDAP__i_cache_ttl
            assert 'cn=Frank Reich,ou=people,dc=example,dc=net' not in self.ldap._LDAP__i_cache

    def test_extend(self):
        with unittest.mock.patch.object(self.ldap, 'create') as m:
            self.ldap.extend('78475884-c7f2-1035-8262-f535be14d43a',{'data':'test'},{'params':'test'},{'foreign_keys':'test'})
            m.assert_called_with('cn=Frank Reich,ou=people,dc=example,dc=net',{'data':'test'},{'params':'test'},{'foreign_keys':'test'})

    def test_move(self):
        with unittest.mock.patch.object(self.ldap.con, 'rename_s') as m:
            self.ldap.move('78475884-c7f2-1035-8262-f535be14d43a', 'ou=people,dc=test,dc=de')
            m.assert_called_with('cn=Frank Reich,ou=people,dc=example,dc=net','cn=Frank Reich', 'ou=people,dc=test,dc=de')


