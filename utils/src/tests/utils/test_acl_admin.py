# This file is part of the GOsa project.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.
import pytest
from unittest import mock, TestCase

from gosa.common.components.auth import AUTH_FAILED, AUTH_SUCCESS
from gosa.utils.acl_admin import *


class ACLAdminTestCase(TestCase):

    def setUp(self):
        super(ACLAdminTestCase, self).setUp()
        self.proxy = mock.MagicMock()
        self.acl = ACLAdmin(self.proxy)

    def tearDown(self):
        super(ACLAdminTestCase, self).tearDown()
        self.proxy.reset_mock()

    def test_get_value_from_args(self):
        assert self.acl.get_value_from_args("dn", ['test_dn']) == "test_dn"

        # test missing parameters
        for name in ["dn", "scope", "priority", "topic", "acl-definition", "members",
                     "acls", "rolename", "acl-update-action", "roleacl-update-action", "acl-add-action"]:
            with pytest.raises(SystemExit):
                self.acl.get_value_from_args(name, [])

        with pytest.raises(Exception):
            self.acl.get_value_from_args("unknown_parameter", [])

        with pytest.raises(SystemExit):
            self.acl.get_value_from_args("scope", ["unknown_scope"])
        assert self.acl.get_value_from_args("scope", ["sub"]) == "sub"

        with pytest.raises(SystemExit):
            self.acl.get_value_from_args("priority", ["-101"])
        with pytest.raises(SystemExit):
            self.acl.get_value_from_args("priority", ["101"])
        with pytest.raises(SystemExit):
            self.acl.get_value_from_args("priority", ["no int"])
        assert self.acl.get_value_from_args("priority", ["0"]) == 0

        assert self.acl.get_value_from_args("topic", ["test topic"]) == "test topic"

        with pytest.raises(SystemExit):
            self.acl.get_value_from_args("acl-definition", ["wrong def"])
        with pytest.raises(SystemExit):
            self.acl.get_value_from_args("acl-definition", ["topic:acl:wrong_option"])

        self.acl.get_value_from_args("acl-definition", ["topic:acl:test_options=option_value"]) == [{'topic': 'topic', 'acl': 'acl',
                                                                                                    'options': {
                                                                                                        'test_option': 'option_value'}
                                                                                                     }]
        assert self.acl.get_value_from_args("members", ["tester1 , tester2 "]) == ["tester1", "tester2"]

        assert self.acl.get_value_from_args("acls", ["test_acls"]) == "test_acls"
        assert self.acl.get_value_from_args("rolename", ["role1"]) == "role1"

        assert self.acl.get_value_from_args("options", []) == {}
        with pytest.raises(SystemExit):
            self.acl.get_value_from_args("options", ["wrong syntax"])
        assert self.acl.get_value_from_args("options", ["opt1:val1;opt2:val2;"]) == {'opt1': 'val1', 'opt2': 'val2'}

        with pytest.raises(SystemExit):
            self.acl.get_value_from_args("acl-update-action", ["unknown-action"])
        assert self.acl.get_value_from_args("acl-update-action", ["set-scope"]) == "set-scope"

        with pytest.raises(SystemExit):
            self.acl.get_value_from_args("roleacl-update-action", ["unknown-action"])
        assert self.acl.get_value_from_args("roleacl-update-action", ["set-scope"]) == "set-scope"

        with pytest.raises(SystemExit):
            self.acl.get_value_from_args("acl-add-action", ["unknown-action"])
        assert self.acl.get_value_from_args("acl-add-action", ["with-actions"]) == "with-actions"

    def test_add_acl(self):
        m_object = self.proxy.openObject.return_value
        m_object.get_extension_types.return_value = {}
        self.acl.add_acl(['with-actions', 'base', '0', 'tester', 'sub', 'topic:w', 'w'])
        assert not self.proxy.openObject.return_value.commit.called

        m_object.get_extension_types.return_value = {'Acl': None}
        self.acl.add_acl(['with-actions', 'base', '0', 'tester', 'sub', 'topic:w', 'w'])
        assert m_object.extend.called
        assert m_object.commit.called

        assert len(m_object.AclSets) == 1
        assert m_object.AclSets[0] == {
            'priority': 0,
            'members': ['tester'],
            'actions': [{
                'topic': 'topic',
                'acl': 'w',
                'options': {}
            }],
            'scope': 'sub'
        }
        m_object.reset_mock()

        # with role
        self.acl.add_acl(['with-role', 'base', '0', 'tester', 'role1'])
        assert m_object.extend.called
        assert m_object.commit.called

        assert len(m_object.AclSets) == 1
        assert m_object.AclSets[0] == {
            'priority': 0,
            'members': ['tester'],
            'rolename': 'role1'
        }

    def test_add_roleacl(self):
        m_object = self.proxy.openObject.return_value
        m_object.AclRoles = None
        self.acl.add_roleacl(['with-actions', 'base', '0', 'sub', 'topic:w', 'w'])
        assert not m_object.commit.called

        m_object.AclRoles = []
        self.acl.add_roleacl(['with-actions', 'base', '0', 'sub', 'topic:w', 'w'])
        assert m_object.commit.called

        assert len(m_object.AclRoles) == 1
        assert m_object.AclRoles[0] == {
            'priority': 0,
            'actions': [{
                'topic': 'topic',
                'acl': 'w',
                'options': {}
            }],
            'scope': 'sub'
        }
        m_object.reset_mock()
        m_object.AclRoles = []

        # with role
        self.acl.add_roleacl(['with-role', 'base', '0', 'role1'])
        assert m_object.commit.called

        assert len(m_object.AclRoles) == 1
        assert m_object.AclRoles[0] == {
            'priority': 0,
            'rolename': 'role1'
        }

    def test_add_role(self):
        m_object = self.proxy.openObject.return_value
        self.acl.add_role(['base', 'role1'])
        assert m_object.commit.called
        assert m_object.name == "role1"

    def test_remove_roleacls(self):
        m_object = self.proxy.openObject.return_value
        m_object.AclRoles = []
        self.acl.add_roleacl(['with-actions', 'base', '0', 'sub', 'topic:w', 'w'])
        assert len(m_object.AclRoles) == 1
        self.acl.remove_roleacls(['base'])
        assert len(m_object.AclRoles) == 0

    def test_remove_acls(self):
        m_object = self.proxy.openObject.return_value

        # does not support acls
        m_object.get_extension_types.return_value = {}
        self.acl.remove_acls(['base'])
        assert not m_object.retract.called

        # acl extensaion not activated
        m_object.get_extension_types.return_value = {'Acl': None}
        self.acl.remove_acls(['base'])
        assert not m_object.retract.called

        m_object.get_extension_types.return_value = {'Acl': True}
        self.acl.remove_acls(['base'])
        assert len(m_object.AclSets) == 0
        m_object.retract.assert_called_with("Acl")

    def test_remove_role(self):
        m_object = self.proxy.openObject.return_value
        self.acl.remove_role(["base"])
        assert m_object.remove.called

    def test_list(self):
        m_object = self.proxy.openObject.return_value
        m_object.AclRoles = []

        self.proxy.getACLs.return_value = []
        with mock.patch("gosa.utils.acl_admin.print") as m_print:
            self.acl.list([])
            m_print.assert_called_with("   ... none")

        self.acl.add_roleacl(['with-actions', 'base', '0', 'sub', 'topic:w', 'w'])
        m_object.get_extension_types.return_value = {'Acl': None}
        self.acl.add_acl(['with-actions', 'base', '0', 'tester', 'sub', 'topic:w', 'w'])
        acls = {
            'base': m_object.AclSets
        }
        acls['base'][0]['id'] = 0
        acls['base'][0]['actions'][0]['acls'] = acls['base'][0]['actions'][0]['acl']

        self.proxy.getACLs.return_value = acls

        roles = m_object.AclRoles
        roles[0]['name'] = 'role1'
        roles[0]['dn'] = 'base'
        roles[0]['acls'] = acls['base']
        self.proxy.getACLRoles.return_value = roles
        # just check that the function completes without errors, no assertions here

        self.acl.list([])


