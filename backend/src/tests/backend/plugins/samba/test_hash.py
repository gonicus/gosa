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
from gosa.backend.plugins.samba.hash import *

class SambaHashTestCase(unittest.TestCase):

    def test_SambaHash(self):
        filter = SambaHash(None)
        testDict = {
            "password": {
                "value": ["test"]
            },
            "sambaNTPassword": {
                "value": []
            },
            "sambaLMPassword": {
                "value": []
            }
        }
        (key, valDict) = filter.process(None, "password", testDict)
        assert valDict['sambaNTPassword']['value'][0] == "0cb6948805f797bf2a82807973b89537"
        assert valDict['sambaLMPassword']['value'][0] == "01fc5a6be7bc6929aad3b435b51404ee"

        testDict["password"]["value"] = [True]
        with pytest.raises(ValueError):
            filter.process(None, "password", testDict)