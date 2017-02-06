# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

from email.utils import parseaddr
from gosa.common.utils import N_
from gosa.backend.objects.comparator import ElementComparator


class IsValidMailAddress(ElementComparator):
    """
    Validates a given mail address.
    """

    def process(self, all_props, key, value):

        errors = []

        for mail in value:
            if not '@' in parseaddr(mail)[1]:
                errors.append(dict(index=value.index(mail),
                    detail=N_("invalid mail address '%(mail)s'"),
                    mail=mail))

        return len(errors) == 0, errors
