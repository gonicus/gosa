#!/usr/bin/env python3
# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

print("This tool is still using AMQP. Needs to be revised.")
exit()

import os
from time import sleep
from datetime import datetime
from lxml import etree
from base64 import b64decode
from gosa.common import Environment
from gosa.common.utils import parseURL, makeAuthURL
from gosa.common.event import EventMaker
from gosa.common.components import AMQPServiceProxy


def tail(path):
    # Start listening from the end of the given path
    path.seek(0, 2)

    # Try to read until somthing new pops up
    while True:
         line = path.readline()

         if not line:
             sleep(0.1)
             continue

         yield line.strip()


def monitor(path, modifier, proxy):
    # Initialize dn, timestamp and change type.
    dn = None
    ts = None
    ct = None
    ch = False

    try:
        with open(path) as f:

            # Collect lines until a newline occurs, fill
            # dn, ts and ct accordingly. Entries that only
            # change administrative values.
            for line in tail(f):

                # Catch dn
                if line.startswith("dn::"):
                    dn = b64decode(line[5:])
                    continue

                elif line.startswith("dn:"):
                    dn = line[4:]
                    continue

                # Catch modifyTimestamp
                if line.startswith("modifyTimestamp:"):
                    ts = line[17:]
                    continue

                # Catch changetype
                if line.startswith("changetype:"):
                    ct = line[12:]
                    continue

                # Check modifiers name and if it's the
                # gosa-backend who triggered the change,
                # just reset the DN, because we don't need
                # to propagate this change.
                if  line.startswith("modifiersName:"):
                    if line[15:].lower() == modifier.lower():
                        dn = None
                    continue

                # Catch everything else except entryCSN and modifiersName
                if not (line.startswith("entryCSN:") or line.startswith("modifiersName")):
                    ch = True

                # Trigger on newline.
                if line == "":
                    if dn:
                        if not ts:
                            ts = datetime.now().strftime("%Y%m%d%H%M%SZ")

                        e = EventMaker()
                        update = e.Event(
                            e.BackendChange(
                                e.DN(dn),
                                e.ModificationTime(ts),
                                e.ChangeType(ct)
                            )
                        )

                        update = etree.tostring(update, pretty_print=True)
                        proxy.sendEvent(update)

                    dn = ts = ct = None
                    ch = False

    except Exception as e:
        print "Error:", str(e)


def main():
    env = Environment.getInstance()
    config = env.config

    # Load configuration
    path = config.get('backend-monitor.audit-log', default='/var/lib/gosa/ldap-audit.log')
    modifier = config.get('backend-monitor.modifier')
    user = config.get('core.id')
    password = config.get('amqp.key')
    url = parseURL(makeAuthURL(config.get('amqp.url'), user, password))

    # Connect to Clacks BUS
    proxy = AMQPServiceProxy(url['source'] + "/" + env.domain)

    # Main loop
    while True:
        sleep(1)

        # Wait for file to pop up
        if not os.path.exists(path):
            continue

        # Wait for file to be file
        if not os.path.isfile(path):
            continue

        # Check if it is effectively readable
        try:
            with open(path) as f:
                pass
        except IOError as e:
            continue

        # Listen for changes
        monitor(path, modifier, proxy)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
