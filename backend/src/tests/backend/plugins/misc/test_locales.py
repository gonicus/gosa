# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

import unittest
from gosa.backend.plugins.misc.locales import *

class LocalesTests(unittest.TestCase):

    def test_getLanguageList(self):
        loc = Locales()
        all_locs = loc.getLanguageList()

        # just some simple checks if there is something
        assert len(all_locs) > 50
        assert 'en_US.UTF-8' in all_locs
        assert all_locs['en_US.UTF-8']['value'] == "English (USA)"
        assert 'de_DE.UTF-8' in all_locs
        assert all_locs['de_DE.UTF-8']['value'] == "German (Germany) - Deutsch"

        # translates
        all_locs = loc.getLanguageList("de")

        assert len(all_locs) > 50
        assert 'en_US.UTF-8' in all_locs
        assert all_locs['en_US.UTF-8']['value'] == "Englisch (USA)"
        assert 'de_DE.UTF-8' in all_locs
        assert all_locs['de_DE.UTF-8']['value'] == "Deutsch (Deutschland) - Deutsch"

    def test_get_locales_map(self):
        loc = Locales()
        all_locs = loc.get_locales_map()

        # just some simple checks if there is something
        assert len(all_locs) > 50
        assert 'en_US.UTF-8' in all_locs
        assert all_locs['en_US.UTF-8'] == "English (USA)"
        assert 'de_DE.UTF-8' in all_locs
        assert all_locs['de_DE.UTF-8'] == "German (Germany) - Deutsch"