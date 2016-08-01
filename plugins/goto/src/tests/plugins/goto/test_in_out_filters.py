# This file is part of the GOsa project.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.
import unittest
from gosa.plugins.goto.in_out_filters import *

class GotoFilterTestCase(unittest.TestCase):

    def test_registeredDeviceStatusOut(self):
        filter = registeredDeviceStatusOut(None)

        test_dict = {
            "status_Online": {
                "value": [True]
            },
            "status_Offline": {
                "value": [False]
            },
            "status_UpdateAvailable": {
                "value": [True]
            },
            "status_UpdateInProgress": {
                "value": [False]
            },
            "status_InventoryInProgress": {
                "value": [True]
            },
            "status_ConfigurationInProgress": {
                "value": [True]
            },
            "status_InstallationInProgress": {
                "value": [True]
            },
            "status_VirtualMachineCreationInProgress": {
                "value": [True]
            },
            "status_Warning": {
                "value": [True]
            },
            "status_Error": {
                "value": [True]
            },
            "status_SystemHasActiveUserSessions": {
                "value": [True]
            },
            "status_SystemActivated": {
                "value": [True]
            },
            "status_SystemLocked": {
                "value": []
            },
            "flag_str": {
                "value": [""]
            }
        }

        filter.process(None, "flag_str", test_dict)
        res = test_dict["flag_str"]["value"][0]
        assert "O" in res
        assert "o" not in res
        assert "a" not in res
        assert "U" not in res
        assert "u" in res
        assert "i" in res
        assert "C" in res
        assert "I" in res
        assert "V" in res
        assert "W" in res
        assert "E" in res
        assert "B" in res
        assert "A" in res

    def test_registeredDeviceStatusIn(self):
        filter = registeredDeviceStatusIn(None)
        test_dict = {
            "status_Online": {
                "value": [True]
            },
            "status_Offline": {
                "value": [False]
            },
            "status_UpdateAvailable": {
                "value": [True]
            },
            "status_UpdateInProgress": {
                "value": [False]
            },
            "status_InventoryInProgress": {
                "value": [True]
            },
            "status_ConfigurationInProgress": {
                "value": [True]
            },
            "status_InstallationInProgress": {
                "value": [True]
            },
            "status_VirtualMachineCreationInProgress": {
                "value": [True]
            },
            "status_Warning": {
                "value": [True]
            },
            "status_Error": {
                "value": [True]
            },
            "status_SystemHasActiveUserSessions": {
                "value": [True]
            },
            "status_SystemActivated": {
                "value": [True]
            },
            "status_SystemLocked": {
                "value": []
            },
            "flag_str": {
                "value": ["uCiBIEOAVW"]
            }
        }

        filter.process(None, "flag_str", test_dict)
        assert test_dict["status_SystemLocked"]["value"][0] is False
        assert test_dict["status_Offline"]["value"][0] is False
        assert test_dict["status_UpdateInProgress"]["value"][0] is False
        assert test_dict["status_Online"]["value"][0] is True
        assert test_dict["status_UpdateAvailable"]["value"][0] is True
        assert test_dict["status_InventoryInProgress"]["value"][0] is True
        assert test_dict["status_ConfigurationInProgress"]["value"][0] is True
        assert test_dict["status_InstallationInProgress"]["value"][0] is True
        assert test_dict["status_VirtualMachineCreationInProgress"]["value"][0] is True
        assert test_dict["status_Warning"]["value"][0] is True
        assert test_dict["status_Error"]["value"][0] is True
        assert test_dict["status_SystemHasActiveUserSessions"]["value"][0] is True
        assert test_dict["status_SystemActivated"]["value"][0] is True