def test_main():
    sys.argv = ['acl_admin', '-u', 'admin', '-p', 'tester', '-s', 'http://localhost:8000/rpc']
    with mock.patch("gosa.utils.acl_admin.getopt") as m_getopt:
        m_getopt.getopt.side_effect = getopt.GetoptError('test error')
        with pytest.raises(SystemExit):
            main()
        m_getopt.getopt.side_effect = None
        m_getopt.getopt.return_value = [('-u', 'admin'), ('-p', 'tester'), ('-s', 'http://localhost:8000/rpc')], []

        # too few arguments
        with pytest.raises(SystemExit):
            main()

        # unknown method
        sys.argv = ['acl_admin', '-u', 'admin', '-p', 'tester', '-s', 'http://localhost:8000/rpc', 'unknown_method']
        with pytest.raises(SystemExit):
            main()

        with mock.patch("gosa.utils.acl_admin.print_help") as m_help:
            sys.argv = ['acl_admin', '-u', 'admin', '-p', 'tester', '-s', 'http://localhost:8000/rpc', '-h']
            with pytest.raises(SystemExit):
                main()
            assert m_help.called

        sys.argv = ['acl_admin', '-u', 'admin', '-p', 'tester', '-s', 'http://localhost:8000/rpc', 'add_acl', 'with-actions', 'base',
                    '0', 'tester', 'sub', 'topic:w', 'w']

        with mock.patch("gosa.utils.acl_admin.connect", return_value=mock.MagicMock()):
            main()

def test_connect():

    with mock.patch("gosa.utils.acl_admin.JSONServiceProxy") as m_proxy,\
            mock.patch("gosa.utils.acl_admin.input", return_value=""):
        with pytest.raises(SystemExit):
            connect()

        m_proxy.return_value.login.return_value = AUTH_FAILED
        with pytest.raises(SystemExit):
            connect('http://admin:tester@localhost:8000/rpc')

        m_proxy.return_value.login.side_effect = Exception("test error")
        with pytest.raises(SystemExit):
            connect('http://admin:tester@localhost:8000/rpc')

        with pytest.raises(SystemExit):
            connect('ftp://admin:tester@localhost:8000/rpc')

        m_proxy.return_value.login.side_effect = None
        m_proxy.return_value.login.return_value = AUTH_SUCCESS
        connect('http://localhost:8000/rpc', 'admin', 'tester')

        with mock.patch("gosa.utils.acl_admin.getpass.getpass", return_value="tester"), \
             mock.patch("gosa.utils.acl_admin.getpass.getuser", return_value="admin"):
            connect('http://localhost:8000/rpc')
