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
from gosa.backend.plugins.samba.munged import *

class SambaHashTestCase(unittest.TestCase):

    def test_SambaMungedDialIn(self):
        filter = SambaMungedDialIn(None)
        testDict = {
            "munged": {
                "value": ["IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAUAAQABoACAABAEMAdAB4AEMAZgBnAFAAcgBlAHMAZQBuAHQANTUxZTBiYjAYAAgAAQBDAHQAeABDAGYAZwBGAGwAYQBnAHMAMQAwMGUwMDAxMBYAAAABAEMAdAB4AEMAYQBsAGwAYgBhAGMAawASAAgAAQBDAHQAeABTAGgAYQBkAG8AdwAwMTAwMDAwMCIAAAABAEMAdAB4AEsAZQB5AGIAbwBhAHIAZABMAGEAeQBvAHUAdAAqAAIAAQBDAHQAeABNAGkAbgBFAG4AYwByAHkAcAB0AGkAbwBuAEwAZQB2AGUAbAAwMCAAAgABAEMAdAB4AFcAbwByAGsARABpAHIAZQBjAHQAbwByAHkAMDAgAAIAAQBDAHQAeABOAFcATABvAGcAbwBuAFMAZQByAHYAZQByADAwGAACAAEAQwB0AHgAVwBGAEgAbwBtAGUARABpAHIAMDAiAAIAAQBDAHQAeABXAEYASABvAG0AZQBEAGkAcgBEAHIAaQB2AGUAMDAgAAIAAQBDAHQAeABXAEYAUAByAG8AZgBpAGwAZQBQAGEAdABoADAwIgACAAEAQwB0AHgASQBuAGkAdABpAGEAbABQAHIAbwBnAHIAYQBtADAwIgACAAEAQwB0AHgAQwBhAGwAbABiAGEAYwBrAE4AdQBtAGIAZQByADAwKAAIAAEAQwB0AHgATQBhAHgAQwBvAG4AbgBlAGMAdABpAG8AbgBUAGkAbQBlADAwMDAwMDAwLgAIAAEAQwB0AHgATQBhAHgARABpAHMAYwBvAG4AbgBlAGMAdABpAG8AbgBUAGkAbQBlADAwMDAwMDAwHAAIAAEAQwB0AHgATQBhAHgASQBkAGwAZQBUAGkAbQBlADAwMDAwMDAw"]
            },
            'oldStorageBehavior': {
                "value": []
            },
            'CtxCallback': {
                "value": []
            },
            'CtxCallbackNumber': {
                "value": []
            },
            'CtxCfgFlags1': {
                "value": []
            },
            'CtxCfgPresent': {
                "value": []
            },
            'CtxInitialProgram': {
                "value": []
            },
            'CtxKeyboardLayout': {
                "value": []
            },
            'CtxMaxConnectionTime': {
                "value": []
            },
            'CtxMaxDisconnectionTime': {
                "value": []
            },
            'CtxMaxIdleTime': {
                "value": []
            },
            'CtxMinEncryptionLevel': {
                "value": []
            },
            'CtxNWLogonServer': {
                "value": []
            },
            'CtxShadow': {
                "value": []
            },
            'CtxWFHomeDir': {
                "value": []
            },
            'CtxWFHomeDirDrive': {
                "value": []
            },
            'CtxWFProfilePath': {
                "value": []
            },
            'CtxWorkDirectory': {
                "value": []
            },
            'Ctx_flag_brokenConn': {
                "value": []
            },
            'Ctx_flag_connectClientDrives': {
                "value": []
            },
            'Ctx_flag_connectClientPrinters': {
                "value": []
            },
            'Ctx_flag_defaultPrinter': {
                "value": []
            },
            'Ctx_flag_inheritMode': {
                "value": []
            },
            'Ctx_flag_reConn': {
                "value": []
            },
            'Ctx_shadow': {
                "value": []
            },
            'Ctx_flag_tsLogin': {
                "value": []
            }
        }
        testDict["munged"]["value"] = ["IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAUAAQABoACAABAEMAdAB4AEMAZgBnAFAAcgBlAHMAZQBuAHQANTUxZTBiYjAYAAgAAQBDAHQAeABDAGYAZwBGAGwAYQBnAHMAMQAwMGUwMDAxMBYAAAABAEMAdAB4AEMAYQBsAGwAYgBhAGMAawASAAgAAQBDAHQAeABTAGgAYQBkAG8AdwAwMTAwMDAwMCIAAAABAEMAdAB4AEsAZQB5AGIAbwBhAHIAZABMAGEAeQBvAHUAdAAqAAIAAQBDAHQAeABNAGkAbgBFAG4AYwByAHkAcAB0AGkAbwBuAEwAZQB2AGUAbAAwMCAAAgABAEMAdAB4AFcAbwByAGsARABpAHIAZQBjAHQAbwByAHkAMDAgAAIAAQBDAHQAeABOAFcATABvAGcAbwBuAFMAZQByAHYAZQByADAwGAACAAEAQwB0AHgAVwBGAEgAbwBtAGUARABpAHIAMDAiAAIAAQBDAHQAeABXAEYASABvAG0AZQBEAGkAcgBEAHIAaQB2AGUAMDAgAAIAAQBDAHQAeABXAEYAUAByAG8AZgBpAGwAZQBQAGEAdABoADAwIgACAAEAQwB0AHgASQBuAGkAdABpAGEAbABQAHIAbwBnAHIAYQBtADAwIgACAAEAQwB0AHgAQwBhAGwAbABiAGEAYwBrAE4AdQBtAGIAZQByADAwKAAIAAEAQwB0AHgATQBhAHgAQwBvAG4AbgBlAGMAdABpAG8AbgBUAGkAbQBlADAwMDAwMDAwLgAIAAEAQwB0AHgATQBhAHgARABpAHMAYwBvAG4AbgBlAGMAdABpAG8AbgBUAGkAbQBlADAwMDAwMDAwHAAIAAEAQwB0AHgATQBhAHgASQBkAGwAZQBUAGkAbQBlADAwMDAwMDAw"]
        (key, valDict) = filter.process(None, "munged", testDict.copy())
        assert valDict["Ctx_flag_connectClientDrives"]["value"][0] is True
        assert valDict["Ctx_flag_connectClientPrinters"]["value"][0] is True
        assert valDict["Ctx_flag_defaultPrinter"]["value"][0] is True
        assert valDict["Ctx_flag_tsLogin"]["value"][0] is False
        assert valDict["Ctx_flag_inheritMode"]["value"][0] is True
        assert valDict["CtxMaxConnectionTime"]["value"][0] == 0
        assert valDict["CtxMaxDisconnectionTime"]["value"][0] == 0
        assert valDict["CtxMaxIdleTime"]["value"][0] == 0


        testDict["munged"]["value"] = ["IAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAIAAgACAAUAAQABoACAABAEMAdAB4AEMAZgBnAFAAcgBlAHMAZQBuAHQANTUxZTBiYjAYAAgAAQBDAHQAeABDAGYAZwBGAGwAYQBnAHMAMQAwMDAwMDAwMBYAAAABAEMAdAB4AEMAYQBsAGwAYgBhAGMAawASAAgAAQBDAHQAeABTAGgAYQBkAG8AdwAwMTAwMDAwMCIAAAABAEMAdAB4AEsAZQB5AGIAbwBhAHIAZABMAGEAeQBvAHUAdAAqAAIAAQBDAHQAeABNAGkAbgBFAG4AYwByAHkAcAB0AGkAbwBuAEwAZQB2AGUAbAAwMCAAJgABAEMAdAB4AFcAbwByAGsARABpAHIAZQBjAHQAbwByAHkAMmY3NzZmNzI2YjY5NmU2NzJmNjQ2OTcyNjU2Mzc0NmY3Mjc5MDAgAAIAAQBDAHQAeABOAFcATABvAGcAbwBuAFMAZQByAHYAZQByADAwGAAUAAEAQwB0AHgAVwBGAEgAbwBtAGUARABpAHIAMmY2ODZmNmQ2NTJmNjQ2OTcyMDAiAAYAAQBDAHQAeABXAEYASABvAG0AZQBEAGkAcgBEAHIAaQB2AGUANDgzYTAwIAAiAAEAQwB0AHgAVwBGAFAAcgBvAGYAaQBsAGUAUABhAHQAaAAyZjcwNjE3NDY4MmY3NDZmMmY3MDcyNmY2NjY5NmM2NTAwIgAgAAEAQwB0AHgASQBuAGkAdABpAGEAbABQAHIAbwBnAHIAYQBtADY5NmU2OTc0Njk2MTZjNWY3MDcyNmY2NzcyNjE2ZDAwIgACAAEAQwB0AHgAQwBhAGwAbABiAGEAYwBrAE4AdQBtAGIAZQByADAwKAAIAAEAQwB0AHgATQBhAHgAQwBvAG4AbgBlAGMAdABpAG8AbgBUAGkAbQBlADYwZWEwMDAwLgAIAAEAQwB0AHgATQBhAHgARABpAHMAYwBvAG4AbgBlAGMAdABpAG8AbgBUAGkAbQBlAGMwZDQwMTAwHAAIAAEAQwB0AHgATQBhAHgASQBkAGwAZQBUAGkAbQBlADIwYmYwMjAw"]
        (key, valDict) = filter.process(None, "munged", testDict.copy())
        assert valDict["Ctx_flag_connectClientDrives"]["value"][0] is False
        assert valDict["Ctx_flag_connectClientPrinters"]["value"][0] is False
        assert valDict["Ctx_flag_defaultPrinter"]["value"][0] is False
        assert valDict["Ctx_flag_tsLogin"]["value"][0] is False
        assert valDict["Ctx_flag_inheritMode"]["value"][0] is False
        assert valDict["CtxMaxConnectionTime"]["value"][0] == 1.0
        assert valDict["CtxMaxDisconnectionTime"]["value"][0] == 2.0
        assert valDict["CtxMaxIdleTime"]["value"][0] == 3.0

        assert valDict["CtxInitialProgram"]["value"][0] == b"initial_program"
        assert valDict["CtxWorkDirectory"]["value"][0] == b"/working/directory"
        assert valDict["CtxWFHomeDir"]["value"][0] == b"/home/dir"
        assert valDict["CtxWFHomeDirDrive"]["value"][0] == b"H:"
        assert valDict["CtxWFProfilePath"]["value"][0] == b"/path/to/profile"

    def test_SambaMungedDialOut(self):
        filter = SambaMungedDialOut(None)
        testDict = {'CtxWorkDirectory': {'value': ['']},
                    'CtxCfgPresent': {'value': ['551e0bb0']},
                    'CtxKeyboardLayout': {'value': ['']},
                    'oldStorageBehavior': {'value': []},
                    'Ctx_flag_connectClientPrinters': {'value': [False]},
                    'Ctx_flag_connectClientDrives': {'value': [False]},
                    'CtxWFHomeDir': {'value': ['']},
                    'munged': {'value': [] },
                    'Ctx_flag_defaultPrinter': {'value': [False]},
                    'Ctx_flag_reConn': {'value': [False]},
                    'CtxMaxIdleTime': {'value': [3.0]},
                    'Ctx_shadow': {'value': [1]},
                    'CtxCallback': {'value': ['']},
                    'Ctx_flag_inheritMode': {'value': [False]},
                    'CtxMaxConnectionTime': {'value': [1.0]},
                    'CtxMinEncryptionLevel': {'value': ['']},
                    'Ctx_flag_brokenConn': {'value': [False]},
                    'CtxCallbackNumber': {'value': ['']},
                    'CtxWFProfilePath': {'value': ['']},
                    'Ctx_flag_tsLogin': {'value': [False]},
                    'CtxWFHomeDirDrive': {'value': ['']},
                    'CtxInitialProgram': {'value': ['']},
                    'CtxShadow': {'value': ['01000000']},
                    'CtxNWLogonServer': {'value': ['']},
                    'CtxCfgFlags1': {'value': ['00000000']},
                    'CtxMaxDisconnectionTime': {'value': [2.0]}}
        testDict = {'CtxCfgFlags1': {'value': [b'00000000']},
                    'CtxCfgPresent': {'value': [b'551e0bb0']},
                    'Ctx_flag_reConn': {'value': [False]},
                    'CtxKeyboardLayout': {'value': ['']},
                    'CtxNWLogonServer': {'value': [""]},
                    'CtxWFHomeDir': {'value': [b"/home/dir"]},
                    'Ctx_flag_connectClientPrinters': {'value': [False]},
                    'CtxMaxConnectionTime': {'value': [1.0]},
                    'CtxWFHomeDirDrive': {'value': [b"H:"]},
                    'Ctx_flag_tsLogin': {'value': [False]},
                    'oldStorageBehavior': {'value': []},
                    'CtxMaxIdleTime': {'value': [3.0]},
                    'Ctx_flag_brokenConn': {'value': [False]},
                    'Ctx_flag_connectClientDrives': {'value': [False]},
                    'CtxMaxDisconnectionTime': {'value': [2.0]},
                    'Ctx_flag_defaultPrinter': {'value': [False]},
                    'Ctx_shadow': {'value': [1]},
                    'CtxWorkDirectory': {'value': [b"/working/directory"]},
                    'CtxShadow': {'value': [b'01000000']},
                    'munged': {'value': []},
                    'CtxInitialProgram': {'value': [b'initial_program']},
                    'CtxMinEncryptionLevel': {'value': [0]},
                    'Ctx_flag_inheritMode': {'value': [False]},
                    'CtxCallback': {'value': ['']},
                    'CtxCallbackNumber': {'value': ['']},
                    'CtxWFProfilePath': {'value': [b'/path/to/profile']}}

        with pytest.raises(AttributeError):
            filter.process(None, "munged", testDict.copy())

        testDict["oldStorageBehavior"]["value"] = [False]

        # test all booleans TRUE
        for flag in ['Ctx_flag_brokenConn', 'Ctx_flag_connectClientDrives', 'Ctx_flag_connectClientPrinters', 'Ctx_flag_defaultPrinter', 'Ctx_flag_inheritMode', 'Ctx_flag_reConn', 'Ctx_shadow', 'Ctx_flag_tsLogin']:
            testDict[flag]["value"] = [True]

        print(testDict)
        (key, valDict) = filter.process(None, "munged", testDict.copy())
        assert valDict['munged']['value']

        filterIn = SambaMungedDialIn(None)
        print(valDict)
        (key, valDict) = filterIn.process(None, "munged", valDict.copy())
        for flag in ['Ctx_flag_brokenConn', 'Ctx_flag_connectClientDrives', 'Ctx_flag_connectClientPrinters',
                     'Ctx_flag_defaultPrinter', 'Ctx_flag_inheritMode', 'Ctx_flag_reConn', 'Ctx_shadow',
                     'Ctx_flag_tsLogin']:
            assert valDict[flag]["value"][0] == True

        assert valDict["CtxInitialProgram"]["value"][0] == b"initial_program"
        assert valDict["CtxWorkDirectory"]["value"][0] == b"/working/directory"
        assert valDict["CtxWFHomeDir"]["value"][0] == b"/home/dir"
        assert valDict["CtxWFHomeDirDrive"]["value"][0] == b"H:"
        assert valDict["CtxWFProfilePath"]["value"][0] == b"/path/to/profile"

