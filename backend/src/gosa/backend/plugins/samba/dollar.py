# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.
from gosa.backend.objects.filter import ElementFilter
from gosa.common.error import GosaErrorHandler as C


class SambaDollarFilterOut(ElementFilter):
    """
    An object filter which can add a '$' after the machines system-ID
    """
    def __init__(self, obj):
        super(SambaDollarFilterOut, self).__init__(obj)

    def process(self, obj, key, valDict):

        found = False

        entry = valDict[key]
        val = self.__get_value(entry)
        if val:
            entry['value'][0] = val
            found = True
        elif 'depends_on' in entry:
            for dep in entry['depends_on']:
                val = self.__get_value(valDict[dep])
                if val:
                    entry['value'].append(val)
                    found = True
                    break

        if not found:
            raise ValueError(C.make_error("TYPE_UNKNOWN", self.__class__.__name__, type=type(entry['value'])))

        return key, valDict

    def __get_value(self, entry):
        value_entry = entry['value']
        if len(value_entry) and type(value_entry[0]) == str:
            return value_entry[0].rstrip("$") + "$"


class SambaDollarFilterIn(ElementFilter):
    """
    An object filter which can remove a '$' after the machines system-ID
    """
    def __init__(self, obj):
        super(SambaDollarFilterIn, self).__init__(obj)

    def process(self, obj, key, valDict):
        if len(valDict[key]['value']) and type(valDict[key]['value'][0]) == str:
            valDict[key]['value'][0] = valDict[key]['value'][0].rstrip("$")
        else:
            raise ValueError(C.make_error("TYPE_UNKNOWN", self.__class__.__name__, type=type(valDict[key]['value'])))

        return key, valDict
