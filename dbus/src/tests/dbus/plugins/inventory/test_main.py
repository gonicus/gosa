# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.
import os
import pytest
from lxml import objectify
from unittest import TestCase, mock
from gosa.dbus.plugins.inventory.main import DBusInventoryHandler, InventoryException


class DBusInventoryHandlerTestCase(TestCase):

    def test_inventory(self):
        handler = DBusInventoryHandler()

        # real usage should not work as is requires root privileges
        assert handler.inventory() is None

        with open(os.path.join(os.path.dirname(__file__), "fusion_example.xml"), "rb") as f:
            example = f.read()
            with mock.patch("gosa.dbus.plugins.inventory.main.subprocess.check_output", return_value=example):
                res = handler.inventory()
                event = objectify.fromstring(res)
                assert hasattr(event, "Inventory")

        with mock.patch("gosa.dbus.plugins.inventory.main.subprocess.check_output", return_value="wrong syntax"),\
                pytest.raises(InventoryException):
            handler.inventory()
