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

slow = pytest.mark.skipif(
    not pytest.config.getoption("--runslow"),
    reason="need --runslow option to run"
)


class GosaTestCase(TestCase):
    _test_dn = None

    def _create_test_data(self):
        """
        Insert new data just for testing purposes
        """
        try:
            new_domain = ObjectProxy("dc=test,dc=example,dc=net")
            new_domain.remove(True)
            new_domain.commit()
        except:
            pass

        new_domain = ObjectProxy("dc=example,dc=net", "DomainComponent")
        new_domain.dc = "test"
        new_domain.description = "Domain for testing purposes"
        new_domain.commit()
        self._test_dn = "dc=test,dc=example,dc=net"

    def tearDown(self):
        super(GosaTestCase, self).tearDown()
        if self._test_dn is not None:
            try:
                new_domain = ObjectProxy("dc=test,dc=example,dc=net")
                new_domain.remove(True)
                new_domain.commit()
                self._test_dn = None
            except Exception as e:
                print(str(e))
