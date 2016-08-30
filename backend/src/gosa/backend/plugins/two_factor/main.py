# This file is part of the GOsa project.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.
import logging
import os
from gosa.backend.utils.ldap import check_auth
from gosa.common.components import Command

from pyotp import TOTP, random_base32
from gosa.backend.exceptions import ACLException
from gosa.backend.objects import ObjectProxy
from gosa.common import Environment
from gosa.common.components import Plugin
from gosa.common.components import PluginRegistry
from json import loads, dumps
from gosa.common.utils import N_
from gosa.common.error import GosaErrorHandler as C

# Register the errors handled  by us
C.register_codes(dict(
    UNKNOWN_2FA_METHOD=N_("Unknown two factor authentication method '%(method)s'"),
    CHANGE_2FA_METHOD_FORBIDDEN=N_("Wrong password! Changing two-factor authentication method denied.")
))


class UnknownTwoFAMethod(Exception):
    pass


class ChangingNotAllowed(Exception):
    pass


class TwoFactorAuthManager(Plugin):
    """
    Manages the two factor authentication settings for users
    """
    # TODO: implement U2F

    _priority_ = 80
    _target_ = 'user'
    instance = None
    methods = [None, "otp"]#, "u2f"]
    __settings = {}

    def __init__(self):
        super(TwoFactorAuthManager, self).__init__()
        self.__log = logging.getLogger(__name__)
        self.env = Environment.getInstance()
        self.settings_file = self.env.config.get("user.2fa-store", "/var/lib/gosa/2fa")
        self.__reload()

    def __reload(self):
        if not os.path.exists(self.settings_file):
            self.__save_settings()
        else:
            with open(self.settings_file, "r") as f:
                self.__settings = loads(f.read())

    @staticmethod
    def get_instance():
        """
        Returns an instance of this object
        """
        if not TwoFactorAuthManager.instance:
            TwoFactorAuthManager.instance = TwoFactorAuthManager()
        return TwoFactorAuthManager.instance

    def __save_settings(self):
        with open(self.settings_file, "w") as f:
            f.write(dumps(self.__settings))

    @Command(needsUser=True, __help__=N_("Returns the available two factor authentication methods"))
    def getAvailable2FAMethods(self, user_name):
        return self.methods

    @Command(needsUser=True, __help__=N_("Returns the current two factor authentication method for the given user"))
    def getTwoFactorMethod(self, user_name, object_dn):

        # Do we have read permissions for the requested attribute
        topic = "%s.objects.%s.attributes.%s" % (self.env.domain, "User", "twoFactorMethod")
        aclresolver = PluginRegistry.getInstance("ACLResolver")
        if not aclresolver.check(user_name, topic, "r", base=object_dn):

            self.__log.debug("user '%s' has insufficient permissions to read %s on %s, required is %s:%s" % (
                user_name, "twoFactorMethod", object_dn, topic, "r"))
            raise ACLException(C.make_error('PERMISSION_ACCESS', topic, target=object_dn))

        user = ObjectProxy(object_dn)
        return self.get_method_from_user(user)

    @Command(needsUser=True, __help__=N_("Enable two factor authentication for the given user"))
    def setTwoFactorMethod(self, user_name, object_dn, factor_method, user_password=None):

        # Do we have read permissions for the requested attribute
        topic = "%s.objects.%s.attributes.%s" % (self.env.domain, "User", "twoFactorMethod")
        aclresolver = PluginRegistry.getInstance("ACLResolver")
        if not aclresolver.check(user_name, topic, "w", base=object_dn):

            self.__log.debug("user '%s' has insufficient permissions to write %s on %s, required is %s:%s" % (
                user_name, "twoFactorMethod", object_dn, topic, "w"))
            raise ACLException(C.make_error('PERMISSION_ACCESS', topic, target=object_dn))

        if factor_method == "None":
            factor_method = None

        if factor_method not in self.methods:
            raise UnknownTwoFAMethod(C.make_error("UNKNOWN_2FA_METHOD", method=factor_method))

        # Get the object for the given dn
        user = ObjectProxy(object_dn)
        current_method = self.get_method_from_user(user)
        if current_method == factor_method:
            # nothing to change
            return None

        if current_method is not None:
            # we need to be verified by user password in order to change the method
            if current_method == "otp":
                if user_password is None or not check_auth(user_name, user_password):
                    raise ChangingNotAllowed(C.make_error('CHANGE_2FA_METHOD_FORBIDDEN'))
            elif current_method == "u2f":
                raise NotImplementedError()

        if factor_method == "otp":
            return self.__enable_otp(user)
        elif factor_method == "u2f":
            return self.__enable_u2f(user)
        elif factor_method is None:
            # disable two factor auth
            del self.__settings[user.uuid]
            self.__save_settings()
        return None

    def verify(self, user_name, object_dn, key):

        # Do we have read permissions for the requested attribute
        topic = "%s.objects.%s.attributes.%s" % (self.env.domain, "User", "twoFactorMethod")
        aclresolver = PluginRegistry.getInstance("ACLResolver")
        if not aclresolver.check(user_name, topic, "r", base=object_dn):

            self.__log.debug("user '%s' has insufficient permissions to read %s on %s, required is %s:%s" % (
                user_name, "twoFactorMethod", object_dn, topic, "r"))
            raise ACLException(C.make_error('PERMISSION_ACCESS', topic, target=object_dn))

        # Get the object for the given dn
        user = ObjectProxy(object_dn)
        factor_method = self.get_method_from_user(user)
        if factor_method == "otp":
            totp = TOTP(self.__settings[user.uuid]['otp_secret'])
            return totp.verify(key)

        elif factor_method == "u2f":
            raise NotImplementedError()

        elif factor_method is None:
            return True

        return False

    def get_method_from_user(self, user):
        """
        Get the currently used two-factor authentication method of the given user

        :param user: User to check
        :type user: ObjectProxy
        :return: the two-factor method of the user
        :rtype: string or None
        """
        if isinstance(user, str):
            user = ObjectProxy(user)
        if user.uuid in self.__settings:
            if 'otp_secret' in self.__settings[user.uuid]:
                return "otp"
        return None

    def __enable_otp(self, user):

        secret = random_base32()
        totp = TOTP(secret)
        self.__settings[user.uuid] = {
            'otp_secret': secret
        }
        self.__save_settings()
        return totp.provisioning_uri("%s@%s.gosa" % (user.uid, self.env.domain))

    def __enable_u2f(self, user):
        raise NotImplementedError()

