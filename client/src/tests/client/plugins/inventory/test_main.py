# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.
import subprocess
import dbus
import dbusmock
import time
from unittest import mock
from gosa.client.plugins.inventory.main import *


class ClientInventoryTestCase(dbusmock.DBusTestCase):

    @classmethod
    def setUpClass(klass):
        klass.start_system_bus()
        klass.dbus_con = klass.get_dbus(system_bus=True)

    def setUp(self):
        self.inv_mock = self.spawn_server('org.gosa',
                                           '/org/gosa/inventory',
                                           'org.gosa',
                                           system_bus=True,
                                           stdout=subprocess.PIPE)

        # Get a proxy for the object's Mock interface
        self.dbus_inventory_mock = dbus.Interface(self.dbus_con.get_object(
            'org.gosa', '/org/gosa/inventory'),
            dbusmock.MOCK_IFACE)
        schema_loc = resource_filename("gosa.plugins.goto", "data/events/Inventory.xsd")
        self.dbus_inventory_mock.AddMethod('', 'inventory', '', 's', 'ret = \''
                                           '<Event xmlns="http://www.gonicus.de/Events" '
                                           'xmlns:e="http://www.gonicus.de/Events" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                                           'xsi:schemaLocation="http://www.gonicus.de/Events %s">'
                                           '<Inventory>'
                                           '<Checksum>1234567890</Checksum>'
                                           '<DeviceID>localhost.example.net-2016-08-05-11-14-44</DeviceID>'
                                           '<QueryType>INVENTORY</QueryType>'
                                           '<ClientVersion>FusionInventory-Agent_v2.3.16</ClientVersion>'
                                           '<ClientUUID>fake_client_uuid</ClientUUID>'
                                           '<HardwareUUID>fake_hardware_uuid</HardwareUUID>'
                                           '<Hostname>localhost</Hostname>'
                                           '</Inventory>'
                                           '</Event>\'' % schema_loc)

    def tearDown(self):
        self.inv_mock.terminate()
        self.inv_mock.wait()

    def test_request_inventory(self):
        with mock.patch("gosa.client.plugins.inventory.main.DBusRunner.get_instance") as m:
            m.return_value.get_system_bus.return_value = self.dbus_con
            inv = Inventory()
            time.sleep(0.1)
            with mock.patch("gosa.client.plugins.inventory.main.PluginRegistry.getInstance") as m:
                assert inv.request_inventory("f9f56039886788f4716909b32a19dac7") is None
                assert inv.request_inventory() is True
                time.sleep(0.1)
                assert m.return_value.send_message.called

            self.inv_mock.terminate()
            self.inv_mock.wait()

            assert inv.request_inventory() is False

