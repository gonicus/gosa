# This file is part of the GOsa framework.
#
#  http://GOsa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

from gosa.backend.objects.filter import ElementFilter
from gosa.backend.objects.backend.registry import ObjectBackendRegistry
from gosa.common.error import GosaErrorHandler as C
from gosa.common.utils import N_


# Register the errors handled  by us
C.register_codes(dict(
    PARAMETER_NOT_NUMERIC=N_("Parameter for '%(topic)s' have to be numeric"),
    BACKEND_TOO_MANY=N_("Too many backends for %(topic)s specified"),
    POSIX_ID_POOL_EMPTY=N_("ID pool for attribute %(topic)s is empty [> %(max)s]")
))


class PosixException(Exception):
    pass


class GenerateIDs(ElementFilter):
    """
    Generate gid/uidNumbers on demand
    """
    def __init__(self, obj):
        super(GenerateIDs, self).__init__(obj)

    def process(self, obj, key, valDict, maxGidValue=65500, maxUidValue=65500):

        try:
            maxUidValue = int(maxUidValue)
            maxGidValue = int(maxGidValue)
        except ValueError:
            raise PosixException(C.make_error("PARAMETER_NOT_NUMERIC", "GenerateIDs"))

        if "uidNumber" in valDict:
            if not(len(valDict['uidNumber']['value'])):
                if len(valDict["uidNumber"]['backend']) > 1:
                    raise PosixException(C.make_error("BACKEND_TOO_MANY", "GenerateIDs"))

                be = ObjectBackendRegistry.getBackend(valDict["uidNumber"]['backend'][0])
                uid = be.get_next_id("uidNumber")
                if uid > maxUidValue:
                    raise PosixException(C.make_error("POSIX_ID_POOL_EMPTY", "uidNumber", max=maxUidValue))

                valDict["uidNumber"]['value'] = [uid]

        if "gidNumber" in valDict:
            if not(len(valDict['gidNumber']['value'])):
                if len(valDict["gidNumber"]['backend']) > 1:
                    raise PosixException(C.make_error("BACKEND_TOO_MANY", "GenerateIDs"))

                be = ObjectBackendRegistry.getBackend(valDict["gidNumber"]['backend'][0])
                gid = be.get_next_id("gidNumber")
                if gid > maxGidValue:
                    raise PosixException(C.make_error("POSIX_ID_POOL_EMPTY", "gidNumber", max=maxGidValue))

                valDict["gidNumber"]['value'] = [gid]

        return key, valDict


class LoadGecosState(ElementFilter):
    """
    Detects the state of the autoGECOS attribute
    """
    def __init__(self, obj):
        super(LoadGecosState, self).__init__(obj)

    def process(self, obj, key, valDict):

        # No gecos set right now
        if not(len(valDict['gecos']['value'])):
            valDict[key]['value'] = [True]
            return key, valDict

        # Check if current gecos value would match the generated one
        # We will then assume that this user wants to auto update his gecos entry.
        gecos = GenerateGecos.generateGECOS(valDict)
        if gecos == valDict['gecos']['value'][0]:
            valDict[key]['value'] = [True]
            return key, valDict

        # No auto gecos
        valDict[key]['value'] = [False]
        return key, valDict


class GenerateGecos(ElementFilter):
    """
    An object filter which automatically generates the posix-gecos
    entry.
    """
    def __init__(self, obj):
        super(GenerateGecos, self).__init__(obj)

    def process(self, obj, key, valDict):
        """
        The out-filter that generates the new gecos value
        """
        # Only generate gecos if the the autoGECOS field is True.
        if len(valDict["autoGECOS"]['value']) and (valDict["autoGECOS"]['value'][0]):
            gecos = GenerateGecos.generateGECOS(valDict)
            valDict["gecos"]['value'] = [gecos]

        return key, valDict

    @staticmethod
    def generateGECOS(valDict):
        """
        This method genereates a new gecos value out of the given properties list.
        """

        sn = ""
        givenName = ""
        ou = ""
        telephoneNumber = ""
        homePhone = ""

        if len(valDict["sn"]['value']) and (valDict["sn"]['value'][0]):
            sn = valDict["sn"]['value'][0]
        if len(valDict["givenName"]['value']) and (valDict["givenName"]['value'][0]):
            givenName = valDict["givenName"]['value'][0]
        if len(valDict["homePhone"]['value']) and (valDict["homePhone"]['value'][0]):
            homePhone = valDict["homePhone"]['value'][0]
        if len(valDict["telephoneNumber"]['value']) and (valDict["telephoneNumber"]['value'][0]):
            telephoneNumber = valDict["telephoneNumber"]['value'][0]
        if len(valDict["ou"]['value']) and (valDict["ou"]['value'][0]):
            ou = valDict["ou"]['value'][0]

        return "%s %s,%s,%s,%s" % (sn, givenName, ou, telephoneNumber, homePhone)


class GetNextID(ElementFilter):
    """
    An object filter which inserts the next free ID for the property
    given as parameter. But only if the current value is empty.

    =============== =======================
    Name            Description
    =============== =======================
    attributeName   The target attribute we want to generate an ID for. uidNumber/gidNumber
    maxValue        The maximum value that would be dsitributed.
    =============== =======================
    """
    def __init__(self, obj):
        super(GetNextID, self).__init__(obj)

    def process(self, obj, key, valDict, attributeName="uidNumber", maxValue=65500):
        if len(valDict[key]['value']) and (valDict[key]['value'][0] == -1):
            maxValue = int(maxValue)

            if len(valDict[key]['backend']) > 1:
                raise PosixException(C.make_error("BACKEND_TOO_MANY", "GetNextID"))

            be = ObjectBackendRegistry.getBackend(valDict[key]['backend'][0])
            gid = be.get_next_id(attributeName)
            if gid > maxValue:
                raise PosixException(C.make_error("POSIX_ID_POOL_EMPTY", attributeName, max=maxValue))
            valDict[key]['value'] = [gid]

        return key, valDict
