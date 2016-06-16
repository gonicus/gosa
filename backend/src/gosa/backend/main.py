#!/usr/bin/env python
# This file is part of the GOsa project.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

import os
import sys
import logging
import pkg_resources
import codecs
from setproctitle import setproctitle
from gosa.backend import __version__ as VERSION
from gosa.common import Environment
from gosa.common.components import ObjectRegistry, PluginRegistry


def shutdown():
    """
    Function to shut down the backend. Do some clean up and close sockets.
    """
    # Shutdown plugin registry
    PluginRegistry.shutdown()

    logging.info("shut down")
    logging.shutdown()


def mainLoop(env):
    """
    Main event loop which will process all registerd threads in a loop.
    It will run as long env.active is set to True.
    """
    log = logging.getLogger(__name__)

    try:
        # Load plugins
        oreg = ObjectRegistry.getInstance() #@UnusedVariable
        pr = PluginRegistry() #@UnusedVariable
        cr = PluginRegistry.getInstance("CommandRegistry")

        httpd = PluginRegistry.getInstance("HTTPService")
        httpd.thread.join()

    # Catchall, pylint: disable=W0703
    except Exception as detail:
        log.critical("unexpected error in mainLoop")
        log.exception(detail)

    except KeyboardInterrupt:
        log.info("console requested shutdown")

    finally:
        shutdown()


def main():
    """
    Main programm which is called when the GOsa backend process gets started.
    It does the main forking os related tasks.
    """

    # Set process list title
    os.putenv('SPT_NOENV', 'non_empty_value')
    setproctitle("gosa")

    # Inizialize core environment
    env = Environment.getInstance()
    if not env.base:
        env.log.critical("GOsa backend needs a 'core.base' do operate on")
        exit(1)

    env.log.info("GOsa %s is starting up" % VERSION)
    mainLoop(env)


if __name__ == '__main__':
    if not sys.stdout.encoding:
        sys.stdout = codecs.getwriter('utf8')(sys.stdout)
    if not sys.stderr.encoding:
        sys.stderr = codecs.getwriter('utf8')(sys.stderr)

    pkg_resources.require('gosa.common==%s' % VERSION)
    main()
