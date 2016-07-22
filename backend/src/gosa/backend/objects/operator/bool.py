# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

from gosa.backend.objects.operator import ElementOperator


class And(ElementOperator):

    def process(self, v1, v2):
        return v1 and v2


class Or(ElementOperator):

    def process(self, v1, v2):
        return v1 or v2


class Not(ElementOperator):

    def process(self, a):
        return not a
