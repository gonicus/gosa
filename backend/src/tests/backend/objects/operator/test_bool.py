# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

import unittest
from gosa.backend.objects.operator.bool import *

class BoolComparatorTests(unittest.TestCase):

    def test_and(self):
        op = And()
        assert op.process(True, True) == True
        assert op.process(True, False) == False
        assert op.process(False, False) == False
        assert op.process(False, True) == False


    def test_Or(self):
        op = Or()
        assert op.process(True, True) == True
        assert op.process(True, False) == True
        assert op.process(False, False) == False
        assert op.process(False, True) == True

    def test_not(self):
        op = Not()
        assert op.process(True) == False
        assert op.process(False) == True