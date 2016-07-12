import pytest
from unittest import mock
from gosa.backend.plugins.rpc.methods import GOsaException
import gosa
from tests.GosaTestCase import GosaTestCase, slow


class RpcMethodsTestCase(GosaTestCase):

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
        assert res[0][0:3] == b"<ui"

    def test_getGuiDialogs(self):

        with pytest.raises(GOsaException):
            self.rpc.getGuiDialogs('UnknownType')

        res = self.rpc.getGuiDialogs('SambaUser')
        assert res[0][0:3] == b"<ui"

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
            self.rpc.extensionExists('admin', 'cn=Frank Reich,ou=people,dc=example,dc=de', 'PosixUser')

        assert self.rpc.extensionExists('admin', 'cn=Frank Reich,ou=people,dc=example,dc=net', 'PosixUser') is True

    def test_saveUserPreferences(self):
        with pytest.raises(GOsaException):
            self.rpc.saveUserPreferences('unkown', 'description', 'test')

        with mock.patch('gosa.backend.plugins.rpc.methods.ObjectProxy') as m:
            m.return_value.guiPreferences = "{}"
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
            m.return_value.guiPreferences = '{"description": "test"}'
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
            uids = [res[0]['uid'], res[1]['uid']]
            assert 'freich' in uids
            assert 'admin' in uids
            assert 'dn' in res[0]
            assert 'dn' in res[1]

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
            mockedResolver.check.assert_called_with('admin','gosa.objects.User', 's', base='cn=Frank Reich,ou=people,dc=example,dc=net')

    def test_getObjectDetails(self):
        with pytest.raises(GOsaException), \
             mock.patch("gosa.backend.plugins.rpc.methods.ObjectFactory.getInstance") as m:
            m.return_value.getObjectBackendParameters.return_value = None
            self.rpc.getObjectDetails('unknown', 'groupMembership', None, None)

        res = self.rpc.getObjectDetails('User', 'manager', ['cn=Frank Reich,ou=people,dc=example,dc=net', 'cn=System Administrator,ou=people,dc=example,dc=net'], ['uid','unknown'])
        assert len(res['map']) == 2
        assert 'cn=System Administrator,ou=people,dc=example,dc=net' in res['map']
        assert 'cn=Frank Reich,ou=people,dc=example,dc=net' in res['map']

