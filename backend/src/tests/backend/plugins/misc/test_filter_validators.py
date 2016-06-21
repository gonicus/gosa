# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

import unittest
from gosa.backend.plugins.misc.filter_validators import *


#TODO: write tests for other filters when ObjectIndex is working again
class FilterValidatorTests(unittest.TestCase):

    def test_IsValidHostName(self):
        filter = IsValidHostName(None)
        (res, errors) = filter.process(None, None, ["www.gonicus.de"])
        assert res == True
        assert len(errors) == 0

        (res, errors) = filter.process(None, None, ["1www.gonicus.de"])
        assert res == False
        assert len(errors) == 1