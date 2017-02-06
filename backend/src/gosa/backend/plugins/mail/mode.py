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


class MailDeliveryModeOut(ElementFilter):
    """
    Out-Filter for gosaMailDeliveryMode.
    """

    def __init__(self, obj):
        super(MailDeliveryModeOut, self).__init__(obj)

    def process(self, obj, key, valDict):
        # Create a list with all relevant attributes.
        alist = ['inVacation', 'activateSpamFilter', 'mailSizeFilter',
                 'localDelivery', 'skipOwnMailbox', 'customSieveScript']

        # Build up a list of values to encode.
        res = {}
        for entry in alist:
            if not len(valDict[entry]['value']):
                raise AttributeError(C.make_error('ATTRIBUTE_MANDATORY', entry))
            else:
                res[entry] = valDict[entry]['value'][0]

        # Encode the mail delivery mode attribute.
        result = ""
        if res['inVacation']:
            result += "V"
        if res['activateSpamFilter']:
            result += "S"
        if res['mailSizeFilter']:
            result += "R"
        if res['localDelivery']:
            result += "L"
        if res['skipOwnMailbox']:
            result += "I"
        if res['customSieveScript']:
            result += "C"

        valDict[key]['value'] = ["[" + result + "]"]

        return key, valDict


class MailDeliveryModeIn(ElementFilter):
    """
    In-Filter for gosaMailDeliveryMode.
    """

    def __init__(self, obj):
        super(MailDeliveryModeIn, self).__init__(obj)

    def process(self, obj, key, valDict):

        if len(valDict[key]['value']):

            # Update the value of the read property
            value = valDict[key]['value'][0]

            valDict['inVacation']['value'] = ["V" in value]
            valDict['inVacation']['skip_save'] = True
            valDict['activateSpamFilter']['value'] = ["S" in value]
            valDict['activateSpamFilter']['skip_save'] = True
            valDict['mailSizeFilter']['value'] = ["R" in value]
            valDict['mailSizeFilter']['skip_save'] = True
            valDict['localDelivery']['value'] = ["L" in value]
            valDict['localDelivery']['skip_save'] = True
            valDict['skipOwnMailbox']['value'] = ["I" in value]
            valDict['skipOwnMailbox']['skip_save'] = True
            valDict['customSieveScript']['value'] = ["C" in value]
            valDict['customSieveScript']['skip_save'] = True

        return key, valDict
