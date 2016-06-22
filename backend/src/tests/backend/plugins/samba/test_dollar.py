# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

import unittest
import pytest
from gosa.backend.plugins.samba.dollar import *
# import the error code
import gosa.backend.plugins.samba.hash

class SambaDollarTestCase(unittest.TestCase):

    def test_SambaDollarFilterOut(self):
        filter = SambaDollarFilterOut(None)
        testDict = {
            "attr": {
                "value": ["test"],
                "backend": ["NULL"]
            }
        }
        (key, valDict) = filter.process(None, "attr", testDict)
        assert valDict['attr']['value'] == ["test$"]

        # again to make sure that it is not appended twice
        (key, valDict) = filter.process(None, "attr", testDict)
        assert valDict['attr']['value'] == ["test$"]

        valDict['attr']['value'] = [True]
        with pytest.raises(ValueError):
            filter.process(None, "attr", testDict)

    def test_SambaDollarFilterIn(self):
        filter = SambaDollarFilterIn(None)
        testDict = {
            "attr": {
                "value": ["test$"],
                "backend": ["NULL"]
            }
        }
        (key, valDict) = filter.process(None, "attr", testDict)
        assert valDict['attr']['value'] == ["test"]

        valDict['attr']['value'] = [True]
        with pytest.raises(ValueError):
            filter.process(None, "attr", testDict)