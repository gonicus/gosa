# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

import unittest
from gosa.backend.objects.comparator.acl_roles import *

class AclSetComparatorTests(unittest.TestCase):

    @unittest.mock.patch.object(PluginRegistry, 'getInstance')
    def test_IsAclRole(self, mockedResolver):
        resolver = unittest.mock.MagicMock(autoSpec=True, create=True)
        resolver.getAclRoles.return_value = {"name":["role1","role2"]}
        mockedResolver.return_value = resolver

        comp = IsAclRole(None)
        (result, errors) = comp.process(None, None, [{}])
        assert result == False
        assert len(errors) == 1

        (result, errors) = comp.process(None, None, [{"priority":"high"}])
        assert result == False
        assert len(errors) == 1

        (result, errors) = comp.process(None, None, [{"priority": "high", "members":[]}])
        assert result == False
        assert len(errors) == 1

        # with rolename + actions
        (result, errors) = comp.process(None, None, [{"priority": "high", "members": [], "rolename":"role1", "actions":["action"]}])
        assert result == False
        assert len(errors) == 1

        #wrong rolename type
        (result, errors) = comp.process(None, None, [{"priority": "high", "members": [], "rolename": {"role1"}}])
        assert result == False
        assert len(errors) == 1

        #unallowed rolename
        (result, errors) = comp.process(None, None, [{"priority": "high", "members": [], "rolename": "role3"}])
        assert result == False
        assert len(errors) == 1

        # no rolename, scope missing
        (result, errors) = comp.process(None, None, [
            {"priority": "high", "members": [], "actions": ["action"]}])
        assert result == False
        assert len(errors) == 1

        # no rolename, actions missing
        (result, errors) = comp.process(None, None, [
            {"priority": "high", "members": [], "scope": "local"}])
        assert result == False
        assert len(errors) == 1

        # no rolename, no topic in actions
        (result, errors) = comp.process(None, None, [
            {"priority": "high", "members": [], "scope": "local", "actions":{"acl":"acl", "options":{}}}])
        assert result == False
        assert len(errors) == 1

        # no rolename, no acl in actions
        (result, errors) = comp.process(None, None, [
            {"priority": "high", "members": [], "scope": "local",
             "actions": [{"topic": "topic","options": {}}]}])
        assert result == False
        assert len(errors) == 1

        # no rolename, wrong topic type in actions
        (result, errors) = comp.process(None, None, [
            {"priority": "high", "members": [], "scope": "local",
             "actions": [{"topic": True, "acl": "crod", "options": {}}]}])
        assert result == False
        assert len(errors) == 1

        # no rolename, wrong acl type in actions
        (result, errors) = comp.process(None, None, [
            {"priority": "high", "members": [], "scope": "local",
             "actions": [{"topic": "topic", "acl": True, "options": {}}]}])
        assert result == False
        assert len(errors) == 1

        # no rolename, wrong acl content in actions
        (result, errors) = comp.process(None, None, [
            {"priority": "high", "members": [], "scope": "local",
             "actions": [{"topic": "topic", "acl": "asds", "options": {}}]}])
        assert result == False
        assert len(errors) == 1

        # no rolename, unsupportted keys in actions
        (result, errors) = comp.process(None, None, [
            {"priority": "high", "members": [], "scope": "local",
             "actions": [{"topic": "topic", "acl": "crod", "options": {},"unsupported": True}]}])
        assert result == False
        assert len(errors) == 1

        # no rolename, wrong options type in actions
        (result, errors) = comp.process(None, None, [
            {"priority": "high", "members": [], "scope": "local",
             "actions": [{"topic": "topic", "acl": "crod", "options": []}]}])
        assert result == False
        assert len(errors) == 1

        # finally a valid example
        (result, errors) = comp.process(None, None, [
            {"priority": "high", "members": [], "scope": "local",
             "actions": [{"topic": "topic", "acl": "crod", "options": {}}]}])
        assert result == True
        assert len(errors) == 0