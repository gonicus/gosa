# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

import unittest
from gosa.client.event import *


class EventTestCase(unittest.TestCase):

    def test_resume(self):
        res = Resume()
        assert isinstance(res, Resume)