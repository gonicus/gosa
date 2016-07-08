# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

import pytest
from unittest import mock
from tests.GosaTestCase import *
from gosa.backend.objects.index import *


class ObjectBackendTestCase(GosaTestCase):

    def setUp(self):
        super(ObjectBackendTestCase, self).setUp()
        self.obj = PluginRegistry.getInstance("ObjectIndex")

    # def test_insert(self):
    #     test = mock.MagicMock()
    #     test.uuid = '78475884-c7f2-1035-8262-f535be14d43a'
    #     test.asJSON.return_value = {'uuid': test.uuid}
    #     with pytest.raises(IndexException),\
    #             mock.patch.object(self.obj, "_ObjectIndex__save") as m:
    #         self.obj.insert(test)
    #         assert not m.called
    #
    #     with mock.patch.object(self.obj, "_ObjectIndex__save") as m:
    #         test.uuid = '78475884-c7f2-1035-8262-f535be14d43b'
    #         test.asJSON.return_value = {'uuid': test.uuid}
    #         self.obj.insert(test)
    #         m.assert_called_with({'uuid': '78475884-c7f2-1035-8262-f535be14d43b'})
    #
    # def test_remove(self):
    #     test = mock.MagicMock()
    #     test.uuid = '78475884-c7f2-1035-8262-f535be14d43a'
    #     with mock.patch.object(self.obj, "remove_by_uuid") as m:
    #         self.obj.remove(test)
    #         m.assert_called_with(test.uuid)
    #
    # def test_getBaseObjectTypes(self):
    #     res = self.obj.getBaseObjectTypes()
    #     assert 'User' in res
    #
    # def test_update(self):
    #     test = mock.MagicMock()
    #     test.uuid = '78475884-c7f2-1035-8262-f535be14d43b'
    #     test.asJSON.return_value = {
    #         'uuid': '78475884-c7f2-1035-8262-f535be14d43a',
    #         'dn': 'cn=Frank Reich,ou=people,dc=example,dc=de',
    #         'adjusted_parent_dn': 'ou=people,dc=example,dc=de'
    #     }
    #     with pytest.raises(IndexException):
    #         self.obj.update(test)
    #
    #     test.uuid = '7ff15c20-b305-1031-916b-47d262a62cc5'
    #     test.asJSON.return_value = {
    #         'uuid': '7ff15c20-b305-1031-916b-47d262a62cc5',
    #         'dn': 'ou=people,dc=example,dc=de',
    #         'adjusted_parent_dn': 'dc=example,dc=de'
    #     }
    #     with mock.patch.object(self.obj, "_ObjectIndex__save") as ms, \
    #             mock.patch.object(self.obj._ObjectIndex__session, "commit") as mc:
    #         self.obj.update(test)
    #         assert ms.called
    #         assert mc.called
    #
    # def test_find(self):
    #
    #     with pytest.raises(FilterException):
    #         self.obj.find('admin', 'query')
    #
    #     res = self.obj.find('admin', {'uuid': '78475884-c7f2-1035-8262-f535be14d43a'}, {'uid': 1})
    #     assert res[0]['dn'] == "cn=Frank Reich,ou=people,dc=example,dc=net"

    def test_search(self):

        # with mock.patch("gosa.backend.objects.index.GlobalLock.exists", return_value=True),\
        #         pytest.raises(FilterException):
        #     self.obj.search(None, None)
        #
        # with pytest.raises(Exception):
        #     self.obj.search({'unsupported_': {'uuid': '7ff15c20-b305-1031-916b-47d262a62cc5',
        #                                       'dn': 'cn=Frank Reich,ou=people,dc=example,dc=net'}}, {'dn': 1})
        #
        # res = self.obj.search({'or_': {'uuid': '7ff15c20-b305-1031-916b-47d262a62cc5',
        #                                'dn': 'cn=Frank Reich,ou=people,dc=example,dc=net'}}, {'dn': 1})
        #
        # assert len(res) == 2
        # assert 'cn=Frank Reich,ou=people,dc=example,dc=net' in [res[0]['dn'], res[1]['dn']]
        # assert 'ou=people,dc=example,dc=net' in [res[0]['dn'], res[1]['dn']]
        #
        # res = self.obj.search({'and_': {'uuid': '78475884-c7f2-1035-8262-f535be14d43a',
        #                                 'dn': 'cn=Frank Reich,ou=people,dc=example,dc=net'}}, {'dn': 1})
        # assert len(res) == 1
        # assert res[0]['dn'] == 'cn=Frank Reich,ou=people,dc=example,dc=net'
        #
        # res = self.obj.search({'dn': 'ou=people,dc=example,dc=net',
        #                        'not_': {'cn': 'Frank Reich'}}, {'dn': 1})
        # assert len(res) == 1
        # assert res[0]['dn'] == 'ou=people,dc=example,dc=net'
        #
        # res = self.obj.search({'dn': ['cn=Frank Reich,ou=people,dc=example,dc=net', 'cn=System Administrator%']}, {'dn': 1})
        # assert len(res) == 2
        # assert 'cn=Frank Reich,ou=people,dc=example,dc=net' in [res[0]['dn'], res[1]['dn']]
        # assert 'cn=System Administrator,ou=people,dc=example,dc=net' in [res[0]['dn'], res[1]['dn']]
        #
        # res = self.obj.search({'dn': ['%ou=people%'], 'extension': ['PosixUser']}, {'dn': 1})
        # assert len(res) == 3
        # dns = [res[0]['dn'], res[1]['dn'], res[2]['dn']]
        # assert 'ou=people,dc=example,dc=net' in dns
        # assert 'cn=Frank Reich,ou=people,dc=example,dc=net' in dns
        # assert 'cn=System Administrator,ou=people,dc=example,dc=net' in dns

        res = self.obj.search({'uid': ['freich']}, {'dn': 1, 'uid': 1})
        print(res)
        assert len(res) == 1
        assert 'cn=Frank Reich,ou=people,dc=example,dc=net' in res[0]['dn']
        #
        # res = self.obj.search({'uid': 'freich', 'extension': 'PosixUser'}, {'dn': 1})
        # assert len(res) == 1
        # assert 'cn=Frank Reich,ou=people,dc=example,dc=net' in res[0]['dn']
        #
        # res = self.obj.search({'dn': 'cn=Frank Reich,ou=people,dc=example,dc=net'}, {'dn': 1})
        # assert len(res) == 1
        # assert 'cn=Frank Reich,ou=people,dc=example,dc=net' in res[0]['dn']