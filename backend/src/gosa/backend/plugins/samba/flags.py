# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

from gosa.backend.objects.filter import ElementFilter


# SambaAcctFlags mapping.
mapping = {'D': 'acct_accountDisabled',
           'H': 'acct_homeDirectoryRequired',
           'I': 'acct_interDomainTrust',
           'L': 'acct_isAutoLocked',
           'M': 'acct_MNSLogonAccount',
           'N': 'acct_passwordNotRequired',
           'S': 'acct_serverTrustAccount',
           'T': 'acct_temporaryDuplicateAccount',
           'U': 'acct_normalUserAccount',
           'W': 'acct_workstationTrustAccount',
           'X': 'acct_passwordDoesNotExpire'}


class SambaAcctFlagsOut(ElementFilter):
    """
    In-Filter for sambaAcctFlags.

    Combines flag-properties into sambaAcctFlags proeprty
    """

    #pylint: disable=W0613
    def __init__(self, obj):
        super(SambaAcctFlagsOut, self).__init__(obj)

    def process(self, obj, key, valDict):

        # Now parse the existing acctFlags
        flagStr = ""
        for flag in mapping:
            if len(valDict[mapping[flag]]['value']) >= 1 and valDict[mapping[flag]]['value'][0]:
                flagStr += flag

        valDict[key]['value'] = ["[" + flagStr + "]"]

        return key, valDict


class SambaAcctFlagsIn(ElementFilter):
    """
    In-Filter for sambaAcctFlags.

    Each option will be transformed into a separate attribute.
    """

    def __init__(self, obj):
        super(SambaAcctFlagsIn, self).__init__(obj)

    #pylint: disable=W0613
    def process(self, obj, key, valDict):

        # Add newly introduced properties.
        for src in mapping:
            valDict[mapping[src]]['value'] = [False]
            valDict[mapping[src]]['skip_save'] = True

        # Now parse the existing acctFlags
        if len(valDict[key]['value']) >= 1:
            smbAcct = valDict[key]['value'][0]
            for src in mapping:
                if src in set(smbAcct):
                    valDict[mapping[src]]['value'] = [True]

        return key, valDict
