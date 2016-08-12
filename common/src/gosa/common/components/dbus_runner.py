# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

import sys

from gosa.common import Environment

try:
    import dbus

except ImportError:
    print("Please install the python dbus module.")
    sys.exit(1)

from gi.repository import GLib
import time
from threading import Thread
from dbus.mainloop.glib import DBusGMainLoop


class DBusRunner(object):
    """
    The *DBusRunner* module acts as a singleton for the DBUS system
    bus. Interested instances can obtain the system bus from the
    runner.
    """
    __bus = None
    __active = False
    __instance = None

    def __init__(self):
        DBusGMainLoop(set_as_default=True)
        DBusRunner.__bus = dbus.SystemBus()

    def start(self):
        """
        Start the :func:`gi.MainLoop` to establish DBUS communications.
        """
        if self.__active:
            return

        self.__active = True

        self.__thread = Thread(target=self.__runner)
        self.__thread.daemon = True
        self.__thread.start()

    def __runner(self):
        self.__gloop = GLib.MainLoop()
        try:
            self.__gloop.run()
            context = self.__gloop.get_context()
            while self.__active:
                context.iteration(False)
                if not context.pending():
                    time.sleep(.1)
        except KeyboardInterrupt:
            self.__active = False
            env = Environment.getInstance()
            if hasattr(env, "active"):
                env.active = False

    def stop(self):
        """
        Stop the :func:`gobject.MainLoop` to shut down DBUS communications.
        """
        # Don't stop us twice
        if not self.__active:
            return

        self.__active = False
        self.__gloop.quit()
        self.__thread.join(5)

    def get_system_bus(self):
        """
        Return the current DBUS system bus.

        ``Return:`` DBusRunner bus object
        """
        return DBusRunner.__bus

    def is_active(self):
        """
        Return the current DBUS system bus.

        ``Return:`` Bool value
        """
        return self.__active

    @staticmethod
    def get_instance():
        """
        Singleton to return a DBusRunner object.

        ``Return:`` :class:`gosa.common.dbus_runner.DBusRunner`
        """
        if not DBusRunner.__instance:
            DBusRunner.__instance = DBusRunner()
        return DBusRunner.__instance
