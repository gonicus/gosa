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
try:
    import gosa.dbus.main
    has_glib = True
except ImportError:
    has_glib = False


@pytest.mark.skipif(has_glib is False, reason="requires gi package")
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