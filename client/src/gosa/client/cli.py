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
import locale
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
from gosa.common.components import JSONServiceProxy, JSONRPCException
from gosa.common.components.dbus_runner import DBusRunner
from gosa.common.components.registry import PluginRegistry
from gosa.common.error import GosaErrorHandler
from gosa.common.gjson import dumps

t = gettext.translation('messages', resource_filename("gosa.client", "locale"), fallback=True)
_ = t.gettext

log = logging.getLogger(__name__)


class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def connect():
    PluginRegistry.modules["ClientCommandRegistry"] = ClientCommandRegistry()
    PluginRegistry.modules["MQTTClientService"] = MQTTClientService()

    env = Environment.getInstance()
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
            return proxy

    except HTTPError as e:
        if e.code == 401:
            log.error("connection to GOsa backend failed")
            print(_("Cannot join client: check user name or password!"))
            return False
        else:
            print("Error: %s " % str(e))
            raise e

    except Exception as e:
        print("Error: %s " % str(e))
        raise e


def notify_backend(options):
    """
    Notify backend about user session
    """

    mode = options.mode
    user = options.user
    if user is None:
        user = os.getlogin()

    proxy = connect()
    if proxy is not False:
        dbus_proxy = DBUSProxy()
        dbus_proxy.serve(register_methods=False)
        env = Environment.getInstance()
        sys_id = env.config.get("core.id", default=None)

        if mode == "start":
            print("calling preUserSession...")
            try:
                config = proxy.preUserSession(sys_id, user)
            except JSONRPCException as e:
                handle_error(proxy, e)
                return

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
            print("calling postUserSession...")
            try:
                print("postUserSession returned: %s" % proxy.postUserSession(sys_id, user))
            except JSONRPCException as e:
                handle_error(proxy, e)


def get_destination_indicator(options):

    client_id = options.client
    env = Environment.getInstance()
    if client_id is None:
        client_id = env.uuid
    user = options.user
    if user is None:
        user = os.getlogin()

    proxy = connect()
    if proxy is not False:
        try:
            di = proxy.getDestinationIndicator(client_id, user, options.filter)
            print(di)
        except JSONRPCException as e:
            handle_error(proxy, e)


def handle_error(proxy, e):
    # Check for error member
    try:
        err = e.error["error"]
    except Exception:
        err = str(e)
    # Resolve error details if supplied
    error_id = GosaErrorHandler.get_error_id(err)
    if error_id:
        locs = locale.getdefaultlocale()
        info = proxy.getError(error_id, ".".join(locs if locs != (None, None) else ("en_US", "UTF-8")))
        detail = ""
        if info['details']:
            detail = " - %s [%s]" % (info['details'][0]['detail'], info['details'][0]['index'])
        if info['topic']:
            print(bcolors.FAIL + info['text'] + detail + ": " + info['topic'])
        else:
            print(bcolors.FAIL + info['text'] + detail)
    else:
        print(bcolors.FAIL + str(err))


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

    commands = {
        'session': {
            'command': notify_backend,
            'help': 'Get destination indicator for user.',
            'arguments': [
                {
                    'args': ('-u', '--user'),
                    'kwargs': {'dest': 'user', 'type': str, 'help': 'user name'}
                },
                {
                    'args': ('-m', '--mode'),
                    'kwargs': {'dest': 'mode', 'type': str, 'help': '"start" or "end" to specify the user session state'}
                }
            ],

        },
        'getDestinationIndicator': {
            'command': get_destination_indicator,
            'help': 'Notify backend about user sessions and retrieve the user configuration.',
            'arguments': [
                {
                    'args': ('-u', '--user'),
                    'kwargs': {'dest': 'user', 'type': str, 'help': 'user name'}
                },
                {
                    'args': ('-c', '--client'),
                    'kwargs': {'dest': 'client', 'type': str, 'help': 'client id'}
                },
                {
                    'args': ('-f', '--filter'),
                    'kwargs': {'dest': 'filter', 'type': str, 'help': 'cn filter for the server query', 'required': True}
                }
            ]
        }
    }

    description = 'Helper commands to allow communication with the GOsa backend.'
    parser = argparse.ArgumentParser(description=description)
    subparsers = parser.add_subparsers(help='available actions', dest='action')

    for command_name, config in commands.items():
        sub_parser = subparsers.add_parser(command_name, help=config['help'])
        for argument in config['arguments']:
            sub_parser.add_argument(*argument['args'], **argument['kwargs'])

    options = parser.parse_args()

    # Initialize core environment
    if options.action in commands:
        commands[options.action]['command'](options)
    elif options.action is None:
        parser.print_help()
    else:
        print(bcolors.WARNING + _("action '%s' is not available" % options.action))
        sys.exit(1)


if __name__ == '__main__':
    if not sys.stdout.encoding:
        sys.stdout = codecs.getwriter('utf8')(sys.stdout)
    if not sys.stderr.encoding:
        sys.stderr = codecs.getwriter('utf8')(sys.stderr)

    pkg_resources.require('gosa.common==%s' % VERSION)

    netstate = False
    main()
