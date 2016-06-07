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
from gosa.core import Environment
from gosa import __version__ as VERSION
from flask import Flask
from gosa.core import WsgiApplication

app = Flask(__name__)

def shutdown():
    pass


def handleTermSignal(a=None, b=None):
    pass


def handleHupSignal(a=None, b=None):
    pass


def mainLoop(env):
    """
    Main event loop which will process all registerd threads in a loop.
    It will run as long env.active is set to True.
    """
    log = logging.getLogger(__name__)

    try:

        for entry in pkg_resources.iter_entry_points("gosa.plugin"):
            module = entry.load()
            log.debug("adding route %s" % entry.name)
            flask_view = module.as_view(entry.name)
            app.add_url_rule(entry.name, view_func=flask_view)

        WsgiApplication("gosa.main:app", env.config.getOptions('gunicorn')).run()

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
    env.log.info("GOsa %s is starting up" % VERSION)
    mainLoop(env)


if __name__ == '__main__':
    if not sys.stdout.encoding:
        sys.stdout = codecs.getwriter('utf8')(sys.stdout)
    if not sys.stderr.encoding:
        sys.stderr = codecs.getwriter('utf8')(sys.stderr)

    main()
