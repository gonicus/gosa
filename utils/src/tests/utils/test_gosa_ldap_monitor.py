# This file is part of the GOsa project.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.
from base64 import b64encode
from unittest import mock, TestCase

from gosa.utils.gosa_ldap_monitor import *


class LdapMonitorTestCase(TestCase):

    def test_main(self):

        lines = [
            "dn:base",
            "changetype:modify",
            "modifiersName:other",
            "modifyTimestamp:%s" % datetime.now().strftime("%Y%m%d%H%M%SZ"),
            ""
        ]
        env = Environment.getInstance()
        webhook_target = env.config.get('backend-monitor.webhook-target', default='http://localhost:8000/hooks/')
        token = bytes(env.config.get('backend-monitor.webhook-token'), 'ascii')
        m_open = mock.mock_open()
        with mock.patch("gosa.utils.gosa_ldap_monitor.open", m_open, create=True),\
                mock.patch("gosa.utils.gosa_ldap_monitor.tail", return_value=lines) as m_tail,\
                mock.patch("gosa.utils.gosa_ldap_monitor.requests.post") as m_post:
            monitor('/tmp/audit.log', 'other', token, webhook_target)
            assert not m_post.called

            monitor('/tmp/audit.log', 'gosa-backend', token, webhook_target)
            assert m_post.called

            m_post.reset_mock()
            m_tail.return_value = [
                "dn::%s" % b64encode(b"base"),
                "changetype:modify",
                "modifiersName:other",
                ""
            ]
            monitor('/tmp/audit.log', 'gosa-backend', token, webhook_target)
            assert m_post.called