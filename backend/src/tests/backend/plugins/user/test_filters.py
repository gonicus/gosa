# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

import unittest
from gosa.backend.plugins.user.filters import *

class UserFiltersTestCase(unittest.TestCase):

    # def test_ImageProcessor(self):
    #     filter = ImageProcessor(None)


    def test_LoadDisplayNameState(self):
        filter = LoadDisplayNameState(None)
        testDict = {
            "displayName": {
                "value": []
            },
            "autoDisplayName": {
                "value": [False]
            },
            "sn": {
                "value": ["Surname"]
            },
            "givenName": {
                "value": ["Givenname"]
            }
        }

        (key, valDict) = filter.process(None, "autoDisplayName", testDict.copy())
        assert valDict['autoDisplayName']['value'][0] == True

        testDict["displayName"]["value"] = ["Givenname Surname"]
        (key, valDict) = filter.process(None, "autoDisplayName", testDict.copy())
        assert valDict['autoDisplayName']['value'][0] == True

        testDict["displayName"]["value"] = ["Other name"]
        (key, valDict) = filter.process(None, "autoDisplayName", testDict.copy())
        assert valDict['autoDisplayName']['value'][0] == False

    def test_GenerateDisplayName(self):
        filter = GenerateDisplayName(None)
        testDict = {
            "displayName": {
                "value": []
            },
            "autoDisplayName": {
                "value": [False]
            },
            "sn": {
                "value": ["Surname"]
            },
            "givenName": {
                "value": ["Givenname"]
            }
        }

        (key, valDict) = filter.process(None, None, testDict.copy())
        assert valDict['displayName']['value'] == []

        testDict["autoDisplayName"]["value"] = [True]
        (key, valDict) = filter.process(None, None, testDict.copy())
        assert valDict['displayName']['value'][0] == "Givenname Surname"