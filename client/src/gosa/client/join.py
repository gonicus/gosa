#!/usr/bin/env python3
# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

import signal
import sys
import re
import os
import gettext
import grp
import pkg_resources
from os.path import isdir, exists
from pkg_resources import resource_filename #@UnresolvedImport
from gosa.common import Environment
from gosa.common.config import ConfigNoFile
from operator import itemgetter

# Include locales
t = gettext.translation('messages', resource_filename("gosa.client", "locale"), fallback=True)
_ = t.ugettext
joiner = None


def signal_handler(signal, frame):
    joiner.end_gui()
    sys.exit(1)


def main():
    global joiner

    # Init handler
    signal.signal(signal.SIGINT, signal_handler)

    # Load modules
    modules = {}
    priority = {}
    for entry in pkg_resources.iter_entry_points("gosa.client.join.module"):
        mod = entry.load()
        if mod.available():
            priority[mod.__name__] = mod.priority
            modules[mod.__name__] = mod

    # Take the one with the highest priority
    module = sorted(priority.items(), key=itemgetter(1))[0][0]

    # Try to load environment. If it doesn't work, evaluate
    # config file from command line and create a default one.
    try:
        env = Environment.getInstance()
    except ConfigNoFile:
        config_file = os.environ.get("CLACKS_CONFIG_DIR") or "/etc/gosa"
        config_file = os.path.join(config_file, "config")
        service = None

        # Try to find config file without optparser
        for (i, arg) in enumerate(sys.argv):
            r = re.match(r"--config=(.*)", arg)
            if r:
                config_file = r.groups(0)[0]
                continue

            if arg == "--config" or arg == "-c":
                config_file = sys.argv[i + 1]
                continue

            r = re.match(r"--url=(.*)", arg)
            if r:
                service = r.groups(0)[0]
                continue

            if arg == "--url":
                service = sys.argv[i + 1]
                continue

        # Check if config path exists
        config_dir = os.path.dirname(config_file)
        if not exists(config_dir):
            os.mkdir(config_dir)

        if not isdir(config_dir):
            print("Error: configuration directory %s is no directory!" % config_dir)
            exit(1)

        # Read default config and write it back to config_file
        config = open(resource_filename("gosa.client", "data/client.conf")).read()
        if service:
            config = re.sub(r"#url = %URL%", "url = %s" % service, config)
        with open(config_file, "w") as f:
            f.write(config)

        # Nothing important here yet, but lock us down
        os.chmod(config_file, 0600)
        env = Environment.getInstance()

    # Instanciate joiner and ask for help
    joiner = modules[module]()
    if not joiner.test_login():
        joiner.join_dialog()

    # Fix configuration file permission
    cfg = env.config.get("core.config")
    group = env.config.get("client.group", default="gosa")
    try:
        gid = grp.getgrnam(group).gr_gid
    except KeyError as e:
        print("Error: failed to resolve user/group - %s" % str(e))
        exit(1)

    # Fix configuration file permission
    env.log.debug("setting ownership for '%s' to (%s/%s)" % (cfg, "root", group))
    os.chown(cfg, 0, gid)
    env.log.debug("setting permission for '%s' to (%s)" % (cfg, '0640'))
    os.chmod(cfg, 0750)

    cfg = os.path.join(cfg, "config")
    env.log.debug("setting ownership for '%s' to (%s/%s)" % (cfg, "root", group))
    os.chown(cfg, 0, gid)
    env.log.debug("setting permission for '%s' to (%s)" % (cfg, '0640'))
    os.chmod(cfg, 0640)


if __name__ == '__main__':
    # check for root permission
    if os.geteuid() != 0:
        print("Error: you need to be root to join to the GOsa infrastructure!")
        exit()

    main()
