# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

import unittest
import sys
import pytest
from gosa.backend.plugins.posix.shells import *

class ShellSupportTestCase(unittest.TestCase):

    @pytest.mark.skipif(sys.platform == 'win32',
                        reason="does not run on windows")
    def test_ShellSupport(self):
        shells = ShellSupport()

        res = shells.getShellList()
        assert len(res) > 0
        assert '/bin/bash' in res