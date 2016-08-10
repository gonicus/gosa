# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.
import dbusmock


class ClientDBusTestCase(dbusmock.DBusTestCase):
    @classmethod
    def setUpClass(klass):
        klass.start_system_bus()
        klass.dbus_con = klass.get_dbus(system_bus=True)

    # @classmethod
    # def wait_for_bus_object(klass, dest, path, system_bus=False, timeout=10):
    #     dbusmock.DBusTestCase.wait_for_bus_object(dest, path, system_bus=system_bus, timeout=timeout)
