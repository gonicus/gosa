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


class ZarafaDisabledFeaturesOut(ElementFilter):
    """
    Out-Filter for zarafa disabled features.
    """

    def __init__(self, obj):
        super(ZarafaDisabledFeaturesOut, self).__init__(obj)

    def process(self, obj, key, valDict):

        # Reset value
        valDict[key]['value'] = []

        # Create a list with all relevant attributes.
        alist = {'enablePop3' : 'pop3', 'enableZPush': 'zpush', 'enableImap': 'imap'}

        # Build up a list of values to encode.
        for entry, _key in alist.items():
            if not len(valDict[entry]['value']):
                raise AttributeError(C.make_error('ATTRIBUTE_MANDATORY', entry))
            else:
                if not valDict[entry]['value'][0]:
                    valDict[key]['value'].append(_key)

        return key, valDict


class ZarafaEnabledFeaturesOut(ElementFilter):
    """
    Out-Filter for zarafa enabled features.
    """

    def __init__(self, obj):
        super(ZarafaEnabledFeaturesOut, self).__init__(obj)

    def process(self, obj, key, valDict):

        # Reset value
        valDict[key]['value'] = []

        # Create a list with all relevant attributes.
        alist = {'enablePop3' : 'pop3', 'enableZPush': 'zpush', 'enableImap': 'imap'}

        # Build up a list of values to encode.
        for entry, _key in alist.items():
            if not len(valDict[entry]['value']):
                raise AttributeError(C.make_error('ATTRIBUTE_MANDATORY', entry))
            else:
                if valDict[entry]['value'][0]:
                    valDict[key]['value'].append(_key)

        return key, valDict


class ZarafaEnabledFeaturesIn(ElementFilter):
    """
    In-Filter for zarafa enabled features.
    """

    def __init__(self, obj):
        super(ZarafaEnabledFeaturesIn, self).__init__(obj)

    def process(self, obj, key, valDict):

        if len(valDict[key]['value']):

            # Update the value of the read property
            values = valDict[key]['value']

            valDict['enablePop3']['value'] = ["pop3" in values]
            valDict['enablePop3']['skip_save'] = True
            valDict['enableZPush']['value'] = ["zpush" in values]
            valDict['enableZPush']['skip_save'] = True
            valDict['enableImap']['value'] = ["imap" in values]
            valDict['enableImap']['skip_save'] = True

        return key, valDict
