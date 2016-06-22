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
from gosa.backend.plugins.samba.flags import *
# import the error code
import gosa.backend.plugins.samba.hash

class SambaDollarTestCase(unittest.TestCase):

    def test_SambaDollarFilterOut(self):
        filter = SambaAcctFlagsOut(None)
        testDict = {
            "acct_accountDisabled": {
                "value": [True]
            },
            "acct_homeDirectoryRequired": {
                "value":[False]
            },
            "acct_interDomainTrust": {
                "value": [True]
            },
            "acct_isAutoLocked": {
                "value": [True]
            },
            "acct_MNSLogonAccount": {
                "value": [False]
            },
            "acct_passwordNotRequired": {
                "value": [True]
            },
            "acct_serverTrustAccount": {
                "value": [True]
            },
            "acct_temporaryDuplicateAccount": {
                "value": [False]
            },
            "acct_normalUserAccount": {
                "value": [True]
            },
            "acct_workstationTrustAccount": {
                "value": [True]
            },
            "acct_passwordDoesNotExpire": {
                "value": [False]
            },
            "flags": {
                "value": []
            }
        }
        (key, valDict) = filter.process(None, "flags", testDict)
        assert 'D' in valDict['flags']['value'][0]
        assert 'I' in valDict['flags']['value'][0]
        assert 'L' in valDict['flags']['value'][0]
        assert 'N' in valDict['flags']['value'][0]
        assert 'S' in valDict['flags']['value'][0]
        assert 'U' in valDict['flags']['value'][0]
        assert 'W' in valDict['flags']['value'][0]
        assert 'H' not in valDict['flags']['value'][0]
        assert 'M' not in valDict['flags']['value'][0]
        assert 'T' not in valDict['flags']['value'][0]
        assert 'X' not in valDict['flags']['value'][0]

    def test_SambaDollarFilterIn(self):
        filter = SambaAcctFlagsIn(None)
        testDict = {
            "acct_accountDisabled": {
                "value": [False]
            },
            "acct_homeDirectoryRequired": {
                "value": [False]
            },
            "acct_interDomainTrust": {
                "value": [False]
            },
            "acct_isAutoLocked": {
                "value": [False]
            },
            "acct_MNSLogonAccount": {
                "value": [False]
            },
            "acct_passwordNotRequired": {
                "value": [False]
            },
            "acct_serverTrustAccount": {
                "value": [False]
            },
            "acct_temporaryDuplicateAccount": {
                "value": [False]
            },
            "acct_normalUserAccount": {
                "value": [False]
            },
            "acct_workstationTrustAccount": {
                "value": [False]
            },
            "acct_passwordDoesNotExpire": {
                "value": [False]
            },
            "flags": {
                "value": ["ISDWLNU"]
            }
        }
        (key, valDict) = filter.process(None, "flags", testDict)
        assert valDict['acct_accountDisabled']['value'][0] == True
        assert valDict['acct_homeDirectoryRequired']['value'][0] == False
        assert valDict['acct_interDomainTrust']['value'][0] == True
        assert valDict['acct_isAutoLocked']['value'][0] == True
        assert valDict['acct_MNSLogonAccount']['value'][0] == False
        assert valDict['acct_passwordNotRequired']['value'][0] == True
        assert valDict['acct_serverTrustAccount']['value'][0] == True
        assert valDict['acct_temporaryDuplicateAccount']['value'][0] == False
        assert valDict['acct_normalUserAccount']['value'][0] == True
        assert valDict['acct_workstationTrustAccount']['value'][0] == True
        assert valDict['acct_passwordDoesNotExpire']['value'][0] == False