# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

import pytest
from unittest import TestCase, mock
from gosa.backend.utils.ldap import LDAPHandler, map_ldap_value, normalize_ldap, check_auth
from gosa.common import Environment
from gosa.backend.exceptions import LDAPException
import ldap


class LDAPHandlerTestCase(TestCase):

    def test_init(self):
        env = Environment.getInstance()

        def get_conf(key, default=None):
            if key == "ldap.bind-user":
                return "user"
            else:
                return env.config.get(key, default)

        with mock.patch("gosa.backend.utils.ldap.Environment.getInstance") as m_env,\
                mock.patch("gosa.backend.utils.ldap.ldap") as m_ldap,\
                pytest.raises(LDAPException):
            m_env.return_value.config.get.side_effect = get_conf
            m_ldap.SASL_AVAIL = False
            LDAPHandler()

    def test_get_connection(self):
        handler = LDAPHandler()
        with pytest.raises(LDAPException),\
                mock.patch("gosa.backend.utils.ldap.LDAPHandler.connection_usage", new_callable=mock.PropertyMock, return_value=[True]):
            handler.get_connection()
        del handler

        ldap_url = Environment.getInstance().config.get("ldap.url")
        retry_max = 3
        retry_delay = 5
        tls = "False"
        with mock.patch("gosa.backend.utils.ldap.Environment.getInstance") as m_env, \
                mock.patch("gosa.backend.utils.ldap.ldap.ldapobject.ReconnectLDAPObject") as m_conn:
            # ldap.url, bind-user, bind-dn, bind-secret, pool-size, retry-max, retry-delay, tls
            m_env.return_value.config.get.side_effect = [ldap_url, 'admin', None, 'secret', 10, retry_max, retry_delay, tls]
            handler = LDAPHandler()
            handler.get_connection()
            assert m_conn.return_value.sasl_interactive_bind_s.called
            del handler

            m_env.return_value.config.get.side_effect = [ldap_url, None, "bind-dn", 'secret', 10, retry_max, retry_delay, tls]
            handler = LDAPHandler()
            handler.get_connection()
            m_conn.return_value.simple_bind_s.assert_called_with("bind-dn", "secret")
            del handler

            m_env.return_value.config.get.side_effect = [ldap_url, None, None, None, 10, retry_max, retry_delay, tls]
            handler = LDAPHandler()
            handler.get_connection()
            m_conn.return_value.simple_bind_s.assert_called_with()
            del handler

            m_conn.reset_mock()

            m_env.return_value.config.get.side_effect = [ldap_url, None, None, None, 10, retry_max, retry_delay, tls]
            m_conn.return_value.simple_bind_s.side_effect = ldap.INVALID_CREDENTIALS("test error")
            handler = LDAPHandler()
            with mock.patch.object(handler, "log") as m_log:
                handler.get_connection()
                assert m_log.error.called
            del handler

    def test_get_base(self):
        handler = LDAPHandler()
        con = handler.get_connection()
        assert handler.get_base() == "dc=example,dc=net"
        handler.free_connection(con)


def test_map_ldap_value():
    assert map_ldap_value(True) == "TRUE"
    assert map_ldap_value(False) == "FALSE"
    assert list(map_ldap_value(["Test", True, False])) == ["Test", "TRUE", "FALSE"]


def test_normalize_ldap():
    assert normalize_ldap(True) == [True]
    assert normalize_ldap("Test") == ["Test"]
    assert normalize_ldap(["Test", True, False]) == ["Test", True, False]


def test_check_auth():
    ldap_url = Environment.getInstance().config.get("ldap.url")
    retry_max = 3
    retry_delay = 5
    tls = "False"

    with mock.patch("gosa.backend.utils.ldap.Environment.getInstance") as m_env, \
            mock.patch("gosa.backend.utils.ldap.ldap.ldapobject.ReconnectLDAPObject") as m_conn:
        # ldap.url, bind-user, bind-dn, bind-secret, retry-max, retry-delay, tls
        m_env.return_value.config.get.side_effect = [ldap_url, 'admin', None, 'secret', retry_max, retry_delay, tls]
        m_conn.return_value.search_s.return_value = [('fake-dn',)]
        assert check_auth("admin", "tester") is True
        assert m_conn.return_value.sasl_interactive_bind_s.called

        m_env.return_value.config.get.side_effect = [ldap_url, None, "bind-dn", 'secret', retry_max, retry_delay, tls]
        m_conn.return_value.search_s.return_value = [('fake-dn',), ('2nd-dn',)]
        assert check_auth("admin", "tester") is False
        m_conn.return_value.simple_bind_s.assert_called_with("bind-dn", "secret")

        m_env.return_value.config.get.side_effect = [ldap_url, None, None, None, retry_max, retry_delay, tls]
        m_conn.return_value.search_s.return_value = []
        assert check_auth("admin", "tester") is False
        m_conn.return_value.simple_bind_s.assert_called_with()

        m_env.return_value.config.get.side_effect = [ldap_url, None, None, None, retry_max, retry_delay, tls]
        m_conn.return_value.search_s.side_effect = ldap.INVALID_CREDENTIALS("test error")
        assert check_auth("admin", "tester") is False
        m_conn.return_value.simple_bind_s.assert_called_with()