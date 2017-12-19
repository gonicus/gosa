#!/usr/bin/env python3
# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2010-2012 GONICUS GmbH, Germany, http://www.gonicus.de
#
# License:
#  GPL-2: http://www.gnu.org/licenses/gpl-2.0.html
#
# See the LICENSE file in the project's top-level directory for details.

import os
import sys
import time
import logging
import pkg_resources
import codecs
import traceback
from random import randint

from setproctitle import setproctitle
from gosa.common import Environment
from gosa.client import __version__ as VERSION
from gosa.common.components.registry import PluginRegistry
from gosa.common.components.dbus_runner import DBusRunner
from gosa.common.network import Monitor
from gosa.common.event import EventMaker

netstate = False

def shutdown(a=None, b=None):
    global dr

    env = Environment.getInstance()
    log = logging.getLogger(__name__)

    # Function to shut down the client. Do some clean up and close sockets.
    mqtt = PluginRegistry.getInstance("MQTTClientHandler")

    # Tell others that we're away now
    e = EventMaker()
    goodbye = e.Event(e.ClientLeave(e.Id(env.uuid)))
    if mqtt:
        mqtt.send_event(goodbye, qos=2)
        mqtt.close()

    # Shutdown plugins
    PluginRegistry.shutdown()

    #TODO: remove this hack
    wait = 1
    for t in env.threads:
        if t.isAlive():
            log.warning("thread %s still alive" % t.getName())
            if hasattr(t, 'stop'):
                log.warning("calling 'stop' for thread %s" % t.getName())
                t.stop()
            if hasattr(t, 'cancel'):
                log.warning("calling 'cancel' for thread %s" % t.getName())
                t.cancel()
            t.join(wait)

        if t.is_alive():
            try:
                log.warning("calling built in 'stop' for thread %s" % t.getName())
                t._stop()
            except:
                log.error("could not stop thread %s" % t.getName())

    dr.stop()

    log.info("shut down")
    logging.shutdown()


def mainLoop(env):
    global netstate, dr

    # Enable DBus runner
    dr = DBusRunner()
    dr.start()

    # Do network monitoring
    nm = Monitor(netactivity)
    netactivity(nm.is_online())

    """ Main event loop which will process all registered threads in a loop.
        It will run as long env.active is set to True."""
    try:
        log = logging.getLogger(__name__)

        while True:

            # Check netstate and wait until we're back online
            if not netstate:
                log.info("waiting for network connectivity")
            while not netstate:
                time.sleep(1)

            # Load plugins
            PluginRegistry(component='gosa.client.module')

            # Sleep and slice
            wait = 2
            while True:
                # Threading doesn't seem to work well with python...
                for p in env.threads:

                    # Bail out if we're active in the meanwhile
                    if not env.active:
                        break

                    p.join(wait)

                # No break, go to main loop
                else:
                    continue

                # Break, leave main loop
                break

            # Break, leave main loop
            if not env.reset_requested:
                break

            # Wait for threads to shut down
            for t in env.threads:
                if hasattr(t, 'stop'):
                    t.stop()
                if hasattr(t, 'cancel'):
                    t.cancel()
                t.join(wait)

                #TODO: remove me
                if t.is_alive():
                    try:
                        t._stop()
                    except:
                        print(str(t.getName()) + ' could not be terminated')

            # Lets do an environment reset now
            PluginRegistry.shutdown()

            # Make us active and loop from the beginning
            env.reset_requested = False
            env.active = True

            if not netstate:
                log.info("waiting for network connectivity")
            while not netstate:
                time.sleep(1)

            sleep = randint(30, 60)
            env.log.info("waiting %s seconds to try an MQTT connection recovery" % sleep)
            time.sleep(sleep)

    except Exception as detail:
        log.critical("unexpected error in mainLoop")
        log.exception(detail)
        log.debug(traceback.format_exc())

    except KeyboardInterrupt:
        log.info("console requested shutdown")

    finally:
        shutdown()


def netactivity(online):
    global netstate
    env = Environment.getInstance()
    if online:
        netstate = True
        env.active = True
    else:
        env = Environment.getInstance()
        netstate = False

        # Function to shut down the client. Do some clean up and close sockets.
        mqtt = PluginRegistry.getInstance("MQTTClientHandler")

        # Tell others that we're away now
        e = EventMaker()
        goodbye = e.Event(e.ClientLeave(e.Id(env.uuid)))
        if mqtt:
            mqtt.send_event(goodbye, qos=2)
            mqtt.close()

        env.reset_requested = True
        env.active = False


def main():
    """
    Main programm which is called when the GOsa backend process gets started.
    It does the main forking os related tasks.
    """

    # Set process list title
    os.putenv('SPT_NOENV', 'non_empty_value')
    setproctitle("gosa-client")

    # Initialize core environment
    env = Environment.getInstance()
    env.active = False

    env.log.info("GOsa client is starting up")

    mainLoop(env)


if __name__ == '__main__':
    if not sys.stdout.encoding:
        sys.stdout = codecs.getwriter('utf8')(sys.stdout)
    if not sys.stderr.encoding:
        sys.stderr = codecs.getwriter('utf8')(sys.stderr)

    pkg_resources.require('gosa.common==%s' % VERSION)

    netstate = False
    main()
