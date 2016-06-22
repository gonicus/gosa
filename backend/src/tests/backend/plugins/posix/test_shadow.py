# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

import unittest
from gosa.backend.plugins.posix.shadow import *

class PosixShadowTestCase(unittest.TestCase):

    def test_ShadowDaysToDatetime(self):
        filter = ShadowDaysToDatetime(None)
        testDict = {
            "attr": {
                "value": [10]
            }
        }
        (key, valDict) = filter.process(None, "attr", testDict)
        date = list(valDict['attr']['value'])[0]
        assert date.year == 1970
        assert date.month == 1
        assert date.day == 11
        assert valDict['attr']['backend_type'] == 'Integer'

    def test_DatetimeToShadowDays(self):
        filter = DatetimeToShadowDays(None)
        testDict = {
            "attr": {
                "value": [datetime.datetime(1970, 1, 11)]
            }
        }
        (key, valDict) = filter.process(None, "attr", testDict)
        assert list(valDict['attr']['value']) == [10]