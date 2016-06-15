# This file is part of the clacks framework.
#
#  http://clacks-project.org
#
# Copyright:
#  (C) 2010-2012 GONICUS GmbH, Germany, http://www.gonicus.de
#
# License:
#  GPL-2: http://www.gnu.org/licenses/gpl-2.0.html
#
# See the LICENSE file in the project's top-level directory for details.

import unittest
import pytest
import os
# from gosa.common.acl import ACL, ACLSet, ACLRole, ACLRoleEntry, ACLResolver, ACLException
from gosa.common import Environment

Environment.reset()
Environment.config = os.path.join(os.path.dirname(os.path.realpath(__file__)), "test.conf")
Environment.noargs = True

@pytest.mark.skip(reason="needs to be updated when ACL has been ported to GOsa")
class TestACLResolver(unittest.TestCase):

    env = None
    ldap_base = None

    def setUp(self):
        """ Stuff to be run before every test """
        self.env = Environment.getInstance()

        self.resolver = ACLResolver()
        self.resolver.clear()
        self.ldap_base = self.resolver.base

    def test_simple_exported_command(self):

        # Ensure that we've got the right permissions to perform this tests.
        acls = ACLSet()
        acl = ACL(scope=ACL.SUB)
        acl.add_action('%s.acl' % self.env.domain, 'rw')
        acl.set_members(['acl_tester'])
        acls.add(acl)
        self.resolver.add_acl_set(acls)

        # -------------

        # Create first role with some acls
        self.resolver.addACLRole('acl_tester', 'rolle1')
        self.resolver.addACLToRole('acl_tester', 'rolle1', 0, [{'topic': 'com.wurstpelle.de', 'acls': 'rwcds'}], 'sub')

        # Create another role which uses the above defined role
        self.resolver.addACLRole('acl_tester', 'rolle2')
        self.resolver.addACLToRole('acl_tester', 'rolle2', 0, None, None, 'rolle1')

        # Now use the role 'rolle1' and check if it is resolved correclty
        lid = self.resolver.addACL('acl_tester', 'dc=gonicus,dc=de', 0, ['peter'], None, None, 'rolle2')
        self.assertTrue(self.resolver.check('peter', 'com.wurstpelle.de', 'r', {}, 'dc=1,dc=gonicus,dc=de'),
                "Resolving acl-roles using the exported clacks.agent commands does not work! The user should be able to read, but he cannot!")

        # Set the currently added acl-rule to a non-role based acl and defined some actions
        self.resolver.updateACL('acl_tester', lid, members=['peter', 'cajus'], actions=[{'topic': 'com.*', 'acls': 'rwcds'}], scope='sub')
        self.assertTrue(self.resolver.check('peter', 'com.wurstpelle.de', 'r', {}, 'dc=1,dc=gonicus,dc=de'),
                "Resolving acl-roles using the exported clacks.agent commands does not work! The user should be able to read, but he cannot!")

        self.resolver.updateACL('acl_tester', lid, actions=[{'topic': 'com.nope', 'acls': 'rwcds'}])
        self.assertFalse(self.resolver.check('peter', 'com.wurstpelle.de', 'r', {}, 'dc=1,dc=gonicus,dc=de'),
                "Resolving acl-roles using the exported clacks.agent commands does not work! The user should not be able to read, but he can!")

        # Drop the actions and fall back to use a role.
        self.resolver.updateACL('acl_tester', lid, rolename='rolle2')
        self.assertTrue(self.resolver.check('peter', 'com.wurstpelle.de', 'r', {}, 'dc=1,dc=gonicus,dc=de'),
                "Resolving acl-roles using the exported clacks.agent commands does not work! The user should be able to read, but he cannot!")

        # -----------------

        # Now update the role-acl 1 to use another role.
        self.resolver.addACLRole('acl_tester', 'dummy')
        self.resolver.updateACLRole('acl_tester', 2, use_role='dummy')
        self.assertFalse(self.resolver.check('peter', 'com.wurstpelle.de', 'r', {}, 'dc=1,dc=gonicus,dc=de'),
                "Resolving acl-roles using the exported clacks.agent commands does not work! The user should not be able to read, but he can!")

        # Now switch back to an action-based acl.
        self.resolver.updateACLRole('acl_tester', 2, actions=[{'topic': 'com.wurstpelle.de', 'acls': 'rwcds'}], scope='sub')
        self.assertTrue(self.resolver.check('peter', 'com.wurstpelle.de', 'r', {}, 'dc=1,dc=gonicus,dc=de'),
                "Resolving acl-roles using the exported clacks.agent commands does not work! The user should be able to read, but he cannot!")

        #------------------

        # Now remove the role-acl with id 1 from the resolver.
        self.resolver.removeRoleACL('acl_tester', 2)
        self.assertFalse(self.resolver.check('peter', 'com.wurstpelle.de', 'r', {}, 'dc=1,dc=gonicus,dc=de'),
                "Resolving acl-roles using the exported clacks.agent commands does not work! The user should not be able to read, but he can!")

        # -----------------

        # Try to remove role 'roll2'
        self.assertRaises(ACLException, self.resolver.removeRole, 'acl_tester', 'rolle2')

    def test_role_removal(self):
        """
        This test checks if an ACLRole objects can be removed!
        """

        # Create an ACLRole
        role = ACLRole('role1')
        acl = ACLRoleEntry(scope=ACL.ONE)
        acl.add_action('org.clacks.factory', 'rwx')
        role.add(acl)
        self.resolver.add_acl_role(role)

        # Use the recently created role.
        base = self.ldap_base
        aclset = ACLSet(base)
        acl = ACL(role='role1')
        acl.set_members([u'tester1'])
        aclset.add(acl)
        self.resolver.add_acl_set(aclset)

        # Check the permissions to be sure that they are set correctly
        self.assertTrue(self.resolver.check('tester1', 'org.clacks.factory', 'r', base=base),
                "ACLRoles are not resolved correctly! The user should be able to read, but he cannot!")

        self.assertRaises(ACLException, self.resolver.remove_role, 'role1')

        self.assertTrue(self.resolver.check('tester1', 'org.clacks.factory', 'r', base=base),
                "ACLRoles are not resolved correctly! The user should be able to read, but he cannot!")

        self.resolver.remove_aclset_by_base(base)

        self.assertFalse(self.resolver.check('tester1', 'org.clacks.factory', 'r', base=base),
                "Role removal failed! The user should not be able to read, but he can!")

        self.assertTrue(self.resolver.remove_role('role1'),
                "Role removal failed! The expected return code was True!")

        self.assertTrue(len(self.resolver.list_roles()) == 0,
                "Role removal failed! The role still exists despite removal!")

    def test_remove_acls_for_user(self):

        # Create acls with scope SUB
        aclset = ACLSet()
        acl = ACL(scope=ACL.SUB)
        acl.set_members([u'tester1', u'tester2'])
        acl.add_action('org.clacks.factory', 'rwx')
        aclset.add(acl)
        self.resolver.add_acl_set(aclset)

        # Now remove all ACLs for user 'tester1' but keep those for 'tester2'
        self.resolver.remove_acls_for_user('tester1')

        # No check the permissions 'tester1' should not be able to read anymore, where 'tester2' should.
        self.assertFalse(self.resolver.check('tester1', 'org.clacks.factory', 'r'),
                "Removing ACLs for a specific user does not work correctly! The user should not be able to read, but he can!")

        self.assertTrue(self.resolver.check('tester2', 'org.clacks.factory', 'r'),
                "Removing ACLs for a specific user does not work correctly! The user should still be able to read, but he cannot!")

    def test_role_endless_recursion(self):
        """
        A test which ensures that roles do not refer to each other, creating an endless-recursion.
        role1 -> role2 -> role1
        """
        # Create an ACLRole
        role1 = ACLRole('role1')
        role2 = ACLRole('role2')
        role3 = ACLRole('role3')

        self.resolver.add_acl_role(role1)
        self.resolver.add_acl_role(role2)
        self.resolver.add_acl_role(role3)

        acl1 = ACLRoleEntry(role='role2')
        acl2 = ACLRoleEntry(role='role3')
        acl3 = ACLRoleEntry(role='role1')

        role1.add(acl1)
        role2.add(acl2)
        role3.add(acl3)

        # Use the recently created role.
        base = self.ldap_base
        aclset = ACLSet(base)
        acl = ACL(role='role1')
        acl.set_members([u'tester1'])
        aclset.add(acl)
        self.resolver.add_acl_set(aclset)

        # Check the permissions to be sure that they are set correctly
        self.assertRaises(Exception, self.resolver.check, 'tester1', 'org.clacks.factory', 'r',
            base=base)

    def test_user_wildcards(self):
        """
        checks if wildcards/regular expressions can be used for ACL member names
        i.e. to match all users starting with 'clacks_' and ending with '_test'
            acl.set_members([u'^clacks_.*_test$'])
        """

        # Create acls with wildcard # in actions
        base = self.ldap_base
        aclset = ACLSet(base)
        acl = ACL(scope=ACL.ONE)
        acl.set_members([u'^clacks_.*_test$'])
        acl.add_action('org.clacks.factory', 'rwx')
        acl.set_priority(100)
        aclset.add(acl)
        self.resolver.add_acl_set(aclset)

        # Check the permissions to be sure that they are set correctly
        self.assertTrue(self.resolver.check('clacks_user_test', 'org.clacks.factory', 'r', base=base),
                "Wildcards in ACL members are not resolved correctly! The user was not able to read, but he should!")

        # Check the permissions to be sure that they are set correctly
        self.assertTrue(self.resolver.check('clacks__test', 'org.clacks.factory', 'r', base=base),
                "Wildcards in ACL members are not resolved correctly! The user was not able to read, but he should!")

        # Check the permissions to be sure that they are set correctly
        self.assertFalse(self.resolver.check('clacks_test_testWrong', 'org.clacks.factory', 'r', base=base),
                "Wildcards in ACL members are not resolved correctly! The was able to read, but he shouldn't!")

    def test_action_wildcards(self):
        """
        This test checks if ACLs containing wildcard actions are processed correctly.
        e.g.    To match all actions for 'com.' that ends with '.fatcory'
                acl.add_action('com.#.factory', 'rwx')
        """

        # Create acls with wildcard # in actions
        base = self.ldap_base
        aclset = ACLSet(base)
        acl = ACL(scope=ACL.ONE)
        acl.set_members([u'tester1'])
        acl.add_action('com.#.factory', 'rwx')
        acl.set_priority(100)
        aclset.add(acl)
        self.resolver.add_acl_set(aclset)

        # Check the permissions to be sure that they are set correctly
        self.assertTrue(self.resolver.check('tester1', 'org.clacks.factory', 'r', base=base),
                "Wildcards (#) in actions are not resolved correctly! The user should be able to read, but he cannot!")
        self.assertTrue(self.resolver.check('tester1', 'com.gonicus.factory', 'r', base=base),
                "Wildcards (#) in actions are not resolved correctly! The user should be able to read, but he cannot!")
        self.assertFalse(self.resolver.check('tester1', 'org.clacks.factory', 'r', base=base),
                "Wildcards (#) in actions are not resolved correctly! The user should not be able to read, but he can!")

        # Clear created ACL defintions
        self.resolver.clear()

        # Create acls with wildcard * in actions
        base = self.ldap_base
        aclset = ACLSet(base)
        acl = ACL(scope=ACL.ONE)
        acl.set_members([u'tester1'])
        acl.add_action('com.*.factory', 'rwx')
        acl.set_priority(100)
        aclset.add(acl)
        self.resolver.add_acl_set(aclset)

        # Check the permissions to be sure that they are set correctly
        self.assertTrue(self.resolver.check('tester1', 'org.clacks.factory', 'r', base=base),
                "Wildcards (*) in actions are not resolved correctly! The user should be able to read, but he cannot!")
        self.assertTrue(self.resolver.check('tester1', 'com.gonicus.factory', 'r', base=base),
                "Wildcards (*) in actions are not resolved correctly! The user should be able to read, but he cannot!")
        self.assertTrue(self.resolver.check('tester1', 'org.clacks.factory', 'r', base=base),
                "Wildcards (*) in actions are not resolved correctly! The user should be able to read, but he cannot!")

    def test_roles(self):
        """
        This test checks if ACLRole objects are resolved correctly.
        """

        # Create an ACLRole
        role = ACLRole('role1')
        acl = ACLRoleEntry(scope=ACL.ONE)
        acl.add_action('org.clacks.factory', 'rwx')
        role.add(acl)
        self.resolver.add_acl_role(role)

        # Use the recently created role.
        base = self.ldap_base
        aclset = ACLSet(base)
        acl = ACL(role='role1')
        acl.set_members([u'tester1'])
        aclset.add(acl)
        self.resolver.add_acl_set(aclset)

        # Check the permissions to be sure that they are set correctly
        self.assertTrue(self.resolver.check('tester1', 'org.clacks.factory', 'r', base=base),
                "ACLRoles are not resolved correctly! The user should be able to read, but he cannot!")

    def test_role_recursion(self):
        """
        This test checks if ACLRoles that contain ACLRoles are resolved correctly.
        e.g.
        ACLSet -> Acl -> points to role1
                         role1 -> AclRoleEntry -> points to role 2
                                                  role 2 contains the effective acls.
        """

        # Create an ACLRole
        role1 = ACLRole('role1')
        acl = ACLRoleEntry(scope=ACL.ONE)
        acl.add_action('org.clacks.factory', 'rwx')
        role1.add(acl)
        self.resolver.add_acl_role(role1)

        # Create another ACLRole wich refers to first one
        role2 = ACLRole('role2')
        acl = ACLRoleEntry(role='role1')
        role2.add(acl)
        self.resolver.add_acl_role(role2)

        # Use the recently created role.
        base = self.ldap_base
        aclset = ACLSet(base)
        acl = ACL(role='role2')
        acl.set_members([u'tester1'])
        aclset.add(acl)
        self.resolver.add_acl_set(aclset)

        # Check the permissions to be sure that they are set correctly
        self.assertTrue(self.resolver.check('tester1', 'org.clacks.factory', 'r',
            base=base),
                "Stacked ACLRoles are not resolved correctly! The user should be able to read, but he cannot!")

    def test_acl_priorities(self):

        # Set up a RESET and a ONE or SUB scoped acl for the same base
        # and check which wins.

        # Create acls with scope SUB
        base = self.ldap_base
        aclset = ACLSet(base)
        acl = ACL(scope=ACL.ONE)
        acl.set_members([u'tester1'])
        acl.add_action('org.clacks.factory', 'rwx')
        acl.set_priority(100)
        aclset.add(acl)
        self.resolver.add_acl_set(aclset)

        # Check the permissions to be sure that they are set correctly
        self.assertTrue(self.resolver.check('tester1', 'org.clacks.factory', 'r', base=base),
                "Acl priorities are not handled correctly! The user should be able to read, but he cannot!")

        # Now add the RESET acl
        acl = ACL(scope=ACL.RESET)
        acl.set_members([u'tester1'])
        acl.add_action('org.clacks.factory', 'rwx')
        acl.set_priority(99)
        aclset.add(acl)

        # Check the permissions to be sure that they are set correctly
        self.assertFalse(self.resolver.check('tester1', 'org.clacks.factory', 'r', base=base),
                "Acl priorities are not handled correctly! The user should not be able to read, but he can!")

    def test_acls_scope_reset(self):
        """
        This test checks if an ACL entry containing the RESET scope revokes permission correctly.
        """

        # Create acls with scope SUB
        base = "dc=a," + self.ldap_base
        aclset = ACLSet(base)
        acl = ACL(scope=ACL.SUB)
        acl.set_members([u'tester1'])
        acl.add_action('org.clacks.factory', 'rwx')
        aclset.add(acl)
        self.resolver.add_acl_set(aclset)

        # Check for acls for the base, should return False
        base = self.ldap_base
        self.assertFalse(self.resolver.check('tester1', 'org.clacks.factory', 'r', base=base),
                "ACL scope RESET is not resolved correclty! The user should not be able to read, but he can!")

        # Check for acls for the tree we've created acls for.
        base = "dc=a," + self.ldap_base
        self.assertTrue(self.resolver.check('tester1', 'org.clacks.factory', 'r', base=base),
                "ACL scope RESET is not resolved correclty! The user should be able to read, but he cannot!")

        # Check for acls for one level above the acl definition
        base = "dc=b,dc=a," + self.ldap_base
        self.assertTrue(self.resolver.check('tester1', 'org.clacks.factory', 'r', base=base),
                "ACL scope RESET is not resolved correclty! The user should be able to read, but he cannot!")

        # Check for acls for two levels above the acl definition
        base = "dc=c,dc=b,dc=a," + self.ldap_base
        self.assertTrue(self.resolver.check('tester1', 'org.clacks.factory', 'r', base=base),
                "ACL scope RESET is not resolved correclty! The user should be able to read, but he cannot!")

        # ------
        # Now add the ACL.RESET
        # ------
        base = "dc=b,dc=a," + self.ldap_base
        aclset = ACLSet(base)
        acl = ACL(scope=ACL.RESET)
        acl.set_members([u'tester1'])
        acl.add_action('org.clacks.factory', 'rwx')
        aclset.add(acl)

        self.resolver.add_acl_set(aclset)

        # Check for acls for the tree we've created acls for.
        # Should return True
        base = "dc=a," + self.ldap_base
        self.assertTrue(self.resolver.check('tester1', 'org.clacks.factory', 'r', base=base),
                "ACL scope RESET is not resolved correclty! The user should be able to read, but he cannot!")

        # Check for acls for one level above the acl definition
        # Should return False
        base = "dc=b,dc=a," + self.ldap_base
        self.assertFalse(self.resolver.check('tester1', 'org.clacks.factory', 'r', base=base),
                "ACL scope RESET is not resolved correclty! The user should not be able to read, but he can!")

        # Check for acls for two levels above the acl definition
        # Should return False
        base = "dc=c,dc=b,dc=a," + self.ldap_base
        self.assertFalse(self.resolver.check('tester1', 'org.clacks.factory', 'r', base=base),
                "ACL scope RESET is not resolved correclty! The user should not be able to read, but he can!")

    def test_acls_scope_sub(self):
        """
        This test checks if permissions with scope SUB are spreed over the subtree correctly.
        A ACL.SUB scope will effect the complete subtree of the base. (In case that no ACL.RESET is used.)
        """

        # Create acls with scope SUB
        base = "dc=a," + self.ldap_base
        aclset = ACLSet(base)
        acl = ACL(scope=ACL.SUB)
        acl.set_members([u'tester1'])
        acl.add_action('org.clacks.factory', 'rwx')
        aclset.add(acl)
        self.resolver.add_acl_set(aclset)

        # Check for read, write, create, execute permisions
        base = "dc=a," + self.ldap_base
        self.assertTrue(self.resolver.check('tester1', 'org.clacks.factory', 'r', base=base),
                "ACL scope SUB is not resolved correclty! The user should be able to read, but he cannot!")
        self.assertTrue(self.resolver.check('tester1', 'org.clacks.factory', 'w', base=base),
                "ACL scope SUB is not resolved correclty! The user should be able to read, but he cannot!")
        self.assertTrue(self.resolver.check('tester1', 'org.clacks.factory', 'x', base=base),
                "ACL scope SUB is not resolved correclty! The user should be able to read, but he cannot!")
        self.assertFalse(self.resolver.check('tester1', 'org.clacks.factory', 'd', base=base),
                "ACL scope SUB is not resolved correclty! The user should not be able to read, but he can!")

        # Check for permissions one level above the base we've created acls for.
        # This should return True.
        base = "dc=b,dc=a," + self.ldap_base
        self.assertTrue(self.resolver.check('tester1', 'org.clacks.factory', 'r', base=base),
                "ACL scope SUB is not resolved correclty! The user should be able to read, but he cannot!")

        # Check for permissions tow levels above the base we've created acls for.
        # This should return True too.
        base = "dc=c,dc=b,dc=a," + self.ldap_base
        self.assertTrue(self.resolver.check('tester1', 'org.clacks.factory', 'r', base=base),
                "ACL scope SUB is not resolved correclty! The user should be able to read, but he cannot!")

        # Check for permissions one level below the base we've created acls for.
        # This should return False.
        base = self.ldap_base
        self.assertFalse(self.resolver.check('tester1', 'org.clacks.factory', 'r', base=base),
                "ACL scope SUB is not resolved correclty! The user should not be able to read, but he can!")

    def test_acls_scope_one(self):
        """
        This test check if the scope ACL.ONE is populated correclty.
        """

        # Create acls with scope ONE
        base = "dc=a," + self.ldap_base
        aclset = ACLSet(base)
        acl = ACL(scope=ACL.ONE)
        acl.set_members([u'tester1'])
        acl.add_action('org.clacks.factory', 'rwx')
        aclset.add(acl)
        self.resolver.add_acl_set(aclset)

        # Check for read, write, create, execute permisions
        base = "dc=a," + self.ldap_base
        self.assertTrue(self.resolver.check('tester1', 'org.clacks.factory', 'r', base=base),
                "ACL scope ONE is not resolved correclty! The user should be able to read, but he cannot!")
        self.assertTrue(self.resolver.check('tester1', 'org.clacks.factory', 'w', base=base),
                "ACL scope ONE is not resolved correclty! The user should be able to read, but he cannot!")
        self.assertTrue(self.resolver.check('tester1', 'org.clacks.factory', 'x', base=base),
                "ACL scope ONE is not resolved correclty! The user should be able to read, but he cannot!")
        self.assertFalse(self.resolver.check('tester1', 'org.clacks.factory', 'd', base=base),
                "ACL scope ONE is not resolved correclty! The user should not be able to read, but he can!")

        # Check for permissions one level above the base we've created acls for.
        base = "dc=b,dc=a," + self.ldap_base
        self.assertFalse(self.resolver.check('tester1', 'org.clacks.factory', 'r', base=base),
                "ACL scope ONE is not resolved correclty! The user should not be able to read, but he can!")

        # Check for permissions one level below the base we've created acls for.
        base = self.ldap_base
        self.assertFalse(self.resolver.check('tester1', 'org.clacks.factory', 'r', base=base),
                "ACL scope ONE is not resolved correclty! The user should not be able to read, but he can!")


if __name__ == '__main__':
    unittest.main()
