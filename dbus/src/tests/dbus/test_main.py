# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.
import pytest
from unittest import TestCase, mock
import gosa.dbus.main


class MainTestCase(TestCase):

    def test_main(self):
        with mock.patch("gosa.dbus.main.mainLoop") as m,\
                mock.patch("gosa.dbus.main.os.geteuid", return_value=1) as mg:

            with pytest.raises(SystemExit) as cm:
                gosa.dbus.main.main()
                assert not m.called
                assert cm.exception_code == 1

            mg.return_value = 0

            gosa.dbus.main.main()
            assert m.called