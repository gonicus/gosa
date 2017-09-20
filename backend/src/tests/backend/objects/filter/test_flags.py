# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

import unittest
from unittest import mock
from gosa.backend.objects.filter.flags import *


class FlagsTests(unittest.TestCase):

    def test_UnmarshalFlags(self):
        filter = UnmarshalFlags(None)
        testDict = {
            "attr1": {"value": ["GO"]},
            "isG": {"value": [False]},
            "isO": {"value": [False]}

        }
        fakeObj = mock.MagicMock()
        fakeObj.attributesInSaveOrder = ["attr1", "isG", "isO"]

        (new_key, newDict) = filter.process(fakeObj, "attr1", testDict, "G,O", "isG,isO")
        assert newDict['isG']['value'][0] is True
        assert newDict['isO']['value'][0] is True

        testDict = {
            "attr1": {"value": ["G"]},
            "isG": {"value": [False]},
            "isO": {"value": [False]}
        }

        (new_key, newDict) = filter.process(fakeObj, "attr1", testDict, "G,O", "isG,isO")
        assert newDict['isG']['value'][0] is True
        assert newDict['isO']['value'][0] is False

    def test_MarshalFlags(self):
        filter = MarshalFlags(None)
        testDict = {
            "attr1": {"value": []},
            "isG": {"value": [False]},
            "isO": {"value": [False]}

        }
        fakeObj = mock.MagicMock()
        fakeObj.attributesInSaveOrder = ["attr1", "isG", "isO"]

        (new_key, newDict) = filter.process(fakeObj, "attr1", testDict, "G,O", "isG,isO")
        assert newDict['attr1']['value'] == [""]

        testDict["isG"]["value"][0] = True
        (new_key, newDict) = filter.process(fakeObj, "attr1", testDict, "G,O", "isG,isO")
        assert newDict['attr1']['value'] == ["G"]

        testDict["isO"]["value"][0] = True
        (new_key, newDict) = filter.process(fakeObj, "attr1", testDict, "G,O", "isG,isO")
        assert newDict['attr1']['value'] == ["GO"]
