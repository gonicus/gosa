# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

import re
import difflib
from urllib.parse import urlparse
from gosa.common.utils import N_
from gosa.backend.objects.comparator import ElementComparator


class Like(ElementComparator):
    """
    Object property validator which checks if a given property value is
    like a given operand.

    =========== ==================
    Key         Description
    =========== ==================
    match       The value we match against.
    =========== ==================
    """

    def process(self, all_props, key, value, match):

        errors = []

        # All items of value have to match.
        cnt = 0
        for item in value:
            if difflib.SequenceMatcher(None, item, match).ratio() < 0.75:
                errors.append(dict(index=cnt,
                    detail=N_("value is not like %(comparator)s"),
                    comparator=match))
                return False, errors
            cnt += 1
        return True, errors


class RegEx(ElementComparator):
    """
    Object property validator which checks if a given property matches
    a given regular expression.

    =========== ==================
    Key         Description
    =========== ==================
    match       The value we match againt.
    =========== ==================
    """

    def process(self, all_props, key, value, match):

        errors = []

        # All items of value have to match.
        cnt = 0
        for item in value:
            if not re.match(match, item):
                errors.append(dict(index=cnt, detail=N_("syntax error")))
                return False, errors
            cnt += 1
        return True, errors


class IsValidURL(ElementComparator):
    """
    Object property validator which checks if a given property is a valid URL.
    """

    def process(self, all_props, key, value):

        errors = []

        # All items of value have to match.
        cnt = 0
        for item in value:
            spec = urlparse(item)

            if not spec.scheme in ["http", "https"]:
                errors.append(dict(index=cnt, detail=N_("invalid HTTP URL")))
                return False, errors
            cnt += 1
        return True, errors



class stringLength(ElementComparator):
    """
    Object property validator which checks for a given value length.

    ======= ==================
    Key     Description
    ======= ==================
    minSize The minimum-size of the property values.
    maxSize The maximum-size of the property values.
    ======= ==================

    """

    def process(self, all_props, key, value, minSize, maxSize):

        errors = []

        # Convert limits to integer values.
        minSize = int(minSize)
        maxSize = int(maxSize)

        # Each item of value has to match the given length-rules
        for entry in value:
            cnt = len(entry)
            if minSize >= 0 and cnt < minSize:
                errors.append(dict(index=cnt,
                    detail=N_("value is short, at least %(count)s characters required"),
                    count=minSize))
                return False, errors
            elif 0 <= maxSize < cnt:
                errors.append(dict(index=cnt,
                    detail=N_("value is long, at max %(count)s characters allowed"),
                    count=maxSize))
                return False, errors
        return True, errors
