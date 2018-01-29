# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.
from unittest import TestCase

import pytest

from gosa.backend.objects import ObjectProxy
from gosa.common.components import PluginRegistry

slow = pytest.mark.skipif(
    not pytest.config.getoption("--runslow"),
    reason="need --runslow option to run"
)


class GosaTestCase(TestCase):
    _test_dn = None

    @staticmethod
    def create_test_data():
        """
        Insert new data just for testing purposes
        """
        index = PluginRegistry.getInstance("ObjectIndex")
        res = index.search({"dn": "dc=test,dc=example,dc=net"}, {"dn": 1})
        if len(res) > 0:
            new_domain = ObjectProxy("dc=test,dc=example,dc=net")
            new_domain.remove(True)

        new_domain = ObjectProxy("dc=example,dc=net", "DomainComponent")
        new_domain.dc = "test"
        new_domain.description = "Domain for testing purposes"
        new_domain.commit()
        return "dc=test,dc=example,dc=net"

    @staticmethod
    def remove_test_data(dn):
        if dn is not None:
            new_domain = ObjectProxy(dn)
            new_domain.remove(True)

    def _create_test_data(self):
        self._test_dn = GosaTestCase.create_test_data()

    def tearDown(self):
        super(GosaTestCase, self).tearDown()
        if self._test_dn is not None:
            GosaTestCase.remove_test_data(self._test_dn)
            self._test_dn = None
