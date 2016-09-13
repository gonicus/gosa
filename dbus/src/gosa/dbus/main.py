#!/usr/bin/env python3
# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

import os
import sys
import pkg_resources
import codecs
import traceback
from gi.repository import GLib
import dbus.mainloop.glib
import logging

from setproctitle import setproctitle
from gosa.common import Environment
from gosa.dbus import __version__ as VERSION
from gosa.common.components.registry import PluginRegistry
from gosa.dbus import get_system_bus

loop = None


def shutdown(a=None, b=None):
    """ Function to shut down the client. """
    global loop

    env = Environment.getInstance()
    env.log.info("GOsa DBUS is shutting down")

    # Shutdown plugins
    PluginRegistry.shutdown()
    if loop:
        loop.quit()

    logging.shutdown()
    exit(0)


def mainLoop(env):
    global loop

    log = logging.getLogger(__name__)

    try:
        # connect to dbus and setup loop
        dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
        get_system_bus()

        # Instanciate dbus objects
        PluginRegistry(component='gosa.dbus.module')

        # Enter main loop
        loop = GLib.MainLoop()
        loop.run()

    except Exception as detail:
        log.critical("unexpected error in mainLoop")
        log.exception(detail)
        log.debug(traceback.format_exc())

    finally:
        shutdown()


def main():
    """ Main programm which is called when the gosa agent process gets started.
        It does the main forking os related tasks. """

    # Set process list title
    os.putenv('SPT_NOENV', 'non_empty_value')
    setproctitle("gosa-dbus")

    # Inizialize core environment
    env = Environment.getInstance()
    env.log.info("GOsa DBUS is starting up")

    # Are we root?
    if os.geteuid() != 0:
        env.log.critical("GOsa DBUS must be run as root")
        exit(1)

    mainLoop(env)


if __name__ == '__main__':  # pragma: nocover
    if not sys.stdout.encoding:
        sys.stdout = codecs.getwriter('utf8')(sys.stdout)
    if not sys.stderr.encoding:
        sys.stderr = codecs.getwriter('utf8')(sys.stderr)

    pkg_resources.require('gosa.common==%s' % VERSION)

    main()
