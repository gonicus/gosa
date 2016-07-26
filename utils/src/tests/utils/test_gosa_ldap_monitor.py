# This file is part of the GOsa project.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

from unittest import mock, TestCase
from gosa.utils import gosa_ldap_monitor


class LdapMonitorTestCase(TestCase):

    def test_main(self):
        handler = mock.MagicMock()
        gosa_ldap_monitor.monitor('/tmp/audit.log', 'modified', handler)
