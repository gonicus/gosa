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
from gosa.backend.plugins.posix.filters import *
from gosa.backend.objects.backend.back_null import NULL

class PosixFiltersTestCase(unittest.TestCase):

    def setUp(self):
        self.id = 1000
        def get_next_id(name):
            return self.id
        self.backend = NULL()
        self.backend.get_next_id = get_next_id


    @unittest.mock.patch.object(ObjectBackendRegistry,'getBackend')
    def test_GenerateIDs(self, mockedGetBackend):
        mockedGetBackend.return_value = self.backend

        filter = GenerateIDs(None)
        testDict = {
            "uidNumber": {
                "value": [],
                "backend": ["NULL"]
            }
        }

        with pytest.raises(PosixException):
            filter.process(None, None, testDict, 1, "test")

        # too many backends
        testDict["uidNumber"]["backend"] = ["NULL", "ldap"]
        with pytest.raises(PosixException):
            filter.process(None, None, testDict)

        testDict["uidNumber"]["backend"] = ["NULL"]

        (key, valDict) = filter.process(None, None, testDict)
        assert valDict["uidNumber"]["value"] == [1000]
        valDict["uidNumber"]["value"] = []

        # > maxId
        with pytest.raises(PosixException):
            print(filter.process(None, None, testDict, "10", "10"))

        # same tests for gidNumber
        testDict = {
            "gidNumber": {
                "value": [],
                "backend": ["NULL"]
            }
        }

        with pytest.raises(PosixException):
            filter.process(None, None, testDict, "test", 2)

        # too many backends
        testDict["gidNumber"]["backend"] = ["NULL", "ldap"]
        with pytest.raises(PosixException):
            filter.process(None, None, testDict)

        testDict["gidNumber"]["backend"] = ["NULL"]

        (key, valDict) = filter.process(None, None, testDict)
        assert valDict["gidNumber"]["value"] == [1000]
        valDict["gidNumber"]["value"] = []

        # > maxId
        with pytest.raises(PosixException):
            filter.process(None, None, testDict, "10", "10")

    @unittest.mock.patch.object(GenerateGecos, 'generateGECOS')
    def test_LoadGecosState(self, mock):
        mock.return_value = 'Test'
        filter = LoadGecosState(None)
        testDict = {
            "gecos": {
                "value": []
            },
            "autoGECOS": {
                "value": [False]
            }
        }

        (key, valDict) = filter.process(None, "autoGECOS", testDict)
        assert valDict['gecos']['value'] == []
        assert valDict['autoGECOS']['value'] == [True]

        testDict['gecos']['value'] = ['Test']
        testDict['autoGECOS']['value'] = [False]
        (key, valDict) = filter.process(None, "autoGECOS", testDict)
        assert valDict['gecos']['value'] == ['Test']
        assert valDict['autoGECOS']['value'] == [True]

        testDict['gecos']['value'] = ['Test1']
        (key, valDict) = filter.process(None, "autoGECOS", testDict)
        assert valDict['gecos']['value'] == ['Test1']
        assert valDict['autoGECOS']['value'] == [False]

    def test_GenerateGecos(self):
        filter = GenerateGecos(None)
        testDict = {
            "gecos": {
                "value": []
            },
            "autoGECOS": {
                "value": [False]
            },
            "sn": {
                "value": ["Max"]
            },
            "givenName":{
                "value": ["Tester"]
            },
            "homePhone":{
                "value": ["0"]
            },
            "telephoneNumber":{
                "value": ["1"]
            },
            "ou": {
                "value": ["2"]
            }
        }

        (key, valDict) = filter.process(None, "autoGECOS", testDict)
        assert valDict['gecos']['value'] == []

        testDict['autoGECOS']['value'] = [True]
        (key, valDict) = filter.process(None, "autoGECOS", testDict)
        assert valDict['gecos']['value'] == ['Max Tester,2,1,0']

    @unittest.mock.patch.object(ObjectBackendRegistry, 'getBackend')
    def test_GetNextId(self, mockedGetBackend):
        mockedGetBackend.return_value = self.backend
        filter = GetNextID(None)
        testDict = {
            "attr": {
                "value": [-1],
                "backend": ["NULL"]
            }
        }

        (key, valDict) = filter.process(None, "attr", testDict)
        assert valDict["attr"]["value"] == [1000]

        valDict["attr"]["value"] = [-1]
        # too many backends
        testDict["attr"]["backend"] = ["NULL", "ldap"]
        with pytest.raises(PosixException):
            filter.process(None, "attr", testDict)

        # > maxId
        testDict["attr"]["backend"] = ["NULL"]
        with pytest.raises(PosixException):
            print(filter.process(None, "attr", testDict, "uidNumber", "10"))