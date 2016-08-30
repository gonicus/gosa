# This file is part of the GOsa project.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.
import pytest

from unittest import TestCase, mock
from gosa.backend.plugins.two_factor.main import *


class TwoFactorAuthManagerTestCase(TestCase):

    def setUp(self):
        super(TwoFactorAuthManagerTestCase, self).setUp()
        # make sure that we do not destroy anything
        env = Environment.getInstance()
        assert env.config.get("user.2fa-store").startswith("/tmp")
        os.remove(env.config.get("user.2fa-store"))
        self.manager = PluginRegistry.getInstance("TwoFactorAuthManager")

    def test_getAvailable2FAMethods(self):
        methods = self.manager.getAvailable2FAMethods("admin")
        assert None in methods
        assert 'otp' in methods

    def test_OTPMethod(self):
        with mock.patch("gosa.backend.plugins.two_factor.main.PluginRegistry.getInstance") as m_resolver:
            m_resolver.return_value.check.return_value = False
            with pytest.raises(ACLException):
                self.manager.getTwoFactorMethod("admin", "cn=System Administrator,ou=people,dc=example,dc=net")

            m_resolver.return_value.check.return_value = True
            assert self.manager.getTwoFactorMethod("admin", "cn=System Administrator,ou=people,dc=example,dc=net") is None

            # change the settings
            m_resolver.return_value.check.return_value = False
            with pytest.raises(ACLException):
                self.manager.setTwoFactorMethod("admin", "cn=System Administrator,ou=people,dc=example,dc=net", "otp")
            m_resolver.return_value.check.return_value = True
            assert self.manager.getTwoFactorMethod("admin", "cn=System Administrator,ou=people,dc=example,dc=net") is None

            self.manager.setTwoFactorMethod("admin", "cn=System Administrator,ou=people,dc=example,dc=net", "otp")
            assert self.manager.getTwoFactorMethod("admin", "cn=System Administrator,ou=people,dc=example,dc=net") == "otp"

            # verify
            with mock.patch("gosa.backend.plugins.two_factor.main.TOTP") as m_totp:
                m_resolver.return_value.check.return_value = False
                with pytest.raises(ACLException):
                    self.manager.verify("admin", "cn=System Administrator,ou=people,dc=example,dc=net", "fake-key")
                m_resolver.return_value.check.return_value = True
                m_totp.return_value.verify.return_value = True
                assert self.manager.verify("admin", "cn=System Administrator,ou=people,dc=example,dc=net", "fake-key") is True
                m_totp.return_value.verify.return_value = False
                assert self.manager.verify("admin", "cn=System Administrator,ou=people,dc=example,dc=net", "fake-key") is False

            # remove the method
            with pytest.raises(ChangingNotAllowed):
                self.manager.setTwoFactorMethod("admin", "cn=System Administrator,ou=people,dc=example,dc=net", "None", "wrongpw")
            assert self.manager.getTwoFactorMethod("admin", "cn=System Administrator,ou=people,dc=example,dc=net") == "otp"

            with pytest.raises(UnknownTwoFAMethod):
                self.manager.setTwoFactorMethod("admin", "cn=System Administrator,ou=people,dc=example,dc=net", "unknown", "tester")
            assert self.manager.getTwoFactorMethod("admin", "cn=System Administrator,ou=people,dc=example,dc=net") == "otp"

            self.manager.setTwoFactorMethod("admin", "cn=System Administrator,ou=people,dc=example,dc=net", "None", "tester")
            assert self.manager.getTwoFactorMethod("admin", "cn=System Administrator,ou=people,dc=example,dc=net") is None
            # should always verify when no 2FA method is used
            assert self.manager.verify("admin", "cn=System Administrator,ou=people,dc=example,dc=net", "fake-key") is True