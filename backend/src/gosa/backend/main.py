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
import signal
from setproctitle import setproctitle
from gosa.backend import __version__ as VERSION
from gosa.common import Environment
from gosa.common.components import ObjectRegistry, PluginRegistry
from tornado.ioloop import IOLoop
import tornado.web


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

        routes = []
        # Install routes for flask
        for entry in pkg_resources.iter_entry_points("gosa.route"):
            module = entry.load()
            log.debug("adding route %s" % entry.name)
            routes.append((entry.name, module))

        log.debug(routes)
        application = tornado.web.Application(handlers=routes, debug=True)

        # Run web service
        application.listen(8000)
        signal.signal(signal.SIGINT, lambda x, y: IOLoop.instance().stop())
        IOLoop.instance().start()

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
    Main programm which is called when the clacks agent process gets started.
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
