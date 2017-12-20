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
import argparse
import codecs
import gettext
import os
import sys
import logging
from urllib.parse import urlparse

import pkg_resources
from pkg_resources import resource_filename
from setproctitle import setproctitle
from gosa.client import __version__ as VERSION
from requests import HTTPError

from gosa.client.command import ClientCommandRegistry
from gosa.client.mqtt_service import MQTTClientService
from gosa.client.plugins.dbus.proxy import DBUSProxy
from gosa.common import Environment
from gosa.common.components import JSONServiceProxy
from gosa.common.components.dbus_runner import DBusRunner
from gosa.common.components.registry import PluginRegistry
from gosa.common.gjson import dumps

t = gettext.translation('messages', resource_filename("gosa.client", "locale"), fallback=True)
_ = t.gettext


def notify_backend(env, mode, user):

    """ Main event loop which will process all registered threads in a loop.
        It will run as long env.active is set to True."""
    log = logging.getLogger(__name__)

    PluginRegistry.modules["ClientCommandRegistry"] = ClientCommandRegistry()
    PluginRegistry.modules["MQTTClientService"] = MQTTClientService()

    dbus_proxy = DBUSProxy()
    dbus_proxy.serve(register_methods=False)

    url = env.config.get("jsonrpc.url", default=None)
    sys_id = env.config.get("core.id", default=None)
    key = env.config.get("jsonrpc.key", default=None)

    # Prepare URL for login
    url = urlparse(url)

    # Try to log in with provided credentials
    connection = '%s://%s%s' % (url.scheme, url.netloc, url.path)
    proxy = JSONServiceProxy(connection)

    # Try to log in
    try:
        if not proxy.login(sys_id, key):
            log.error("connection to GOsa backend failed")
            print(_("Cannot join client: check user name or password!"))
            return False
        else:
            if mode == "start":
                config = proxy.preUserSession(sys_id, user)
                # send config to dbus
                if "menu" in config:
                    # send to client
                    print("sending generated menu for user '%s'" % user)
                    dbus_proxy.callDBusMethod("dbus_configureUserMenu", user, dumps(config["menu"]))

                if "printer-setup" in config and "printers" in config["printer-setup"]:
                    dbus_proxy.callDBusMethod("dbus_deleteAllPrinters")
                    for p_conf in config["printer-setup"]["printers"]:
                        print("adding printer '%s'" % p_conf["cn"])
                        p = {key: value if value is not None else "" for (key, value) in p_conf.items()}
                        dbus_proxy.callDBusMethod("dbus_addPrinter", p)

                    if "defaultPrinter" in config["printer-setup"] and config["printer-setup"]["defaultPrinter"] is not None:
                        print("setting '%s' as default printer" % config["printer-setup"]["defaultPrinter"])
                        dbus_proxy.callDBusMethod("dbus_defaultPrinter", config["printer-setup"]["defaultPrinter"])

                if "resolution" in config and config["resolution"] is not None and len(config["resolution"]):
                    print("sending screen resolution: %sx%s for user %s" % (config["resolution"][0], config["resolution"][1], user))
                    dbus_proxy.callDBusMethod("dbus_configureUserScreen", user, config["resolution"][0], config["resolution"][1])

            elif mode == "end":
                    proxy.postUserSession(sys_id, user)
    except HTTPError as e:
        if e.code == 401:
            log.error("connection to GOsa backend failed")
            print(_("Cannot join client: check user name or password!"))
            return False
        else:
            print("Error: %s " % str(e))
            sys.exit(1)

    except Exception as e:
        print("Error: %s " % str(e))
        sys.exit(1)


def main():
    """
    Main programm which is called when the GOsa backend process gets started.
    It does the main forking os related tasks.
    """

    # Enable DBus runner
    dr = DBusRunner()
    dr.start()

    # Set process list title
    os.putenv('SPT_NOENV', 'non_empty_value')
    setproctitle("gosa-session")

    description = 'Helper commands to notify the GOsa backend about active user sessions on the client.'
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('-m', '--mode', dest="mode", type=str, help='"start" or "end" to specify the user session state')
    parser.add_argument('-u', '--user', dest="user", type=str, help='user name')

    options, unknown = parser.parse_known_args()

    # Initialize core environment
    env = Environment.getInstance()
    notify_backend(env, options.mode, options.user)


if __name__ == '__main__':
    if not sys.stdout.encoding:
        sys.stdout = codecs.getwriter('utf8')(sys.stdout)
    if not sys.stderr.encoding:
        sys.stderr = codecs.getwriter('utf8')(sys.stderr)

    pkg_resources.require('gosa.common==%s' % VERSION)

    netstate = False
    main()
