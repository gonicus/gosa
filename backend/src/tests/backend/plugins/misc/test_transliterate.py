# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

import unittest
from gosa.backend.plugins.misc.transliterate import *

class TransliterateTests(unittest.TestCase):

    def test_transliterate(self):
        trans = Transliterate()
        assert trans.transliterate("üöäÜÖÄ") == "ueoeaeUeOeAe"