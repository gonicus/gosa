# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.
import random
import uuid as Uuid
import pkg_resources
import logging
from gosa.common.components import Plugin
from gosa.common.components.command import Command
from gosa.common.gjson import loads
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
    PASSWORD_NOT_AVAILABLE=N_("No password to lock."),
    UID_UNKNOWN=N_("User ID '%(target)s' is unknown."),
    PASSWORD_RECOVERY_IMPOSSIBLE=N_("The password recovery process cannot be started for this user, because of invalid ot missing data"),
    PASSWORD_RECOVERY_STATE_ERROR=N_("This step of the password recovery process cannot be executed at the current state")
))


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

        # Do we have write permissions for the requested attribute
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

        # Generate the new password hash using the detected method
        pwd_str = pwd_o.generate_password_hash(password, method)

        # Set the password and commit the changes
        user.userPassword = pwd_str
        user.commit()

    @Command(needsUser=True, __help__=N_("Sets a new password recovery answers for a user"))
    def setPasswordRecoveryAnswers(self, user, object_dn, data):
        """
        Set the password recovery answers for a user
        """
        data = loads(data)

        # Do we have read permissions for the requested attribute
        env = Environment.getInstance()
        topic = "%s.objects.%s.attributes.%s" % (env.domain, "User", "passwordRecoveryHash")
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

        # hash the new answers
        for idx, answer in data.items():
            data[idx] = pwd_o.generate_password_hash(self.clean_string(answer), method)
            print("%s encrypted with %s as index %s => %s" % (self.clean_string(answer), method, idx, data[idx]))

        # Set the password and commit the changes
        user.passwordRecoveryHash = data
        user.commit()

    @Command(__help__=N_("List all password hashing-methods"))
    def listPasswordMethods(self):
        """
        Returns a list of all available password methods
        """
        return list(self.list_methods().keys())

    @Command(noLoginRequired=True, __help__=N_("List all password recovery questions"))
    def listRecoveryQuestions(self):
        """
        Returns a list with all available and translated password recovery questions
        """
        # DO NOT CHANGE THE ORDER OF THESE QUESTIONS OR REMOVE QUESTIONS FROM THE LIST
        # as the answers are stored with a reference to the questions index
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

    @Command(noLoginRequired=True, __help__=N_("Request a password reset"))
    def requestPasswordReset(self, uid, step, uuid=None, data=None):
        """
        Request a password reset if the submitted password recovery answers match the stored ones for the given user
        :param uid: user id
        :param step: 'start' to trigger the password reset process by sending an email with activation link to the user
        :param uuid: the recovery uuid
        :param data: optional data required by the current step
        :return: *
        """

        # check for existing uid and status of the users password settings
        index = PluginRegistry.getInstance("ObjectIndex")
        res = index.search({'uid': uid, '_type': 'User'}, {'dn': 1})
        if len(res) == 0:
            raise PasswordException(C.make_error("UID_UNKNOWN", target=uid))
        dn = res[0]['dn']
        user = ObjectProxy(dn)
        if user.mail is None:
            raise PasswordException(C.make_error("PASSWORD_RECOVERY_IMPOSSIBLE"))

        recovery_state = user.passwordRecoveryState if user.passwordRecoveryState is not None else {}

        if step != "start":
            # check uuid
            if 'uuid' not in recovery_state or recovery_state['uuid'] != uuid:
                # recovery process has not been started
                raise PasswordException(C.make_error("PASSWORD_RECOVERY_STATE_ERROR"))

        if step == "start":
            # start process by generating an unique password recovery link for this user and sending it to him via mail

            if 'uuid' not in recovery_state:
                # generate a new id
                recovery_state['sent_counter'] = 0
                recovery_state['uuid'] = str(Uuid.uuid4())
                recovery_state['state'] = 'started'

            # send the link to the user
            content = N_("Please open this link to continue your password recovery process.")+":"
            gui = PluginRegistry.getInstance("HTTPService").get_gui_uri()
            content += "\n\n%s?pwruid=%s&uid=%s\n\n" % ("/".join(gui), recovery_state['uuid'], uid)

            mail = PluginRegistry.getInstance("Mail")
            mail.send(user.mail, N_("Password recovery link"), content)
            recovery_state["sent_counter"] += 1

            user.passwordRecoveryState = recovery_state
            user.commit()
            return True

        elif step == "get_questions":
            # check correct state
            if recovery_state['state'] is None:
                raise PasswordException(C.make_error("PASSWORD_RECOVERY_STATE_ERROR"))

            # return the indices of the questions the user has answered
            # TODO retrieve minimum amount of correct answers from user policy object
            return random.sample(user.passwordRecoveryHash.keys(), 3)

        elif step == "check_answers":
            # check correct state
            if recovery_state['state'] is None:
                raise PasswordException(C.make_error("PASSWORD_RECOVERY_STATE_ERROR"))

            data = loads(data)
            recovery_hashes = user.passwordRecoveryHash
            correct_answers = 0
            for idx, answer in data.items():
                if idx not in recovery_hashes:
                    # the user hasn't answered this question
                    continue
                # detect method from existing answer
                pwd_o = self.detect_method_by_hash(recovery_hashes[idx])
                if not pwd_o:
                    raise PasswordException(C.make_error("PASSWORD_RECOVERY_IMPOSSIBLE"))

                # encrypt and compare new answer
                if pwd_o.compare_hash(self.clean_string(answer), recovery_hashes[idx]):
                    correct_answers += 1

            # TODO retrieve minimum amount of correct answers from user policy object
            if correct_answers >= 3:
                recovery_state['state'] = 'verified'
                user.commit()
                return True
            else:
                return False

        elif step == "change_password":
            # check correct state
            if recovery_state['state'] != 'verified':
                raise PasswordException(C.make_error("PASSWORD_RECOVERY_STATE_ERROR"))

            self.setUserPassword(uid, user.dn, data)

            user.passwordRecoveryState = None
            user.commit()
            return True

    def clean_string(self, string):
        """ Removes all non word/digit characters from string and lowercases it."""
        return ''.join(e.lower() for e in string if e.isalnum())

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
        Returns the password-method that is responsible for the given hashing-method,
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
