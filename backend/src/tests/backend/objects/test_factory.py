# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

import pytest
from tests.GosaTestCase import GosaTestCase
from gosa.backend.objects.factory import *


class ObjectBackendTestCase(GosaTestCase):

    def setUp(self):
        self.obj = ObjectFactory()

    def tearDown(self):
        del self.obj

    def test_getAttributeTypes(self):
        res = self.obj.getAttributeTypes()
        # check if some type are available
        assert 'String' in res
        assert 'AnyType' in res
        assert 'Timestamp' in res
        assert 'Boolean' in res
        assert 'Binary' in res
        assert 'Integer' in res
        assert 'AclRole' in res
        assert 'AclSet' in res

    def test_getObjectBackendProperties(self):
        res = self.obj.getObjectBackendProperties('User')
        assert 'JSON' in res
        assert res['JSON']['type'] == 'User'
        assert 'LDAP' in res
        assert res['LDAP']['RDN'] == 'cn,uid'

    def test_getObjectBackendParameters(self):
        res = self.obj.getObjectBackendParameters('User', 'manager')
        assert res['manager'] == ['User', 'dn', None, None]
        assert self.obj.getObjectBackendParameters('User', 'type') == {}

    def test_getIndexedAttributes(self):
        res = self.obj.getIndexedAttributes()
        # just some checks
        assert 'displayName' in res
        assert 'givenName' in res
        assert 'uid' in res

    def test_getBinaryAttributes(self):
        res = self.obj.getBinaryAttributes()
        # just some checks
        assert 'audio' in res
        assert 'jpegPhoto' in res
        assert 'photo' in res
        assert 'userCertificate' in res

    def test_getAvailableObjectNames(self):
        res = self.obj.getAvailableObjectNames()
        # just some checks
        assert 'User' in res
        assert 'Domain' in res
        assert 'Country' in res
        assert 'Acl' in res

    def test_getObjectTemplates(self):
        res = self.obj.getObjectTemplates('User')
        assert res[0][0:3] == b'<ui'

    def test_getObjectDialogs(self):
        res = self.obj.getObjectDialogs('User')
        assert res == []

        res = self.obj.getObjectDialogs('SambaUser')
        assert res[0][0:3] == b'<ui'

    def test_getObjectTemplateNames(self):
        with pytest.raises(KeyError):
            self.obj.getObjectTemplateNames('Unknown')

        res = self.obj.getObjectTemplateNames('User')
        assert 'user.ui' in res
        assert 'user-organizational.ui' in res

    def test_getObjectDialogNames(self):
        with pytest.raises(KeyError):
            self.obj.getObjectDialogNames('Unknown')

        res = self.obj.getObjectDialogNames('SambaUser')
        assert 'sambaLogonHours.ui' in res
        assert 'sambaUserWorkstations.ui' in res
        assert 'sambaDomainInfo.ui' in res

    def test_getObjectSearchAid(self):
        with pytest.raises(KeyError):
            self.obj.getObjectSearchAid('Unknown')

        res = self.obj.getObjectSearchAid('User')
        assert res['type'] == 'User'
        assert res['tag'] == 'User'
        assert res['search'] == ['givenName', 'sn', 'cn', 'uid']
        assert res['keyword'] == ['User']
        assert {'filter': 'cn', 'type': 'PosixGroup', 'attribute': 'groupMembership'} in res['resolve']
        assert {'filter': 'DN', 'type': None, 'attribute': 'manager'} in res['resolve']

        assert res['map']['title'] == 'cn'
        assert res['map']['description'] == '%(description)s%(phoneRenderer)s%(mailRenderer)s<br>%(extensions)s'
        assert res['map']['icon'] == 'jpegPhoto'

    def test_getAllowedSubElementsForObject(self):
        with pytest.raises(KeyError):
            self.obj.getAllowedSubElementsForObject('Unknown')

        with pytest.raises(TypeError):
            self.obj.getAllowedSubElementsForObject('SambaUser')

        res = self.obj.getAllowedSubElementsForObject('Domain')
        assert 'PeopleContainer' in res
        assert 'GroupContainer' in res
        assert 'OrganizationalUnit' in res
        assert 'Organization' in res
        assert 'Locality' in res
        assert 'DomainComponent' in res
        assert 'Domain' in res
        assert 'Country' in res
        assert 'SambaDomain' in res
        assert 'DeviceContainer' in res
        assert 'OrganizationalRoleContainer' in res
        assert 'AclRole' in res
        assert 'SystemsContainer' in res

    def test_getAttributeTypeMap(self):
        with pytest.raises(KeyError):
            self.obj.getAttributeTypeMap('Unknown')

        with pytest.raises(TypeError):
            self.obj.getAttributeTypeMap('SambaUser')

        res = self.obj.getAttributeTypeMap('User')
        # just some checks
        assert res['ou'] == 'User'
        assert res['cn'] == 'User'
        assert res['uid'] == 'User'
        assert res['givenName'] == 'User'
        assert res['sambaPwdMustChange'] == 'SambaUser'
        assert res['uidNumber'] == 'PosixUser'
        assert res['shadowWarning'] == 'ShadowUser'

    def test_getReferences(self):
        res = self.obj.getReferences()
        assert res['PosixGroup']['memberUid'] == [('PosixUser', 'uid')]

        res = self.obj.getReferences('PosixUser', 'uid')
        assert res['PosixGroup']['memberUid'] == [('PosixUser', 'uid')]

    def test_get_attributes_by_object(self):
        with pytest.raises(TypeError):
            self.obj.get_attributes_by_object('Unknown')

        with pytest.raises(TypeError):
            self.obj.get_attributes_by_object('SambaUser')

        res = self.obj.get_attributes_by_object('User')
        assert res['ou']['base'] == 'User'
        assert res['cn']['base'] == 'User'
        assert res['sn']['base'] == 'User'
        assert res['uid']['base'] == 'User'
        assert res['givenName']['base'] == 'User'
        assert res['givenName']['secondary'] == ['PosixUser']
        assert res['sambaPwdMustChange']['base'] == 'SambaUser'
        assert res['uidNumber']['base'] == 'PosixUser'
        assert res['shadowWarning']['base'] == 'ShadowUser'

    def test_getAttributes(self):
        res = self.obj.getAttributes()
        # also just basic checking if something gets returned
        assert 'uid' in res
        assert 'User' in res['uid']
        assert 'SambaMachineAccount' in res['uid']

    def test_getNamedI18N(self):
        assert self.obj.getNamedI18N(None) == {}

        res = self.obj.getNamedI18N(['user.ui'], 'de')
        assert res['User'] == 'Benutzer'
        assert res['Title'] == 'Titel'

        res = self.obj.getNamedI18N(['user.ui'], 'de-DE')
        assert res['User'] == 'Benutzer'
        assert res['Title'] == 'Titel'

    def test_getXmlSchema(self):
        assert self.obj.getXMLSchema('User') is not None
        assert self.obj.getXMLSchema('Unknown') is None
