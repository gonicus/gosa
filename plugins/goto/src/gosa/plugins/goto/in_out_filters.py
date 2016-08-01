# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

from gosa.backend.objects.filter import ElementFilter

mapping = {'O': 'status_Online',
           'o': 'status_Offline',
           'u': 'status_UpdateAvailable',
           'U': 'status_UpdateInProgress',
           'i': 'status_InventoryInProgress',
           'C': 'status_ConfigurationInProgress',
           'I': 'status_InstallationInProgress',
           'V': 'status_VirtualMachineCreationInProgress',
           'W': 'status_Warning',
           'E': 'status_Error',
           'B': 'status_SystemHasActiveUserSessions',
           'A': 'status_SystemActivated',
           'a': 'status_SystemLocked'}


class registeredDeviceStatusOut(ElementFilter):
    """
    out-Filter for deviceStatus.

    Combines flag-properties into deviceStatus property
    """

    #pylint: disable=W0613
    def __init__(self, obj):
        super(registeredDeviceStatusOut, self).__init__(obj)

    def process(self, obj, key, valDict):

        # Now parse the existing acctFlags
        flagStr = ""
        for flag in mapping:
            if len(valDict[mapping[flag]]['value']) >= 1 and valDict[mapping[flag]]['value'][0]:
                flagStr += flag

        valDict[key]['value'] = [flagStr]
        return key, valDict


class registeredDeviceStatusIn(ElementFilter):
    """
    In-Filter for deviceStatus.

    Each option will be transformed into a separate attribute.
    """

    def __init__(self, obj):
        super(registeredDeviceStatusIn, self).__init__(obj)

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
