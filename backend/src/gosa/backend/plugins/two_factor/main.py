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
from gosa.common.gjson import loads, dumps
from u2flib_server.model import DeviceRegistration
from u2flib_server.u2f import (begin_registration, complete_registration,
                               begin_authentication, complete_authentication)
from cryptography.hazmat.primitives.serialization import Encoding
from pyotp import TOTP, random_base32
from gosa.backend.exceptions import ACLException
from gosa.backend.objects import ObjectProxy
from gosa.common import Environment
from gosa.common.components import Plugin
from gosa.common.components import PluginRegistry
from gosa.common.utils import N_, is_uuid
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
    methods = [None, "otp", "u2f"]
    __settings = {}

    def __init__(self):
        super(TwoFactorAuthManager, self).__init__()
        self.__log = logging.getLogger(__name__)
        self.env = Environment.getInstance()
        self.settings_file = self.env.config.get("user.2fa-store", "/var/lib/gosa/2fa")
        self.__reload()

        if self.env.config.get("http.ssl") is True:
            host = "localhost" if self.env.config.get("http.host", default="localhost") in ["0.0.0.0", "127.0.0.1"] else self.env.config.get("http.host", default="localhost")
            # U2F requires https protocol otherwise facet is invalid
            self.facet = "https://%s:%s" % (host, self.env.config.get('http.port', default=8080))
            self.app_id = self.facet
        else:
            # u2f only available in ssl mode
            self.methods = [None, "otp"]

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
        self.__check_acl(user_name, object_dn, "r")

        return self.get_method_from_user(object_dn)

    @Command(needsUser=True, __help__=N_("Enable two factor authentication for the given user"))
    def setTwoFactorMethod(self, user_name, object_dn, factor_method, user_password=None):

        # Do we have write permissions for the requested attribute
        self.__check_acl(user_name, object_dn, "w")

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
           if user_password is None or not check_auth(user_name, user_password):
            raise ChangingNotAllowed(C.make_error('CHANGE_2FA_METHOD_FORBIDDEN'))

        if factor_method == "otp":
            return self.__enable_otp(user)
        elif factor_method == "u2f":
            return self.__enable_u2f(user)
        elif factor_method is None:
            # disable two factor auth
            del self.__settings[user.uuid]
            self.__save_settings()
        return None

    @Command(needsUser=True, __help__=N_("Complete the started U2F registration"))
    def completeU2FRegistration(self, user_name, object_dn, data):

        # Do we have write permissions for the requested attribute
        self.__check_acl(user_name, object_dn, "w")

        uuid = self.__dn_to_uuid(object_dn)
        user_settings = self.__settings[uuid]
        data = loads(data)
        binding, cert = complete_registration(user_settings.pop('_u2f_enroll_'), data,
                                          [self.facet])
        devices = [DeviceRegistration.wrap(device)
                   for device in user_settings.get('_u2f_devices_', [])]
        devices.append(binding)
        user_settings['_u2f_devices_'] = [d.json for d in devices]
        self.__save_settings()

        self.__log.info("U2F device enrolled. Username: %s", user_name)
        self.__log.debug("Attestation certificate:\n%s", cert.public_bytes(Encoding.PEM))

        return True

    def sign(self, user_name, object_dn):

        # Do we have read permissions for the requested attribute
        self.__check_acl(user_name, object_dn, "r")

        uuid = self.__dn_to_uuid(object_dn)
        user_settings = self.__settings[uuid] if uuid in self.__settings else {}
        devices = [DeviceRegistration.wrap(device)
                   for device in user_settings.get('_u2f_devices_', [])]
        challenge = begin_authentication(self.app_id, devices)
        user_settings['_u2f_challenge_'] = challenge.json
        self.__save_settings()
        return challenge.json

    def verify(self, user_name, object_dn, key):

        # Do we have read permissions for the requested attribute
        self.__check_acl(user_name, object_dn, "r")

        # Get the object for the given dn
        uuid = self.__dn_to_uuid(object_dn)
        factor_method = self.get_method_from_user(uuid)
        user_settings = self.__settings[uuid] if uuid in self.__settings else {}
        if factor_method == "otp":
            totp = TOTP(user_settings.get('otp_secret'))
            return totp.verify(key)

        elif factor_method == "u2f":

            challenge = user_settings.pop('_u2f_challenge_')
            data = loads(key)
            device, c, t = complete_authentication(challenge, data, [self.facet])
            return {
                'keyHandle': device['keyHandle'],
                'touch': t,
                'counter': c
            }

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
            if not is_uuid(user):
                user = self.__dn_to_uuid(user)
        elif isinstance(user, ObjectProxy):
            user = user.uuid
        if user in self.__settings:
            if 'otp_secret' in self.__settings[user]:
                return "otp"
            elif '_u2f_devices_' in self.__settings[user]:
                return "u2f"

        return None

    def __dn_to_uuid(self, dn):
        index = PluginRegistry.getInstance("ObjectIndex")
        res = index.search({'dn': dn}, {'_uuid': 1})
        if len(res) == 1:
            return res[0]['_uuid']
        return None

    def __enable_otp(self, user):
        if user.uuid not in self.__settings:
            self.__settings[user.uuid] = {}

        user_settings = self.__settings[user.uuid]
        secret = random_base32()
        totp = TOTP(secret)
        user_settings['otp_secret'] = secret
        self.__save_settings()
        return totp.provisioning_uri("%s@%s.gosa" % (user.uid, self.env.domain))

    def __enable_u2f(self, user):
        if user.uuid not in self.__settings:
            self.__settings[user.uuid] = {}

        user_settings = self.__settings[user.uuid]
        devices = [DeviceRegistration.wrap(device)
                   for device in user_settings.get('_u2f_devices_', [])]
        enroll = begin_registration(self.app_id, devices)
        user_settings['_u2f_enroll_'] = enroll.json
        self.__save_settings()
        return enroll.json

    def __check_acl(self, user_name, object_dn, actions):
        # Do we have read permissions for the requested attribute
        topic = "%s.objects.%s.attributes.%s" % (self.env.domain, "User", "twoFactorMethod")
        aclresolver = PluginRegistry.getInstance("ACLResolver")
        if not aclresolver.check(user_name, topic, "r", base=object_dn):

            self.__log.debug("user '%s' has insufficient permissions for %s on %s, required is %s:%s" % (
                user_name, "twoFactorMethod", object_dn, topic, actions))
            raise ACLException(C.make_error('PERMISSION_ACCESS', topic, target=object_dn))
