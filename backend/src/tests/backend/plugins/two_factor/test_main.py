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
        self.env = Environment.getInstance()
        assert self.env.config.get("user.2fa-store").startswith("/tmp")
        os.remove(self.env.config.get("user.2fa-store"))
        self.manager = PluginRegistry.getInstance("TwoFactorAuthManager")

    def test_getAvailable2FAMethods(self):
        methods = self.manager.getAvailable2FAMethods("admin")
        assert None in methods
        assert 'otp' in methods
        assert 'u2f' in methods

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

    def test_U2FMethod(self):
        with mock.patch("gosa.backend.plugins.two_factor.main.PluginRegistry.getInstance") as m_resolver:
            m_resolver.return_value.check.return_value = False
            with pytest.raises(ACLException):
                self.manager.getTwoFactorMethod("admin", "cn=System Administrator,ou=people,dc=example,dc=net")

            m_resolver.return_value.check.return_value = True
            assert self.manager.getTwoFactorMethod("admin", "cn=System Administrator,ou=people,dc=example,dc=net") is None

            # change the settings
            m_resolver.return_value.check.return_value = False
            with pytest.raises(ACLException):
                self.manager.setTwoFactorMethod("admin", "cn=System Administrator,ou=people,dc=example,dc=net", "u2f")
            m_resolver.return_value.check.return_value = True
            assert self.manager.getTwoFactorMethod("admin", "cn=System Administrator,ou=people,dc=example,dc=net") is None

            res = loads(self.manager.setTwoFactorMethod("admin", "cn=System Administrator,ou=people,dc=example,dc=net", "u2f"))

            # still none as we are not done yet
            assert self.manager.getTwoFactorMethod("admin", "cn=System Administrator,ou=people,dc=example,dc=net") is None

            assert 'registerRequests' in res
            assert len(res['registerRequests']) == 1

            # proceed with some fake data
            fake_response = {"clientData": "eyJvcmlnaW4iOiAiaHR0cDovL2xvY2FsaG9zdDo4MDgxIiwgImNoYWxsZW5nZSI6ICJEMnB6VFBaYTdicTY5QUJ1aUdRSUxvOXpjc1RVUlAyNlJMaWZUeUNraWxjIiwgInR5cCI6ICJuYXZpZ2F0b3IuaWQuZmluaXNoRW5yb2xsbWVudCJ9", "registrationData": "BQSivQtJ6-lAgZ2qQ0aUGLEiJSRoLWUSGcmMO8C-GuibA0-xTvmuQfTqKyFJZWOUjGzEIgF4xV6gJ6itcagsyuUWQEQh9noDSu-WtzTOMhK_lKHxwHtQgJHCkzs4mukfpf310K5Dq9k6zBNtZ2RMBWgJhI7hJo4JiFn3k2GUNLwKZpwwggGHMIIBLqADAgECAgkAmb7osQyi7BwwCQYHKoZIzj0EATAhMR8wHQYDVQQDDBZZdWJpY28gVTJGIFNvZnQgRGV2aWNlMB4XDTEzMDcxNzE0MjEwM1oXDTE2MDcxNjE0MjEwM1owITEfMB0GA1UEAwwWWXViaWNvIFUyRiBTb2Z0IERldmljZTBZMBMGByqGSM49AgEGCCqGSM49AwEHA0IABDvhl91zfpg9n7DeCedcQ8gGXUnemiXoi-JEAxz-EIhkVsMPAyzhtJZ4V3CqMZ-MOUgICt2aMxacMX9cIa8dgS2jUDBOMB0GA1UdDgQWBBQNqL-TV04iaO6mS5tjGE6ShfexnjAfBgNVHSMEGDAWgBQNqL-TV04iaO6mS5tjGE6ShfexnjAMBgNVHRMEBTADAQH_MAkGByqGSM49BAEDSAAwRQIgXJWZdbvOWdhVaG7IJtn44o21Kmi8EHsDk4cAfnZ0r38CIQD6ZPi3Pl4lXxbY7BXFyrpkiOvCpdyNdLLYbSTbvIBQOTBFAiEA1uwJKNez6_BHdA2d-DPmRFJj19biYNkhN86SFH5Z_lYCICld2L3ZAVsm_uNFRt13_N9dlhGu50pb1ql8-_3_p5v1"}
            m_resolver.return_value.check.return_value = False
            with pytest.raises(ACLException):
                self.manager.completeU2FRegistration("admin", "cn=System Administrator,ou=people,dc=example,dc=net", fake_response)
            m_resolver.return_value.check.return_value = True
            assert self.manager.getTwoFactorMethod("admin", "cn=System Administrator,ou=people,dc=example,dc=net") is None


            fake_device = {"keyHandle": "fake-key-handle",
                           "appId": self.env.config.get("jsonrpc.url")}
            binding = mock.MagicMock()
            binding.json = dumps(fake_device)
            with mock.patch("gosa.backend.plugins.two_factor.main.complete_register", return_value=(binding, mock.MagicMock())):
                self.manager.completeU2FRegistration("admin", "cn=System Administrator,ou=people,dc=example,dc=net", fake_response)

            assert self.manager.getTwoFactorMethod("admin", "cn=System Administrator,ou=people,dc=example,dc=net") == "u2f"

            # sign
            m_resolver.return_value.check.return_value = False
            with pytest.raises(ACLException):
                self.manager.sign("admin", "cn=System Administrator,ou=people,dc=example,dc=net")

            m_resolver.return_value.check.return_value = True
            res = loads(self.manager.sign("admin", "cn=System Administrator,ou=people,dc=example,dc=net"))

            assert 'authenticateRequests' in res
            assert len(res['authenticateRequests']) == 1

            fake_response = {"clientData": "eyJvcmlHR0cDovL2xvY2FsaG9zdDo4MDgxIiwgImNoYWxsZW5nZSI6ICJlNGtScWk3eTdmUHdtZGZ1RnJ5WkxyVUhYby1BdF91YUFwWHdxdkV2UmxzIiwgInR5cCI6ICJuYXZpZ2F0b3IuaWQuZ2V0QXNzZXJ0aW9uIn0", "challenge": "e4kRqi7y7fPwmdfuFryZLrUHXo-At_uaApXwqvEvRls", "keyHandle": "RCH2egNK75a3NM4yEr-UofHAe1CAkcKTOzia6R-l_fXQrkOr2TrME21nZEwFaAmEjuEmjgmIWfeTYZQ0vApmnA", "signatureData": "AQAAAAIwRQIhAIyr0y4xg-pI8NhAUHJmaluGXwZ7yd5i0e7FQE4l9OaEAiB68JP-df7ro8ohxCcgyxfRiKrsY1J67kLcEuYb0MCrDg"}

            # verify
            m_resolver.return_value.check.return_value = False
            with pytest.raises(ACLException):
                self.manager.verify("admin", "cn=System Administrator,ou=people,dc=example,dc=net", fake_response)

            m_resolver.return_value.check.return_value = True
            with mock.patch("gosa.backend.plugins.two_factor.main.verify_authenticate", return_value=(2, "1")):
                assert self.manager.verify("admin", "cn=System Administrator,ou=people,dc=example,dc=net", fake_response) == {"touch": "1",
                                                                                                                              "counter": 2}

            # remove the method
            with pytest.raises(ChangingNotAllowed):
                self.manager.setTwoFactorMethod("admin", "cn=System Administrator,ou=people,dc=example,dc=net", "None", "wrongpw")
            assert self.manager.getTwoFactorMethod("admin", "cn=System Administrator,ou=people,dc=example,dc=net") == "u2f"

            with pytest.raises(UnknownTwoFAMethod):
                self.manager.setTwoFactorMethod("admin", "cn=System Administrator,ou=people,dc=example,dc=net", "unknown", "tester")
            assert self.manager.getTwoFactorMethod("admin", "cn=System Administrator,ou=people,dc=example,dc=net") == "u2f"

            self.manager.setTwoFactorMethod("admin", "cn=System Administrator,ou=people,dc=example,dc=net", "None", "tester")
            assert self.manager.getTwoFactorMethod("admin", "cn=System Administrator,ou=people,dc=example,dc=net") is None
            # should always verify when no 2FA method is used
            assert self.manager.verify("admin", "cn=System Administrator,ou=people,dc=example,dc=net", "fake-key") is True