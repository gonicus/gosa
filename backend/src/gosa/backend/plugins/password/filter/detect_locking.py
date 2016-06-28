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


class DetectAccountLockStatus(ElementFilter):
    """
    Detects locking status of an account. By checking the incoming password
    hash for the deactivation flag '!'.
    """
    def __init__(self, obj):
        super(DetectAccountLockStatus, self).__init__(obj)

    def process(self, obj, key, valDict):
        """
        Detects whether this password hash was marked as locked or not
        """
        if len(valDict['userPassword']['in_value']):
            pwdh = valDict['userPassword']['in_value'][0]
            valDict[key]['value'] = [re.match(r'^{[^\}]+}!', pwdh.decode()) is not None]
        return key, valDict
