# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

import re
from gosa.backend.objects.filter import ElementFilter
import datetime

from gosa.common.gjson import loads, dumps


class SplitString(ElementFilter):
    """
    splits a string by the given separator

    =========== ===========================
    Key         Description
    =========== ===========================
    glue        The separator string
    =========== ===========================

    e.g.:
    >>> <FilterEntry>
    >>>  <Filter>
    >>>   <Name>SplitString</Name>
    >>>   <Param>,</Param>
    >>>  </Filter>
    >>> </FilterEntry>
    >>>  ...
    """
    def __init__(self, obj):
        super(SplitString, self).__init__(obj)

    def process(self, obj, key, valDict, glue=", "):
        if type(valDict[key]['value']) is not None and len(valDict[key]['value']):
            tmp = valDict[key]['value'][0].split(glue)
            new_val = [n for n in tmp if n != ""]
            valDict[key]['value'] = new_val
        return key, valDict


class JoinArray(ElementFilter):
    """
    Joins an array into a single string using the given separator

    =========== ===========================
    Key         Description
    =========== ===========================
    glue        The joining string
    =========== ===========================

    e.g.:
    >>> <FilterEntry>
    >>>  <Filter>
    >>>   <Name>JoinArray</Name>
    >>>   <Param>,</Param>
    >>>  </Filter>
    >>> </FilterEntry>
    >>>  ...
    """
    def __init__(self, obj):
        super(JoinArray, self).__init__(obj)

    def process(self, obj, key, valDict, glue=", "):
        if type(valDict[key]['value'] is not None):
            new_val = glue.join(valDict[key]['value'])
            if not new_val:
                valDict[key]['value'] = []
            else:
                valDict[key]['value'] = [new_val]
        return key, valDict


class ConcatString(ElementFilter):
    """
    Concatenate a string to the current value.

    =========== ===========================
    Key         Description
    =========== ===========================
    appstr      The string to concatenate
    position    The position 'left' or 'right' we want to concatenate the string
    =========== ===========================

    e.g.:
    >>> <FilterEntry>
    >>>  <Filter>
    >>>   <Name>ConcatString</Name>
    >>>   <Param>Hello Mr. </Param>
    >>>   <Param>left</Param>
    >>>  </Filter>
    >>> </FilterEntry>
    >>>  ...
    """
    def __init__(self, obj):
        super(ConcatString, self).__init__(obj)

    def process(self, obj, key, valDict, appstr, position):
        if type(valDict[key]['value'] is not None):
            if position == "right":
                new_val = list(map(lambda x: x + appstr, valDict[key]['value']))
            else:
                new_val = list(map(lambda x: appstr + x, valDict[key]['value']))
            valDict[key]['value'] = new_val
        return key, valDict


class Replace(ElementFilter):
    """
    Perform a replacement using a reqular expression.

    =========== ===========================
    Key         Description
    =========== ===========================
    regex       The regular expression to use
    replacement The replacement string
    =========== ===========================

    e.g.:
    >>> <FilterEntry>
    >>>  <Filter>
    >>>   <Name>Replace</Name>
    >>>   <Param>^{([^}]*)}.*$</Param>
    >>>   <Param>Result: \1</Param>
    >>>  </Filter>
    >>> </FilterEntry>
    >>>  ...

    """
    def __init__(self, obj):
        super(Replace, self).__init__(obj)

    def process(self, obj, key, valDict, regex, replacement):
        if type(valDict[key]['value'] is not None):
            valDict[key]['value'] = list(map(lambda x: re.sub(regex, str(replacement), x), valDict[key]['value']))
        return key, valDict


class DateToString(ElementFilter):
    """
    Converts a datetime object into a string.

    =========== ===========================
    Key         Description
    =========== ===========================
    fmt         The outgoing format string. E.g. '%Y%m%d%H%M%SZ'
    =========== ===========================

    e.g.:
    >>> <FilterEntry>
    >>>  <Filter>
    >>>   <Name>DateToString</Name>
    >>>   <Param>%Y-%m-%d</Param>
    >>>  </Filter>
    >>> </FilterEntry>
    >>>  ...

    """
    def __init__(self, obj):
        super(DateToString, self).__init__(obj)

    def process(self, obj, key, valDict, fmt="%Y%m%d%H%M%SZ"):
        if type(valDict[key]['value'] is not None):
            valDict[key]['value'] = list(map(lambda x: x.strftime(fmt), valDict[key]['value']))
        return key, valDict


