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
import pyqrcode
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
    CHANGE_2FA_METHOD_FORBIDDEN=N_("You are not allowed to change the two factor authentication method")
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

    def __init__(self):
        super(TwoFactorAuthManager, self).__init__()
        self.__log = logging.getLogger(__name__)
        self.env = Environment.getInstance()
        self.settings_file = self.env.config.get("user.2fa-store", "/var/lib/gosa/2fa")
        self.settings = {}
        if not os.path.exists(self.settings_file):
            self.__save_settings()
        else:
            with open(self.settings_file, "r") as f:
                self.settings = loads(f.read())

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
            f.write(dumps(self.settings))

    @Command(needsUser=True, __help__=N_("Enable two factor authentication for the given user"))
    def setTwoFactorMethod(self, user, object_dn, factor_method, key=None):

        if factor_method not in ("otp", "u2f", None):
            raise UnknownTwoFAMethod(C.make_error("UNKNOWN_2FA_METHOD", method=factor_method))

        # Do we have read permissions for the requested attribute
        env = Environment.getInstance()
        topic = "%s.objects.%s.attributes.%s" % (env.domain, "User", "twoFactorMethod")
        aclresolver = PluginRegistry.getInstance("ACLResolver")
        if not aclresolver.check(user, topic, "w", base=object_dn):

            self.__log.debug("user '%s' has insufficient permissions to write %s on %s, required is %s:%s" % (
                user, "twoFactorMethod", object_dn, topic, "w"))
            raise ACLException(C.make_error('PERMISSION_ACCESS', topic, target=object_dn))

        # Get the object for the given dn
        user = ObjectProxy(object_dn)
        current_method = self.get_method_from_user(user)
        if current_method == factor_method:
            # nothing to change
            return None

        if current_method is not None:
            # we need to be verified by the old method in order to change the method
            if current_method == "otp":
                totp = TOTP(self.settings[user.uuid]['otp_secret'])
                if key is None or not totp.verify(key):
                    raise ChangingNotAllowed(C.make_error('CHANGE_2FA_METHOD_FORBIDDEN'))
            elif current_method == "u2f":
                raise NotImplementedError()

        if factor_method == "otp":
            return self.__enable_otp(user)
        elif factor_method == "u2f":
            return self.__enable_u2f(user)
        elif factor_method is None:
            # disable two factor auth
            del self.settings[user.uuid]
            self.__save_settings()
        return None

    def verify(self, user, object_dn, key):

        # Do we have read permissions for the requested attribute
        env = Environment.getInstance()
        topic = "%s.objects.%s.attributes.%s" % (env.domain, "User", "twoFactorMethod")
        aclresolver = PluginRegistry.getInstance("ACLResolver")
        if not aclresolver.check(user, topic, "r", base=object_dn):

            self.__log.debug("user '%s' has insufficient permissions to read %s on %s, required is %s:%s" % (
                user, "twoFactorMethod", object_dn, topic, "r"))
            raise ACLException(C.make_error('PERMISSION_ACCESS', topic, target=object_dn))

        # Get the object for the given dn
        user = ObjectProxy(object_dn)
        factor_method = self.get_method_from_user(user)
        if factor_method == "otp":
            totp = TOTP(self.settings[user.uuid]['otp_secret'])
            return totp.verify(key)

        elif factor_method == "u2f":
            raise NotImplementedError()

        return False

    def get_method_from_user(self, user):
        if isinstance(user, str):
            user = ObjectProxy(user)
        if user.uuid in self.settings:
            if 'otp_secret' in self.settings[user.uuid]:
                return "otp"
        return None

    def __enable_otp(self, user):

        if self.get_method_from_user(user) is not None:
            # 2FA already set, not changeable yet
            raise ChangingNotAllowed(C.make_error('CHANGE_2FA_METHOD_FORBIDDEN'))

        secret = random_base32()
        totp = TOTP(secret)
        self.settings[user.uuid] = {
            'otp_secret': secret
        }
        self.__save_settings()
        return totp.provisioning_uri("%s@%s.gosa" % (user.uid, self.env.domain))

    def __enable_u2f(self, user):
        raise NotImplementedError()

