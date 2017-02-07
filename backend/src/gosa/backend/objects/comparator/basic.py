# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

from gosa.common.utils import N_
from gosa.backend.objects.comparator import ElementComparator


class Equals(ElementComparator):
    """
    Object property validator which checks for a given property value.

    =========== ==================
    Key         Description
    =========== ==================
    match       The value we want to match for.
    case_ignore If True then upper/lower case is ignored.
    =========== ==================
    """

    def process(self, all_props, key, value, match, case_ignore=False):

        errors = []

        # Check each property value
        cnt = 0
        for item in value:

            # Depending on the ignore-case parameter we do not match upper/lower-case differences.
            if case_ignore:
                if item.lower() != match.lower():
                    errors.append(dict(index=cnt,
                        detail=N_("item does not match the given value ignoring the case",
                        )))
                    return False, errors
            else:
                if item != match:
                    errors.append(dict(index=cnt,
                        detail=N_("item does not match the given value",
                        )))
                    return False, errors
            cnt += 1
        return True, errors


class Greater(ElementComparator):
    """
    Object property validator which checks if a given property value is
    greater than a given operand.

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
        match = int(match)
        for item in value:
            # Number or attribute?
            if item.isdigit():
                item = int(item)
            else:
                item = int(all_props[item]["value"][0])

            if not (item > match):
                errors.append(dict(index=cnt,
                    detail=N_("item needs to be greater than %(compare)s"),
                    compare=match
                    ))
                return False, errors
            cnt += 1
        return True, errors


class Smaller(ElementComparator):

    """
    Object property validator which checks if a given property value is
    smaller than a given operand.

    =========== ==================
    Key         Description
    =========== ==================
    match       The value we match againt.
    =========== ==================
    """

    def process(self, all_props, key, value, match):

        errors = []

        # All items of value have to match.
        match = int(match)
        cnt = 0
        for item in value:

            # Number or attribute?
            if item.isdigit():
                item = int(item)
            else:
                item = int(all_props[item]["value"][0])

            if not (item < match):
                errors.append(dict(index=cnt,
                    detail=N_("item needs to be smaller than %(compare)s"),
                    compare=match
                    ))
                return False, errors
            cnt += 1
        return True, errors
