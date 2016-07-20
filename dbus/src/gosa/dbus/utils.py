# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

import dbus.service
import dbus.mainloop.glib


def get_system_bus():
    """
    *get_system_bus* acts as a singleton and returns the
    system bus for 'org.gosa'.

    ``Return:`` system bus
    """
    if not get_system_bus.bus:
        dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
        get_system_bus.bus = dbus.SystemBus()
        get_system_bus.name = dbus.service.BusName('org.gosa', get_system_bus.bus)

    return get_system_bus.bus

get_system_bus.bus = None
