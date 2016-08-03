# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

import datetime
from unittest import mock, TestCase
from tests.GosaTestCase import *
from gosa.backend.objects.proxy import *


@slow
class ObjectProxyTestCase(TestCase):

    def test_init(self):
        with pytest.raises(ProxyException),\
                mock.patch('gosa.backend.objects.proxy.is_uuid', return_value=True):
            # unknown uuid
            ObjectProxy('78475884-c7f2-1035-8262-f535be14d43n')


        with pytest.raises(ProxyException):
            # unknown object type
            ObjectProxy('cn=Frank Reich,ou=people,dc=example,dc=net', 'Unknown')

        mocked_factory = mock.MagicMock()
        mocked_factory.identifyObject.return_value = (None, None)
        mocked_factory.getObjectTypes.return_value = ['User']
        with pytest.raises(ProxyException), \
             mock.patch('gosa.backend.objects.proxy.ObjectFactory.getInstance', return_value=mocked_factory):
            # base not found
            ObjectProxy('78475884-c7f2-1035-8262-f535be14d43a')

        user = ObjectProxy('cn=Frank Reich,ou=people,dc=example,dc=net')
        assert user.uid == 'freich'

        # create new user
        user = ObjectProxy('cn=Frank Reich,ou=people,dc=example,dc=net', 'User')
        assert user.uid is None

    def test_get_all_method_names(self):
        user = ObjectProxy('cn=Frank Reich,ou=people,dc=example,dc=net')
        res = user.get_all_method_names()
        assert 'lock' in res
        assert 'unlock' in res

    def test_get_extension_dependencies(self):
        user = ObjectProxy('cn=Frank Reich,ou=people,dc=example,dc=net')
        assert user.get_extension_dependencies('PosixUser') == []
        assert user.get_extension_dependencies('SambaUser') == ['PosixUser']

    def test_get_attributes(self):
        mocked_resolver = mock.MagicMock()

        def check(user, topic, mode, base):
            return topic == "net.example.objects.User.attributes.uid"
        mocked_resolver.check.side_effect = check

        with mock.patch.dict("gosa.backend.objects.proxy.PluginRegistry.modules", {'ACLResolver': mocked_resolver}):
            user = ObjectProxy('cn=Frank Reich,ou=people,dc=example,dc=net', None, 'admin')
            res = user.get_attributes()
            assert len(res) == 1
            assert 'uid' in res

            detailed = user.get_attributes(True)
            assert 'uid' in detailed
            assert detailed['uid']['mandatory'] is True

        # without user
        user = ObjectProxy('cn=Frank Reich,ou=people,dc=example,dc=net')
        res = user.get_attributes()
        assert len(res) > 1
        assert 'uid' in res
        assert 'givenName' in res

    def test_get_methods(self):
        mocked_resolver = mock.MagicMock()

        def check(user, topic, mode, base):
            return topic == "net.example.objects.User.methods.lock"
        mocked_resolver.check.side_effect = check

        with mock.patch.dict("gosa.backend.objects.proxy.PluginRegistry.modules", {'ACLResolver': mocked_resolver}):
            user = ObjectProxy('cn=Frank Reich,ou=people,dc=example,dc=net', None, 'admin')
            res = user.get_methods()
            assert len(res) == 1
            assert 'lock' in res

        # without user
        user = ObjectProxy('cn=Frank Reich,ou=people,dc=example,dc=net')
        res = user.get_methods()
        assert len(res) > 1
        assert 'lock' in res
        assert 'unlock' in res

    def test_get_parent_dn(self):
        user = ObjectProxy('cn=Frank Reich,ou=people,dc=example,dc=net', None, 'admin')
        assert user.get_parent_dn() == "ou=people,dc=example,dc=net"
        assert user.get_parent_dn('ou=people,dc=example,dc=net') == "dc=example,dc=net"

    def test_get_base_type(self):
        user = ObjectProxy('cn=Frank Reich,ou=people,dc=example,dc=net', None, 'admin')
        assert user.get_base_type() == "User"

    def test_get_extension_types(self):
        user = ObjectProxy('cn=Frank Reich,ou=people,dc=example,dc=net', None, 'admin')
        res =  user.get_extension_types()
        assert 'PosixUser' in res
        assert 'SambaUser' in res

    def test_get_templates(self):
        user = ObjectProxy('cn=Frank Reich,ou=people,dc=example,dc=net')
        res = user.get_templates()
        assert res['PosixUser'][0][0:3] == "<ui"
        assert res['User'][0][0:3] == "<ui"
        assert res['Acl'] is None

    def test_get_attribute_values(self):
        user = ObjectProxy('cn=Frank Reich,ou=people,dc=example,dc=net')
        res = user.get_attribute_values()

        assert res['value']['uid'] == "freich"
        assert 'loginShell' in res['values']

    def test_get_object_info(self):
        user = ObjectProxy('cn=Frank Reich,ou=people,dc=example,dc=net')
        res = user.get_object_info()

        assert res['base'] == 'User'
        assert 'changeSambaPassword' in res['extension_methods']['SambaUser']
        assert res['extensions']['PosixUser'] is True
        assert res['extensions']['Acl'] is False

    def test_extend(self):
        user = ObjectProxy('cn=Frank Reich,ou=people,dc=example,dc=net', None, 'admin')

        # unkown extension
        with pytest.raises(ProxyException):
            user.extend("unknown")

        #extension already active
        with pytest.raises(ProxyException):
            user.extend("PosixUser")

        # not allowed
        mocked_resolver = mock.MagicMock()
        mocked_resolver.check.return_value = False
        with mock.patch.dict("gosa.backend.objects.proxy.PluginRegistry.modules", {'ACLResolver': mocked_resolver}),\
                pytest.raises(ACLException):
            user = ObjectProxy('cn=Frank Reich,ou=people,dc=example,dc=net', None, 'admin')
            user.extend('TrustAccount')

        user = ObjectProxy('cn=Frank Reich,ou=people,dc=example,dc=net')
        # extend
        assert user.get_object_info()['extensions']['TrustAccount'] is False
        user.extend('TrustAccount')
        assert user.get_object_info()['extensions']['TrustAccount'] is True

        # extend retracted
        user.retract('TrustAccount')
        assert user.get_object_info()['extensions']['TrustAccount'] is False
        user.extend('TrustAccount')
        assert user.get_object_info()['extensions']['TrustAccount'] is True

    def test_retract(self):
        user = ObjectProxy('cn=Frank Reich,ou=people,dc=example,dc=net', None, 'admin')

        # unkown extension
        with pytest.raises(ProxyException):
            user.retract("unknown")

        # extension not active
        with pytest.raises(ProxyException):
            user.retract("TrustAccount")

        # required by others
        with pytest.raises(ProxyException):
            user.retract("PosixUser")

        # not allowed
        mocked_resolver = mock.MagicMock()
        mocked_resolver.check.return_value = False
        with mock.patch.dict("gosa.backend.objects.proxy.PluginRegistry.modules", {'ACLResolver': mocked_resolver}), \
             pytest.raises(ACLException):
            user = ObjectProxy('cn=Frank Reich,ou=people,dc=example,dc=net', None, 'admin')
            user.retract('SambaUser')

        user = ObjectProxy('cn=Frank Reich,ou=people,dc=example,dc=net')
        assert user.get_object_info()['extensions']['SambaUser'] is True
        user.retract('SambaUser')
        assert user.get_object_info()['extensions']['SambaUser'] is False

    def test_move(self):
        # check permissions
        mocked_resolver = mock.MagicMock()
        # First run: w=False, d=True, c=True
        # 2dn run: w=True, d=False, c=True
        # 3rd run: w=True, d=True, c=False
        mocked_resolver.check.side_effect = [False, True, True, True, False, True, True, True, False]

        with mock.patch.dict("gosa.backend.objects.proxy.PluginRegistry.modules", {'ACLResolver': mocked_resolver}):
            user = ObjectProxy('cn=Frank Reich,ou=people,dc=example,dc=net', None, 'admin')
            with pytest.raises(ACLException):
                user.move('new_base')

            with pytest.raises(ACLException):
                user.move('new_base')

            with pytest.raises(ACLException):
                user.move('new_base')

        user = ObjectProxy('cn=Frank Reich,ou=people,dc=example,dc=net')
        with mock.patch("zope.event.notify") as me, \
                mock.patch("gosa.backend.objects.object.ObjectBackendRegistry.getBackend") as mb:
            mb.return_value.identify.return_value = False
            assert user.move('ou=roles,dc=example,dc=net') is True
            mb.return_value.move.assert_called_with(user.uuid, 'ou=roles,dc=example,dc=net')
            assert me.called

            mocked_factory = mock.MagicMock()
            mocked_factory.identifyObject.return_value = ObjectFactory.getInstance().identifyObject('cn=Frank Reich,ou=people,dc=example,dc=net')
            mocked_factory.getObjectChildren.return_value = [1]
            with pytest.raises(ProxyException), \
                 mock.patch('gosa.backend.objects.proxy.ObjectFactory.getInstance', return_value=mocked_factory):
                # none recursive with children
                user = ObjectProxy('cn=Frank Reich,ou=people,dc=example,dc=net')
                user.move('ou=roles,dc=example,dc=net')

            # TODO test recursive moving
            # mb.reset_mock()
            # with mock.patch("gosa.backend.objects.proxy.ObjectProxy") as mp:
            #     # recursive
            #     assert user.move('cn=Frank Reich,ou=roles,dc=example,dc=net', True) is False
            #     mb.return_value.move.assert_called_with(user.uuid, 'cn=Frank Reich,ou=roles,dc=example,dc=net')

    def test_remove(self):
        # check permissions
        mocked_resolver = mock.MagicMock()
        mocked_resolver.check.return_value = False

        with mock.patch.dict("gosa.backend.objects.proxy.PluginRegistry.modules", {'ACLResolver': mocked_resolver}):
            user = ObjectProxy('cn=Frank Reich,ou=people,dc=example,dc=net', None, 'admin')

            with pytest.raises(ACLException):
                user.remove()

        user = ObjectProxy('cn=Frank Reich,ou=people,dc=example,dc=net')
        with mock.patch("gosa.backend.objects.proxy.ObjectProxy") as mp, \
                mock.patch("zope.event.notify") as me, \
                mock.patch("gosa.backend.objects.object.ObjectBackendRegistry.getBackend") as mb:
            user.remove(True)
            assert mb.return_value.remove.called
            assert me.called

        mocked_index = mock.MagicMock()
        mocked_index.search.return_value = [1]
        with pytest.raises(ProxyException), \
                mock.patch.dict("gosa.backend.objects.proxy.PluginRegistry.modules", {'ObjectIndex': mocked_index}), \
                mock.patch("zope.event.notify"):
            # none recursive with children
            user.remove()

    @mock.patch("zope.event.notify")
    @mock.patch("gosa.backend.objects.object.ObjectBackendRegistry.getBackend")
    def test_commit(self, mb, me):
        mb.return_value.identify.return_value = False

        # check permissions
        mocked_resolver = mock.MagicMock()
        mocked_resolver.check.return_value = False

        with mock.patch.dict("gosa.backend.objects.proxy.PluginRegistry.modules", {'ACLResolver': mocked_resolver}):
            user = ObjectProxy('cn=Test User,ou=people,dc=example,dc=net', 'User', 'admin')

            with pytest.raises(ACLException):
                user.commit()

        mocked_factory = mock.MagicMock()
        mocked_factory.identifyObject = ObjectFactory.getInstance().identifyObject
        mocked_factory.getObjectTypes = ObjectFactory.getInstance().getObjectTypes
        mocked_factory.getObject = ObjectFactory.getInstance().getObject
        mocked_factory.get_attributes_by_object = ObjectFactory.getInstance().get_attributes_by_object
        mocked_factory.getObjectProperties = ObjectFactory.getInstance().getObjectProperties
        mocked_factory.getObjectMethods = ObjectFactory.getInstance().getObjectMethods
        mocked_factory.getAttributeTypeMap = ObjectFactory.getInstance().getAttributeTypeMap
        mocked_factory.getAttributeTypes = ObjectFactory.getInstance().getAttributeTypes
        with mock.patch('gosa.backend.objects.proxy.ObjectFactory.getInstance', return_value=mocked_factory):
            user = ObjectProxy('ou=people,dc=example,dc=net', 'User')

            # add mandatory values
            user.givenName = "Test"
            user.sn = "User"
            user.uid = "tuser"

            user.commit()
            assert mb.return_value.create.called

    def test_attribute_manipulation(self):
        # check permissions
        mocked_resolver = mock.MagicMock()
        mocked_resolver.check.return_value = False

        with mock.patch.dict("gosa.backend.objects.proxy.PluginRegistry.modules", {'ACLResolver': mocked_resolver}):
            user = ObjectProxy('cn=Frank Reich,ou=people,dc=example,dc=net', None, 'admin')

            with pytest.raises(ACLException):
                user.lock()
            with pytest.raises(ACLException):
                print(user.uid)
            with pytest.raises(ACLException):
                user.uid = 'changed'

            mocked_resolver.check.return_value = True

            # unknown attribute
            with pytest.raises(AttributeError):
                print(user.unknown)
            with pytest.raises(AttributeError):
                user.unknown = "test"

            assert user.modifyTimestamp == datetime.datetime(2016, 6, 16, 9, 49, 6)

    def test_asJSON(self):
        # check permissions
        mocked_resolver = mock.MagicMock()
        mocked_resolver.check.return_value = False

        with mock.patch.dict("gosa.backend.objects.proxy.PluginRegistry.modules", {'ACLResolver': mocked_resolver}):
            user = ObjectProxy('cn=Frank Reich,ou=people,dc=example,dc=net', None, 'admin')

            with pytest.raises(ACLException):
                user.asJSON()

        user = ObjectProxy('cn=Frank Reich,ou=people,dc=example,dc=net')
        res = user.asJSON()
        assert res['dn'] == 'cn=Frank Reich,ou=people,dc=example,dc=net'
        assert type(res) == dict

    @pytest.mark.skip(reason="XSTL Stylesheet can't be parsed")
    def test_asXML(self):
        #TODO: fix the XSLT error

        # check permissions
        mocked_resolver = mock.MagicMock()
        mocked_resolver.check.return_value = False

        with mock.patch.dict("gosa.backend.objects.proxy.PluginRegistry.modules", {'ACLResolver': mocked_resolver}):
            user = ObjectProxy('cn=Frank Reich,ou=people,dc=example,dc=net', None, 'admin')

            with pytest.raises(ACLException):
                user.asXML()

        user = ObjectProxy('cn=Frank Reich,ou=people,dc=example,dc=net')
        res = user.asXML()
        print(res)
        assert res['dn'] == 'cn=Frank Reich,ou=people,dc=example,dc=net'