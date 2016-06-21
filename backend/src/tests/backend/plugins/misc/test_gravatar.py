# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

import unittest
from urllib import parse
from gosa.backend.plugins.misc.gravatar import *

class GravatarTests(unittest.TestCase):

    def test_getGravatarURL(self):
        grav = Gravatar()
        parsed = parse.urlparse(grav.getGravatarURL("test@tester.org"))
        params = parse.parse_qs(parsed.query)
        assert parsed.path == "/avatar.php"
        assert parsed.netloc == "www.gravatar.com"
        assert params['size'] == ["40"]
        assert params['default'] == ["http://www.gonicus.de"]
        assert params['gravatar_id'] == ["cd7e86e214870c0047faf4daf3be8cb3"]
