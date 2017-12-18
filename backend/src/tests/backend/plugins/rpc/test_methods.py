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
from gosa.backend.plugins.rpc.methods import GOsaException
import gosa
from gosa.common.env import make_session
from gosa.common.gjson import loads
from tests.GosaTestCase import slow


@slow
class RpcMethodsTestCase(TestCase):

    def setUp(self):
        super(RpcMethodsTestCase, self).setUp()
        self.rpc = gosa.common.components.PluginRegistry.getInstance("RPCMethods")

    def tearDown(self):
        del self.rpc
        super(RpcMethodsTestCase, self).tearDown()

    def test_getAvailableObjectNames(self):
        res = self.rpc.getAvailableObjectNames()
        assert len(res) > 0
        assert 'Domain' in res
        assert 'SambaUser' in res

    def test_getGuiTemplates(self):

        with pytest.raises(GOsaException):
            self.rpc.getGuiTemplates('UnknownType')

        res = self.rpc.getGuiTemplates('User')
        assert len(res) == 2

    def test_getGuiDialogs(self):

        with pytest.raises(GOsaException):
            self.rpc.getGuiDialogs('UnknownType')

        res = self.rpc.getGuiDialogs('SambaUser')
        assert len(res) == 3


    def test_getTemplateI18N(self):

        res = self.rpc.getTemplateI18N('de')
        assert res['User'] == 'Benutzer'
        assert res['Title'] == 'Titel'

    def test_getUserDetails(self):

        with pytest.raises(GOsaException):
            self.rpc.getUserDetails('unknown')

        res = self.rpc.getUserDetails('admin')
        assert res['sn'] == 'Administrator'
        assert res['givenName'] == 'System'
        assert res['dn'] == 'cn=System Administrator,ou=people,dc=example,dc=net'
        assert res['uuid'] == '7ffcb0f2-b305-1031-916c-47d262a62cc5'

    def test_extensionExists(self):

        with pytest.raises(GOsaException):
            self.rpc.extensionExists('cn=Frank Reich,ou=people,dc=example,dc=de', 'PosixUser')

        assert self.rpc.extensionExists('cn=Frank Reich,ou=people,dc=example,dc=net', 'PosixUser') is True

    def test_saveUserPreferences(self):
        with pytest.raises(GOsaException):
            self.rpc.saveUserPreferences('unkown', 'description', 'test')

        with mock.patch('gosa.backend.plugins.rpc.methods.ObjectProxy') as m:
            m.return_value.guiPreferences = {}
            self.rpc.saveUserPreferences('admin', 'description', 'test')
            assert m.return_value.commit.called

        with mock.patch('gosa.backend.plugins.rpc.methods.ObjectProxy') as m:
            m.return_value.guiPreferences = None
            self.rpc.saveUserPreferences('admin', 'description', 'test')
            assert m.return_value.commit.called

    def test_loadUserPreferences(self):
        with pytest.raises(GOsaException):
            self.rpc.loadUserPreferences('unkown', 'description')

        with mock.patch('gosa.backend.plugins.rpc.methods.ObjectProxy') as m:
            m.return_value.guiPreferences = {"description": "test"}
            assert self.rpc.loadUserPreferences('admin', 'description') == "test"
            m.return_value.guiPreferences = ''
            assert self.rpc.loadUserPreferences('admin', 'description') is None

    def test_searchForObjectDetails(self):
        with pytest.raises(GOsaException),\
                mock.patch("gosa.backend.plugins.rpc.methods.ObjectFactory.getInstance") as m:
            m.return_value.getObjectBackendParameters.return_value = None
            self.rpc.searchForObjectDetails('admin', 'unknown', 'groupMembership', None, None, None)

        mockedResolver = mock.MagicMock()
        mockedResolver.check.return_value = False

        with mock.patch.dict("gosa.backend.plugins.rpc.methods.PluginRegistry.modules", {'ACLResolver': mockedResolver}):
            res = self.rpc.searchForObjectDetails('admin', 'User', 'manager', '', ['uid'], None)
            assert len(res) == 0

        mockedResolver.check.return_value = True

        with mock.patch.dict("gosa.backend.plugins.rpc.methods.PluginRegistry.modules", {'ACLResolver': mockedResolver}):
            res = self.rpc.searchForObjectDetails('admin', 'User', 'manager', '', ['uid'], None)
            assert len(res) == 2

        with mock.patch.dict("gosa.backend.plugins.rpc.methods.PluginRegistry.modules", {'ACLResolver': mockedResolver}):
            res = self.rpc.searchForObjectDetails('admin', 'User', 'manager', '', ['uid'], ['cn=System Administrator,ou=people,dc=example,dc=net'])
            assert len(res) == 1
            assert 'freich' in res[0]['uid']
            assert 'dn' in res[0]

        with mock.patch.dict("gosa.backend.plugins.rpc.methods.PluginRegistry.modules", {'ACLResolver': mockedResolver}):
            res = self.rpc.searchForObjectDetails('admin', 'User', 'manager', 'Frank', ['uid','unknown'], None)
            assert len(res) == 1
            assert 'freich' in res[0]['uid']
            assert 'dn' in res[0]
            assert 'unknown' in res[0] and res[0]['unknown'] == ""


        mockedResolver.calls.reset()

        with mock.patch.dict("gosa.backend.plugins.rpc.methods.PluginRegistry.modules", {'ACLResolver': mockedResolver}),\
             mock.patch("gosa.backend.plugins.rpc.methods.ObjectFactory.getInstance") as m:
            m.return_value.getObjectBackendParameters.return_value = {'manager': ('User', 'uid', None, None)}
            res = self.rpc.searchForObjectDetails('admin', 'User', 'manager', 'freich', ['uid'], None)
            assert len(res) == 1
            assert 'freich' in res[0]['uid']
            assert 'dn' not in res[0]
            mockedResolver.check.assert_called_with('admin','net.example.objects.User', 's', base='cn=Frank Reich,ou=people,dc=example,dc=net')

    def test_getObjectDetails(self):
        with pytest.raises(GOsaException), \
             mock.patch("gosa.backend.plugins.rpc.methods.ObjectFactory.getInstance") as m:
            m.return_value.getObjectBackendParameters.return_value = None
            self.rpc.getObjectDetails('unknown', 'groupMembership', None, None)

        res = self.rpc.getObjectDetails('User', 'manager', ['cn=Frank Reich,ou=people,dc=example,dc=net', 'cn=System Administrator,ou=people,dc=example,dc=net'], ['uid','unknown'])
        assert len(res['map']) == 2
        assert 'cn=System Administrator,ou=people,dc=example,dc=net' in res['map']
        assert 'cn=Frank Reich,ou=people,dc=example,dc=net' in res['map']

    def test_search(self):
        with pytest.raises(GOsaException):
            self.rpc.search('admin', 'dc=example,dc=net', 'UNKNOWN_SCOPE', 'freich')

        with pytest.raises(GOsaException):
            self.rpc.search('admin', 'dc=example,dc=net', 'SUB', 'freich', fltr={'mod-time': 'unknown-mod-time'})

        assert self.rpc.search('admin', None, 'SUB', 'freich') == []

        with make_session() as session:
            res = session.execute('SELECT "obj-index".uuid AS "obj-index_uuid", "obj-index".dn AS "obj-index_dn", "obj-index"._parent_dn AS "obj-index__parent_dn", "obj-index"._adjusted_parent_dn AS "obj-index__adjusted_parent_dn", "obj-index"._type AS "obj-index__type", "obj-index"._last_modified AS "obj-index__last_modified", "obj-index"._invisible AS "obj-index__invisible", ts_rank_cd(so_index.search_vector, to_tsquery( \'freich\')) AS rank, "kv-index_1".key_id AS "kv-index_1_key_id", "kv-index_1".uuid AS "kv-index_1_uuid", "kv-index_1".key AS "kv-index_1_key", "kv-index_1".value AS "kv-index_1_value", so_index_1.so_uuid AS so_index_1_so_uuid, so_index_1.reverse_parent_dn AS so_index_1_reverse_parent_dn, so_index_1.title AS so_index_1_title, so_index_1.description AS so_index_1_description, so_index_1.search AS so_index_1_search, so_index_1.types AS so_index_1_types, so_index_1.search_vector AS so_index_1_search_vector FROM so_index, "obj-index" LEFT OUTER JOIN "kv-index" AS "kv-index_1" ON "obj-index".uuid = "kv-index_1".uuid LEFT OUTER JOIN so_index AS so_index_1 ON "obj-index".uuid = so_index_1.so_uuid WHERE so_index.search_vector @@ to_tsquery(\'simple\', \'freich\') ORDER BY ts_rank_cd(so_index.search_vector, to_tsquery(\'freich\')) DESC, "kv-index_1".key').fetchall()
            print(res)

        res = self.rpc.search('admin', 'dc=example,dc=net', 'SUB', 'freich')
        # user + group freich must be found
        print(res)
        res = res["results"]
        assert res[0]['title'] == "freich" or res[0]['title'] == "Frank Reich"
        assert res[1]['title'] == "freich" or res[1]['title'] == "Frank Reich"

        res = self.rpc.search('admin', 'dc=example,dc=net', 'SUB', 'freich', fltr={'mod-time': 'hour'})["results"]
        assert len(res) == 0

        res = self.rpc.search('admin', 'dc=example,dc=net', 'ONE', 'freich')["results"]
        assert len(res) == 0

        res = self.rpc.search('admin', 'ou=people,dc=example,dc=net', 'ONE', 'freich')["results"]
        assert len(res) == 1
        assert res[0]['title'] == "Frank Reich"

        res = self.rpc.search('admin', 'ou=people,dc=example,dc=net', 'CHILDREN', 'freich')["results"]
        assert len(res) == 1

        res = self.rpc.search('admin', 'cn=Frank Reich,ou=people,dc=example,dc=net', 'BASE', 'freich',)["results"]
        assert len(res) == 1
        assert res[0]['title'] == "Frank Reich"
