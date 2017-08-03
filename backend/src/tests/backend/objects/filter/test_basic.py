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

import pytest
from gosa.backend.objects.filter.basic import *


class BasicFilterTests(unittest.TestCase):

    def test_Rename(self):
        filter = Rename(None)
        testDict = {
            "attr1": {"value": [1]},
            "attr2": {"value": [2]}
        }
        fakeObj = mock.MagicMock()
        fakeObj.attributesInSaveOrder = ["attr1", "attr2"]

        (new_key, newDict) = filter.process(fakeObj, "attr1", testDict, "attr3")
        assert newDict['attr3']['value'][0] == 1
        assert newDict['attr2']['value'][0] == 2
        assert 'attr1' not in newDict
        assert "attr1" not in fakeObj.attributesInSaveOrder

    def test_SetBackends(self):
        filter = SetBackends(None)
        testDict = {
            "backends": {
                "backend": ["null"]
            }
        }
        (new_key, newDict) = filter.process(None, "backends", testDict, "ldap", "json")
        assert len(newDict["backends"]["backend"]) == 2
        assert "ldap" in newDict["backends"]["backend"]
        assert "json" in newDict["backends"]["backend"]
        assert "null" not in newDict["backends"]["backend"]

    def test_AddBackend(self):
        filter = AddBackend(None)
        testDict = {
            "backends": {
                "backend": ["null"]
            }
        }
        (new_key, newDict) = filter.process(None, "backends", testDict, "ldap")
        assert len(newDict["backends"]["backend"]) == 2
        assert "ldap" in newDict["backends"]["backend"]
        assert "null" in newDict["backends"]["backend"]

    def test_AddBackend(self):
        filter = AddBackend(None)
        testDict = {
            "backends": {
                "backend": ["null"]
            }
        }
        (new_key, newDict) = filter.process(None, "backends", testDict, "ldap")
        assert len(newDict["backends"]["backend"]) == 2
        assert "ldap" in newDict["backends"]["backend"]
        assert "null" in newDict["backends"]["backend"]

    def test_SetValue(self):
        filter = SetValue(None)
        testDict = {
            "attr": {
                "value": ["test"],
                "type": "String"
            }
        }
        (new_key, newDict) = filter.process(None, "attr", testDict, "123")
        assert "123" in newDict["attr"]["value"]

    def test_Clear(self):
        filter = Clear(None)
        testDict = {
            "attr": {
                "value": ["test"],
                "type": "String"
            }
        }
        (new_key, newDict) = filter.process(None, "attr", testDict)
        assert newDict["attr"]["value"] == ['']

    def test_IntegerToDatetime(self):
        filter = IntegerToDatetime(None)
        # "Tue, 21 Jun 2016 09:41:08"
        testDict = {
            "attr": {
                "value": [1466494868],
                "backend_type": "Integer"
            }
        }
        (new_key, newDict) = filter.process(None, "attr", testDict)
        assert newDict['attr']['backend_type'] == "Timestamp"
        date = list(newDict['attr']['value'])[0]
        assert date.year == 2016
        assert date.month == 6
        assert date.day == 21
        assert date.hour == 9
        assert date.minute == 41
        assert date.second == 8

    def test_DatetimeToInteger(self):
        filter = DatetimeToInteger(None)
        testDict = {
            "attr": {
                "value": [datetime.datetime(2016, 6, 21, 9, 41, 8)],
                "backend_type": "Timestamp"
            }
        }
        (new_key, newDict) = filter.process(None, "attr", testDict)
        assert newDict['attr']['backend_type'] == "Integer"
        assert list(newDict['attr']['value'])[0] == 1466494868

    def test_StringToDatetime(self):
        filter = StringToDatetime(None)
        testDict = {
            "attr": {
                "value": ["2016-06-21"],
                "backend_type": "String"
            }
        }
        (new_key, newDict) = filter.process(None, "attr", testDict, "%Y-%m-%d")
        assert newDict['attr']['backend_type'] == "Timestamp"
        date = list(newDict['attr']['value'])[0]
        assert date.year == 2016
        assert date.month == 6
        assert date.day == 21

    def test_DatetimeToString(self):
        filter = DatetimeToString(None)
        testDict = {
            "attr": {
                "value": [datetime.datetime(2016, 6, 21, 9, 41, 8)],
                "backend_type": "Timestamp"
            }
        }
        (new_key, newDict) = filter.process(None, "attr", testDict, "%Y-%m-%d")
        assert newDict['attr']['backend_type'] == "String"
        assert list(newDict['attr']['value'])[0] == "2016-06-21"