class TimeToString(DateToString):
    """
    Converts a datetime object into a string.

    =========== ===========================
    Key         Description
    =========== ===========================
    fmt         The outgoing format string. E.g. '%Y%m%d%H%M%SZ'
    =========== ===========================

    e.g.:
    >>> <FilterEntry>
    >>>  <Filter>
    >>>   <Name>DateToString</Name>
    >>>   <Param>%Y-%m-%d</Param>
    >>>  </Filter>
    >>> </FilterEntry>
    >>>  ...
    """
    def __init__(self, obj):
        super(TimeToString, self).__init__(obj)


class StringToDate(ElementFilter):
    """
    Converts a string object into a datetime.date object..

    =========== ===========================
    Key         Description
    =========== ===========================
    fmt         The format string. E.g. '%Y%m%d%H%M%SZ'
    =========== ===========================

    e.g.:
    >>> <FilterEntry>
    >>>  <Filter>
    >>>   <Name>StringToDate</Name>
    >>>   <Param>%Y-%m-%d</Param>
    >>>  </Filter>
    >>> </FilterEntry>
    >>>  ...
    """

    def __init__(self, obj):
        super(StringToDate, self).__init__(obj)

    def process(self, obj, key, valDict, fmt="%Y%m%d%H%M%SZ"):
        if type(valDict[key]['value'] is not None):
            valDict[key]['value'] = list(map(lambda x: datetime.datetime.strptime(x, fmt).date(), valDict[key]['value']))
        return key, valDict


class StringToTime(ElementFilter):
    """
    Converts a string object into a datetime.datetime object..

    =========== ===========================
    Key         Description
    =========== ===========================
    fmt         The format string. E.g. '%Y%m%d%H%M%SZ'
    =========== ===========================

    e.g.:
    >>> <FilterEntry>
    >>>  <Filter>
    >>>   <Name>StringToTime</Name>
    >>>   <Param>%Y%m%d%H%M%SZ</Param>
    >>>  </Filter>
    >>> </FilterEntry>
    >>>  ...
    """

    def __init__(self, obj):
        super(StringToTime, self).__init__(obj)

    def process(self, obj, key, valDict, fmt="%Y%m%d%H%M%SZ"):
        if type(valDict[key]['value'] is not None):
            valDict[key]['value'] = list(map(lambda x: datetime.datetime.strptime(x, fmt), valDict[key]['value']))
        return key, valDict


class IdnaToUnicode(ElementFilter):
    """
    Converts a idna object into a unicode object..

    e.g.:
    >>> <FilterEntry>
    >>>  <Filter>
    >>>   <Name>IdnaToUnicode</Name>
    >>>  </Filter>
    >>> </FilterEntry>
    >>>  ...
    """

    def __init__(self, obj):
        super(IdnaToUnicode, self).__init__(obj)

    def process(self, obj, key, valDict):
        valDict[key]['value'] = list(map(lambda x: x.encode('ascii').decode('idna'), valDict[key]['value']))
        valDict[key]['backend_type'] = 'UnicodeString'
        return key, valDict


class UnicodeToIdna(ElementFilter):
    """
    Converts an unicode object into a idna value ...

    e.g.:
    >>> <FilterEntry>
    >>>  <Filter>
    >>>   <Name>UnicodeToIdna</Name>
    >>>  </Filter>
    >>> </FilterEntry>
    >>>  ...
    """

    def __init__(self, obj):
        super(UnicodeToIdna, self).__init__(obj)

    def process(self, obj, key, valDict):
        valDict[key]['value'] = list(map(lambda x: x.encode('idna'), valDict[key]['value']))
        valDict[key]['backend_type'] = 'String'
        return key, valDict


class StringToJson(ElementFilter):
    """
    Parses a string with the json parser.

    e.g.:
    >>> <FilterEntry>
    >>>  <Filter>
    >>>   <Name>StringToJson</Name>
    >>>  </Filter>
    >>> </FilterEntry>
    >>>  ...
    """

    def __init__(self, obj):
        super(StringToJson, self).__init__(obj)

    def process(self, obj, key, valDict):
        if type(valDict[key]['value'] is not None):
            valDict[key]['value'] = list(map(lambda x: loads(x), valDict[key]['value']))
        return key, valDict


class JsonToString(ElementFilter):
    """
    Serializes an object to a json string.

    e.g.:
    >>> <FilterEntry>
    >>>  <Filter>
    >>>   <Name>JsonToString</Name>
    >>>  </Filter>
    >>> </FilterEntry>
    >>>  ...
    """

    def __init__(self, obj):
        super(JsonToString, self).__init__(obj)

    def process(self, obj, key, valDict):
        if type(valDict[key]['value'] is not None):
            valDict[key]['value'] = list(map(lambda x: dumps(x), valDict[key]['value']))
        return key, valDict
