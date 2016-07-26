# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

import unittest
import gosa.dbus.main


class MainTestCase(unittest.TestCase):

    def test_main(self):
        with unittest.mock.patch("gosa.dbus.main.mainLoop") as m,\
                unittest.mock.patch("gosa.dbus.main.os.geteuid", return_value=1) as mg:

            gosa.dbus.main.main()
            assert not m.called

            mg.return_value = 0

            gosa.dbus.main.main()
            assert m.called