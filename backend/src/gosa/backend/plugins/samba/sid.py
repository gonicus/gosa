# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

import re
from gosa.common.utils import N_
from gosa.common import Environment
from gosa.backend.objects.filter import ElementFilter
from gosa.common.components import PluginRegistry
from gosa.backend.objects.comparator import ElementComparator
from gosa.common.error import GosaErrorHandler as C


# Register the errors handled  by us
C.register_codes(dict(
    SAMBA_DOMAIN_WITHOUT_SID=N_("Domain %(topic)s has no SID"),
    SAMBA_NO_SID_TYPE=N_("Invalid type '%(type)s' for SID generator [user, group]")
))


class SambaException(Exception):
    pass


class CheckSambaSIDList(ElementComparator):
    """
    Checks whether the given sambaSIDList can be saved or if it
    will produce recursions.
    """
    def __init__(self, obj):
        super(CheckSambaSIDList, self).__init__()

    def process(self, all_props, key, value):
        errors = []
        if "sambaSID" in all_props and len(all_props["sambaSID"]["value"]):
            sid = all_props["sambaSID"]["value"][0]
            if sid in value:
                errors.append(dict(index=value.index(sid),
                        detail=N_("recursive nesting not allowed")))

        return len(errors) == 0, errors


class DetectSambaDomainFromSID(ElementFilter):
    """
    Detects the sambaDomainName for the given SID
    """

    def __init__(self, obj):
        super(DetectSambaDomainFromSID, self).__init__(obj)
        self.env = Environment.getInstance()

    def process(self, obj, key, valDict, sid):

        index = PluginRegistry.getInstance("ObjectIndex")
        sids = index.search({'_type': 'SambaDomain'}, {'sambaSID': 1, 'sambaDomainName': 1})
        for item in sids:
            if re.match("^" + re.escape(item['sambaSID'][0]) + "\-[0-9]*$", sid):
                valDict[key]['value'] = [item['sambaDomainName'][0]]
                return key, valDict

        return key, valDict


class GenerateSambaSid(ElementFilter):
    """
    Out filter to generate a new sambaSID.

    Section **samba**

    +------------------+------------+-------------------------------------------------------------+
    + Key              | Format     +  Description                                                |
    +==================+============+=============================================================+
    + ridbase          | Integer    + Use this as a base for generating SIDs if no pool object    |
    +                  |            + is available.                                               |
    +------------------+------------+-------------------------------------------------------------+

    """

    def __init__(self, obj):
        super(GenerateSambaSid, self).__init__(obj)
        self.env = Environment.getInstance()

    def process(self, obj, key, valDict, method, number, domain, group_type=0):

        if number == "None":
            raise SambaException(C.make_error("ATTRIBUTE_NOT_FOUND", "gidNumber"))

        if domain == "None":
            raise SambaException(C.make_error("ATTRIBUTE_NOT_FOUND", "sambaDomainName"))

        index = PluginRegistry.getInstance("ObjectIndex")
        sid = index.search({'_type': 'SambaDomain', 'sambaDomainName': domain},
            {'sambaSID': 1, 'sambaAlgorithmicRidBase': 1})

        if sid.count() != 1:
            raise SambaException(C.make_error("SAMBA_DOMAIN_WITHOUT_SID", domain))
        dsid = sid[0]['sambaSID'][0]

        if 'sambaAlgorithmicRidBase' in sid[0]:
            ridbase = int(sid[0]['sambaAlgorithmicRidBase'][0])
        else:
            ridbase = int(self.env.config.get('samba.ridbase', default=1000))

        # Generate a sid for groups or users.
        group_type = int(group_type)
        number = int(number)

        if "group" == method:
            if group_type == 0:
                sid = dsid + "-" + str(number * 2 + ridbase + 1)
            else:
                sid = dsid + "-" + str(group_type)
            valDict[key]['value'] = [sid]

        elif "user" == method:
            sid = dsid + "-" + str(number * 2 + ridbase)
            valDict[key]['value'] = [sid]

        else:
            raise SambaException(C.make_error("SAMBA_NO_SID_TYPE", type=method))

        return key, valDict
