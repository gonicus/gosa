# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

from unittest import mock, TestCase

from gosa.common.components import ObjectRegistry
from tests.GosaTestCase import *
from gosa.backend.objects.index import *


@slow
class ObjectIndexTestCase(TestCase):

    def setUp(self):
        super(ObjectIndexTestCase, self).setUp()
        self.obj = PluginRegistry.getInstance("ObjectIndex")

    def test_insert(self):
        test = mock.MagicMock()
        test.get_parent_dn.return_value = "dc=example,dc=net"
        test.uuid = '78475884-c7f2-1035-8262-f535be14d43a'
        test.asJSON.return_value = {'uuid': test.uuid}

        with mock.patch.object(self.obj, "_ObjectIndex__save") as m_save,\
                mock.patch.object(self.obj, "_get_object") as m_get_object:
            m_get_object.return_value.can_host.return_value = True
            with pytest.raises(IndexException):
                self.obj.insert(test)
                assert not m_save.called

            test.uuid = 'new-uuid'
            test.asJSON.return_value = {'uuid': test.uuid}
            self.obj.insert(test)
            m_save.assert_called_with({'uuid': 'new-uuid'})

    def test_remove(self):
        test = mock.MagicMock()
        test.uuid = '78475884-c7f2-1035-8262-f535be14d43a'
        with mock.patch.object(self.obj, "remove_by_uuid") as m:
            self.obj.remove(test)
            m.assert_called_with(test.uuid)

    def test_getBaseObjectTypes(self):
        res = self.obj.getBaseObjectTypes()
        assert 'User' in res

    def test_update(self):
        test = mock.MagicMock()
        test.uuid = '78475884-c7f2-1035-8262-f535be14d43b'
        test.asJSON.return_value = {
            'uuid': '78475884-c7f2-1035-8262-f535be14d43a',
            'dn': 'cn=Frank Reich,ou=people,dc=example,dc=de',
            '_adjusted_parent_dn': 'ou=people,dc=example,dc=de'
        }

        with mock.patch.object(self.obj, "_ObjectIndex__save") as ms, \
                mock.patch.object(self.obj._ObjectIndex__session, "commit") as mc,\
                mock.patch.object(self.obj, "remove_by_uuid") as mr:
            with pytest.raises(IndexException):
                self.obj.update(test)
            assert not ms.called
            assert not mc.called
            assert not mr.called

            test.uuid = '7ff15c20-b305-1031-916b-47d262a62cc5'
            test.asJSON.return_value = {
                'uuid': '7ff15c20-b305-1031-916b-47d262a62cc5',
                'dn': 'ou=people,dc=example,dc=de',
                '_adjusted_parent_dn': 'dc=example,dc=de'
            }

            self.obj.update(test)
            assert ms.called
            assert mc.called
            mr.assert_called_with(test.uuid)

        # ObjectIndex needs to be rebuild after this test
        PluginRegistry.getInstance('HTTPService').srv.stop()
        PluginRegistry.shutdown()

        oreg = ObjectRegistry.getInstance()  # @UnusedVariable
        pr = PluginRegistry()  # @UnusedVariable
        cr = PluginRegistry.getInstance("CommandRegistry") # @UnusedVariable

    def test_find(self):

        with pytest.raises(FilterException):
            self.obj.find('admin', 'query')

        res = self.obj.find('admin', {'uuid': '78475884-c7f2-1035-8262-f535be14d43a'}, {'uid': 1})
        assert res[0]['dn'] == "cn=Frank Reich,ou=people,dc=example,dc=net"

    def test_search(self):

        with pytest.raises(Exception):
            self.obj.search({'unsupported_': {'uuid': '7ff15c20-b305-1031-916b-47d262a62cc5',
                                              'dn': 'cn=Frank Reich,ou=people,dc=example,dc=net'}}, {'dn': 1})

        res = self.obj.search({'or_': {'uuid': '7ff15c20-b305-1031-916b-47d262a62cc5',
                                       'dn': 'cn=Frank Reich,ou=people,dc=example,dc=net'}}, {'dn': 1})

        assert len(res) == 2
        assert 'cn=Frank Reich,ou=people,dc=example,dc=net' in [res[0]['dn'], res[1]['dn']]
        assert 'ou=people,dc=example,dc=net' in [res[0]['dn'], res[1]['dn']]

        res = self.obj.search({'and_': {'uuid': '78475884-c7f2-1035-8262-f535be14d43a',
                                        'dn': 'cn=Frank Reich,ou=people,dc=example,dc=net'}}, {'dn': 1})
        assert len(res) == 1
        assert res[0]['dn'] == 'cn=Frank Reich,ou=people,dc=example,dc=net'

        res = self.obj.search({'_parent_dn': 'ou=people,dc=example,dc=net',
                               'not_': {'dn': 'cn=Frank Reich,ou=people,dc=example,dc=net'}}, {'dn': 1})
        assert len(res) == 1
        assert res[0]['dn'] == 'cn=System Administrator,ou=people,dc=example,dc=net'

        res = self.obj.search({'dn': ['cn=Frank Reich,ou=people,dc=example,dc=net', 'cn=System Administrator%']}, {'dn': 1})
        assert len(res) == 2
        assert 'cn=Frank Reich,ou=people,dc=example,dc=net' in [res[0]['dn'], res[1]['dn']]
        assert 'cn=System Administrator,ou=people,dc=example,dc=net' in [res[0]['dn'], res[1]['dn']]

        res = self.obj.search({'_parent_dn': ['ou=people,dc=example,dc=net'], 'extension': ['PosixUser']}, {'dn': 1})
        assert len(res) == 1
        assert res[0]['dn'] == 'cn=Frank Reich,ou=people,dc=example,dc=net'

        res = self.obj.search({'uid': ['freich']}, {'dn': 1, 'uid': 1})
        assert len(res) == 1
        assert 'cn=Frank Reich,ou=people,dc=example,dc=net' in res[0]['dn']

        res = self.obj.search({'uid': ['freich%']}, {'dn': 1, 'uid': 1})
        assert len(res) == 1
        assert 'cn=Frank Reich,ou=people,dc=example,dc=net' in res[0]['dn']

        res = self.obj.search({'uid': 'freich', 'extension': 'PosixUser'}, {'dn': 1})
        assert len(res) == 1
        assert 'cn=Frank Reich,ou=people,dc=example,dc=net' in res[0]['dn']

        res = self.obj.search({'uid': 'freich%'}, {'dn': 1})
        assert len(res) == 1
        assert 'cn=Frank Reich,ou=people,dc=example,dc=net' in res[0]['dn']

        res = self.obj.search({'dn': 'cn=Frank Reich,ou=people,dc=example,dc=net'}, {'dn': 1})
        assert len(res) == 1
        assert 'cn=Frank Reich,ou=people,dc=example,dc=net' in res[0]['dn']

        res = self.obj.search({'dn': 'cn=Frank Reich,ou=people%'}, {'dn': 1})
        assert len(res) == 1
        assert 'cn=Frank Reich,ou=people,dc=example,dc=net' in res[0]['dn']