# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

import pkg_resources
import logging
from gosa.common.components import Plugin
from gosa.common.components.command import Command
from gosa.common.utils import N_
from zope.interface import implementer
from gosa.common.handler import IInterfaceHandler
from gosa.backend.objects.proxy import ObjectProxy
from gosa.common.components import PluginRegistry
from gosa.common import Environment
from gosa.backend.exceptions import ACLException
from gosa.common.error import GosaErrorHandler as C


# Register the errors handled  by us
C.register_codes(dict(
    PASSWORD_METHOD_UNKNOWN=N_("Cannot detect password method"),
    PASSWORD_UNKNOWN_HASH=N_("No password method to generate hash of type '%(type)s' available"),
    PASSWORD_INVALID_HASH=N_("Invalid hash type for password method '%(method)s'"),
    PASSWORD_NO_ATTRIBUTE=N_("Object has no 'userPassword' attribute"),
    PASSWORD_NOT_AVAILABLE=N_("No password to lock.")))


class PasswordException(Exception):
    pass

@implementer(IInterfaceHandler)
class PasswordManager(Plugin):
    """
    Manager password changes
    """
    _priority_ = 91
    _target_ = 'password'

    methods = None
    instance = None

    def __init__(self):
        super(PasswordManager, self).__init__()
        self.__log = logging.getLogger(__name__)

    @staticmethod
    def get_instance():
        """
        Returns an instance of this object
        """
        if not PasswordManager.instance:
            PasswordManager.instance = PasswordManager()
        return PasswordManager.instance

    @Command(needsUser=True, __help__=N_("Locks the account password for the given DN"))
    def lockAccountPassword(self, user, object_dn):
        """
        Locks the account password for the given DN
        """

        # Do we have read permissions for the requested attribute
        env = Environment.getInstance()
        topic = "%s.objects.%s.attributes.%s" % (env.domain, "User", "userPassword")
        aclresolver = PluginRegistry.getInstance("ACLResolver")
        if not aclresolver.check(user, topic, "w", base=object_dn):

            self.__log.debug("user '%s' has insufficient permissions to write %s on %s, required is %s:%s" % (
                user, "isLocked", object_dn, topic, "w"))
            raise ACLException(C.make_error('PERMISSION_ACCESS', topic, target=object_dn))

        # Get the object for the given dn
        user = ObjectProxy(object_dn)

        # Check if there is a userPasswort available and set
        if not "userPassword" in user.get_attributes():
            raise PasswordException(C.make_error("PASSWORD_NO_ATTRIBUTE"))
        if not user.userPassword:
            raise PasswordException(C.make_error("PASSWORD_NOT_AVAILABLE"))

        # Try to detect the responsible password method-class
        pwd_o = self.detect_method_by_hash(user.userPassword)
        if not pwd_o:
            raise PasswordException(C.make_error("PASSWORD_METHOD_UNKNOWN"))

        # Lock the hash and save it
        user.userPassword = pwd_o.lock_account(user.userPassword)
        user.commit()

    @Command(needsUser=True, __help__=N_("Unlocks the account password for the given DN"))
    def unlockAccountPassword(self, user, object_dn):
        """
        Unlocks the account password for the given DN
        """

        # Do we have read permissions for the requested attribute
        env = Environment.getInstance()
        topic = "%s.objects.%s.attributes.%s" % (env.domain, "User", "userPassword")
        aclresolver = PluginRegistry.getInstance("ACLResolver")
        if not aclresolver.check(user, topic, "w", base=object_dn):

            self.__log.debug("user '%s' has insufficient permissions to write %s on %s, required is %s:%s" % (
                user, "isLocked", object_dn, topic, "w"))
            raise ACLException(C.make_error('PERMISSION_ACCESS', topic, target=object_dn))

        # Get the object for the given dn and its used password method
        user = ObjectProxy(object_dn)

        # Check if there is a userPasswort available and set
        if not "userPassword" in user.get_attributes():
            raise PasswordException(C.make_error("PASSWORD_NO_ATTRIBUTE"))
        if not user.userPassword:
            raise PasswordException(C.make_error("PASSWORD_NOT_AVAILABLE"))

        # Try to detect the responsible password method-class
        pwd_o = self.detect_method_by_hash(user.userPassword)
        if not pwd_o:
            raise PasswordException(C.make_error("PASSWORD_METHOD_UNKNOWN"))

        # Unlock the hash and save it
        user.userPassword = pwd_o.unlock_account(user.userPassword)
        user.commit()

    @Command(needsUser=True, __help__=N_("Check whether the account can be locked or not"))
    def accountLockable(self, user, object_dn):
        index = PluginRegistry.getInstance("ObjectIndex")

        # Do we have read permissions for the requested attribute
        env = Environment.getInstance()
        topic = "%s.objects.%s.attributes.%s" % (env.domain, "User", "isLocked")
        aclresolver = PluginRegistry.getInstance("ACLResolver")
        if not aclresolver.check(user, topic, "r", base=object_dn):

            self.__log.debug("user '%s' has insufficient permissions to read %s on %s, required is %s:%s" % (
                user, "isLocked", object_dn, topic, "r"))
            raise ACLException(C.make_error('PERMISSION_ACCESS', topic, target=object_dn))

        # Get password hash
        res = index.search({'dn': object_dn, 'userPassword': '%'}, {'userPassword': 1})
        if len(res):
            hsh = res[0]['userPassword'][0]

        else:
            # No password hash -> cannot lock/unlock account
            return False

        # Try to detect the responsible password method-class
        pwd_o = self.detect_method_by_hash(hsh)
        if not pwd_o:

            # Could not identify password method
            return False

        return pwd_o.isLockable(hsh)

    @Command(needsUser=True, __help__=N_("Check whether the account can be unlocked or not"))
    def accountUnlockable(self, user, object_dn):
        index = PluginRegistry.getInstance("ObjectIndex")

        # Do we have read permissions for the requested attribute
        env = Environment.getInstance()
        topic = "%s.objects.%s.attributes.%s" % (env.domain, "User", "isLocked")
        aclresolver = PluginRegistry.getInstance("ACLResolver")
        if not aclresolver.check(user, topic, "r", base=object_dn):

            self.__log.debug("user '%s' has insufficient permissions to read %s on %s, required is %s:%s" % (
                user, "isLocked", object_dn, topic, "r"))
            raise ACLException(C.make_error('PERMISSION_ACCESS', topic, target=object_dn))

        res = index.search({'dn': object_dn, 'userPassword': '%'}, {'userPassword': 1})
        if len(res):
            hsh = res[0]['userPassword'][0]
        else:
            # No password hash -> cannot lock/unlock account
            return False

        # Try to detect the responsible password method-class
        pwd_o = self.detect_method_by_hash(hsh)
        if not pwd_o:

            # Could not identify password method
            return False

        return pwd_o.isUnlockable(hsh)

    @Command(needsUser=True, __help__=N_("Changes the used password enryption method"))
    def setUserPasswordMethod(self, user, object_dn, method, password):
        """
        Changes the used password encryption method
        """

        # Do we have read permissions for the requested attribute
        env = Environment.getInstance()
        topic = "%s.objects.%s.attributes.%s" % (env.domain, "User", "userPassword")
        aclresolver = PluginRegistry.getInstance("ACLResolver")
        if not aclresolver.check(user, topic, "w", base=object_dn):

            self.__log.debug("user '%s' has insufficient permissions to write %s on %s, required is %s:%s" % (
                user, "isLocked", object_dn, topic, "w"))
            raise ACLException(C.make_error('PERMISSION_ACCESS', topic, target=object_dn))

        # Try to detect the responsible password method-class
        pwd_o = self.get_method_by_method_type(method)
        if not pwd_o:
            raise PasswordException(C.make_error("PASSWORD_UNKNOWN_HASH", type=method))

        # Generate the new password hash usind the detected method
        pwd_str = pwd_o.generate_password_hash(password, method)

        # Set the password and commit the changes
        user = ObjectProxy(object_dn)
        user.userPassword = pwd_str
        user.commit()

    @Command(needsUser=True, __help__=N_("Sets a new password for a user"))
    def setUserPassword(self, user, object_dn, password):
        """
        Set a new password for a user
        """

        # Do we have read permissions for the requested attribute
        env = Environment.getInstance()
        topic = "%s.objects.%s.attributes.%s" % (env.domain, "User", "userPassword")
        aclresolver = PluginRegistry.getInstance("ACLResolver")
        if not aclresolver.check(user, topic, "w", base=object_dn):

            self.__log.debug("user '%s' has insufficient permissions to write %s on %s, required is %s:%s" % (
                user, "isLocked", object_dn, topic, "w"))
            raise ACLException(C.make_error('PERMISSION_ACCESS', topic, target=object_dn))

        user = ObjectProxy(object_dn)
        method = user.passwordMethod

        # Try to detect the responsible password method-class
        pwd_o = self.get_method_by_method_type(method)
        if not pwd_o:
            raise PasswordException(C.make_error("PASSWORD_UNKNOWN_HASH", type=method))

        # Generate the new password hash usind the detected method
        pwd_str = pwd_o.generate_password_hash(password, method)

        # Set the password and commit the changes
        user.userPassword = pwd_str
        user.commit()

    @Command(__help__=N_("List all password hashing-methods"))
    def listPasswordMethods(self):
        """
        Returns a list of all available password methods
        """
        return list(self.list_methods().keys())

    @Command(__help__=N_("List all password recovery questions"))
    def listRecoveryQuestions(self):
        """
        Returns a list with all available and translated password recovery questions
        """
        questions = [
            N_("Which phone number from your childhood do you remember best (e.g. 058123456)?"),
            N_("What is the name of your oldest cousin (e.g. Luise Miller)?"),
            N_("What are the second names or nicknames of all your children (e.g. Max, Sam, and Lisa)?"),
            N_("Who was your best friend in childhood (e.g. Robert Danilo)?"),
            N_("What is your favorite book (author and title) (e.g. Donald Knuth, The Art of Programming)?"),
            N_("What is your favorite quote / proverb / aphorism (e.g. the pen is mightier than the sword)?"),
            N_("Who was your favorite teacher (e.g. Anna Webber)?"),
            N_("Who is your favorite historical person (e.g. Henry Dunant)?"),
            N_("Where did you spend the most wonderful holidays of your childhood (e.g. Paradise Island)?"),
            N_("What is your favorite historical event (e.g. the industrial revolution)?"),
            N_("What is your favorite literary figure (e.g. William Tell)?"),
            N_("Which person do you admire the most (e.g. Nelson Mandela)?"),
            N_("What model was your first car or bicycle (e.g. Fiat Panda)?"),
            N_("Which famous, no longer living person would you like to meet (e.g. Leonardo da Vinci)?"),
            N_("Who is your favorite actor, musician or painter (e.g. Pablo Picasso)?"),
            N_("What was your favorite stuffed animal (e.g. teddy)?"),
            N_("Where were you at New Year 2000 (e.g. Moulin Rouge)?"),
            N_("What are the last two words on page 32 of your favorite book (e.g. went out)?"),
        ]
        return questions

    @Command(__help_=N_("Request a password reset"))
    def requestPasswordReset(self, uid, recovery_question_data):
        """
        Request a password reset if the submitted password recovery answers match the stored ones for the given user
        :param uid: user id
        :param recovery_question_data: map of array index => answer
        :return: Boolean
        """

    def detect_method_by_hash(self, hash_value):
        """
        Tries to find a password-method that is responsible for this kind of hashes
        """
        methods = self.list_methods()
        for hash_name in methods:
            if methods[hash_name].is_responsible_for_password_hash(hash_value):
                return methods[hash_name]
        return None

    def get_method_by_method_type(self, method_type):
        """
        Returns the passwod-method that is responsible for the given hashing-method,
        e.g. get_method_by_method_type('crypt/blowfish')
        """
        methods = self.list_methods()
        return methods[method_type] if method_type in methods.keys() else None

    def list_methods(self):
        """
        Return a list of all useable password-hashing methods
        """

        # Build up a method hash map if not done before
        if not PasswordManager.methods:
            methods = {}

            # Walk through password methods and build up a hash-map
            for entry in pkg_resources.iter_entry_points("password.methods"):
                module = entry.load()()
                names = module.get_hash_names()
                if not names:
                    raise PasswordException(C.make_error("PASSWORD_INVALID_HASH", method=module.__class__.__name__))

                for name in names:
                    methods[name] = module

            PasswordManager.methods = methods

        return PasswordManager.methods
