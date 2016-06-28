import unittest
import pytest
from gosa.backend.objects.types.acl_set import *


class AclSetTestCase(unittest.TestCase):

    def setUp(self):
        self.type = AclSet()

    def test_is_valid_value(self):
        assert self.type.is_valid_value([{}]) is True
        assert self.type.is_valid_value([True]) is False

    def test_values_match(self):
        assert self.type.values_match(False,False) is True
        assert self.type.values_match(False, True) is False

    def test__convert_to_unicodestring(self):
        testDict={
            "priority": "high",
            "scope": "local",
            "actions":[
                {"topic":"topic", "acl":"acl", "options":{}}
            ]
        }
        assert self.type._convert_to_unicodestring([]) == []
        assert self.type._convert_to_unicodestring([testDict]) == ["local\nhigh\n\n\ntopic:acl:{}"]

        testDict['rolename'] = "role"
        testDict['members']= ["1","2"]
        assert self.type._convert_to_unicodestring([testDict]) == ["\nhigh\n1,2\nrole"]

    def test__convert_from_unicodestring(self):
        assert self.type._convert_from_unicodestring(["local\nhigh\n\n\ntopic:acl:{}"]) == [{
            "priority": "high",
            "scope": "local",
            "actions": [
                {"topic": "topic", "acl": "acl", "options": {}}
            ],
            "members": []
        }]

        assert self.type._convert_from_unicodestring(["\nhigh\n1,2\nrole"]) == [{
            "priority": "high",
            "members": ["1","2"],
            "rolename": "role"
        }]

        assert self.type._convert_from_string(["\nhigh\n1,2\nrole"]) == [{
            "priority": "high",
            "members": ["1", "2"],
            "rolename": "role"
        }]


