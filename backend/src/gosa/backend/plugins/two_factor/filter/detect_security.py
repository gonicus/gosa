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
from gosa.common import Environment


class DetectSecureContext(ElementFilter):
    """
    Detects locking status of an account. By checking the incoming password
    hash for the deactivation flag '!'.
    """
    def __init__(self, obj):
        super(DetectSecureContext, self).__init__(obj)

    def process(self, obj, key, valDict):
        """
        Detects whether this password hash was marked as locked or not
        """
        ssl = Environment.getInstance().config.getboolean('http.ssl')
        valDict[key]['value'] = [ssl]
        return key, valDict
