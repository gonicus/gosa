# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

import unittest
from gosa.backend.objects.filter.strings import *

class StringComparatorTests(unittest.TestCase):

    def test_SplitString(self):
        filter = SplitString(None)
        testDict = {
            "attr": {
                "value": ["This is a test, sentence"],
                "backend_type": "String"
            }
        }
        (new_key, newDict) = filter.process(None, "attr", testDict, ", ")
        assert len(newDict["attr"]["value"]) == 2
        assert newDict["attr"]["value"][0] == "This is a test"
        assert newDict["attr"]["value"][1] == "sentence"

    def test_JoinArray(self):
        filter = JoinArray(None)
        testDict = {
            "attr": {
                "value": ["This is a test", "sentence"],
                "backend_type": "String"
            }
        }
        (new_key, newDict) = filter.process(None, "attr", testDict, ", ")
        assert len(newDict["attr"]["value"]) == 1
        assert newDict["attr"]["value"][0] == "This is a test, sentence"

        testDict = {
            "attr": {
                "value": [],
                "backend_type": "String"
            }
        }
        (new_key, newDict) = filter.process(None, "attr", testDict, ", ")
        assert len(newDict["attr"]["value"]) == 0

    def test_ConcatString(self):
        filter = ConcatString(None)
        testDict = {
            "attr": {
                "value": ["This is a test"],
                "backend_type": "String"
            }
        }
        (new_key, newDict) = filter.process(None, "attr", testDict, " sentence", "right")
        values = list(newDict["attr"]["value"])
        assert len(values) == 1
        assert values[0] == "This is a test sentence"

        testDict = {
            "attr": {
                "value": ["This is a test"],
                "backend_type": "String"
            }
        }
        (new_key, newDict) = filter.process(None, "attr", testDict, "sentence ", "left")
        values = list(newDict["attr"]["value"])
        assert len(values) == 1
        assert values[0] == "sentence This is a test"

    def test_Replace(self):
        filter = Replace(None)
        testDict = {
            "attr": {
                "value": ["This {is} a test"],
                "backend_type": "String"
            }
        }
        (new_key, newDict) = filter.process(None, "attr", testDict, "{([^}]+)}", "\\1/was")
        values = list(newDict["attr"]["value"])
        assert len(values) == 1
        assert values[0] == "This is/was a test"

    def test_DateToString(self):
        filter = DateToString(None)
        testDict = {
            "attr": {
                "value": [datetime.datetime(2016, 6, 21, 9, 41, 8)],
                "backend_type": "Timestamp"
            }
        }
        (new_key, newDict) = filter.process(None, "attr", testDict, "%Y-%m-%d")
        assert list(newDict["attr"]["value"])[0] == "2016-06-21"

    def test_TimeToString(self):
        filter = TimeToString(None)
        testDict = {
            "attr": {
                "value": [datetime.datetime(2016, 6, 21, 9, 41, 8)],
                "backend_type": "Timestamp"
            }
        }
        (new_key, newDict) = filter.process(None, "attr", testDict, "%H:%M:%S")
        assert list(newDict["attr"]["value"])[0] == "09:41:08"

    def test_StringToDate(self):
        filter = StringToDate(None)
        testDict = {
            "attr": {
                "value": ["2016-06-21"]
            }
        }
        (new_key, newDict) = filter.process(None, "attr", testDict, "%Y-%m-%d")
        date = list(newDict['attr']['value'])[0]
        assert date.year == 2016
        assert date.month == 6
        assert date.day == 21

    def test_StringToTime(self):
        filter = StringToTime(None)
        testDict = {
            "attr": {
                "value": ["09:41:08"]
            }
        }
        (new_key, newDict) = filter.process(None, "attr", testDict, "%H:%M:%S")
        date = list(newDict['attr']['value'])[0]
        assert date.hour == 9
        assert date.minute == 41
        assert date.second == 8