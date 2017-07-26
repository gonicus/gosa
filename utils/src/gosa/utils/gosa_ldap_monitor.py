#!/usr/bin/env python3
# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

import hmac
import os
from time import sleep
from datetime import datetime
import requests
from lxml import etree
from base64 import b64decode
from gosa.common import Environment
from gosa.common.event import EventMaker


def tail(path, initially_failed=False):
    # Start listening from the end of the given path
    if not initially_failed:
        path.seek(0, 2)

    # Try to read until something new pops up
    while True:
        line = path.readline()

        if not line:
            sleep(0.1)
            continue

        yield line.strip()


def get_signature(token, payload):
    signature_hash = hmac.new(token, msg=payload, digestmod="sha512")
    return 'sha1=' + signature_hash.hexdigest()


def monitor(path, modifier, token, webhook_target, initially_failed=False):
    # Initialize dn, timestamp and change type.
    dn = None
    ts = None
    ct = None

    try:
        with open(path, encoding='utf-8', errors='ignore') as f:

            # Collect lines until a newline occurs, fill
            # dn, ts and ct accordingly. Entries that only
            # change administrative values.
            for line in tail(f, initially_failed):

                # Catch dn
                if line.startswith("dn::"):
                    dn = b64decode(line[5:]).decode('utf-8')
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
                if line.startswith("modifiersName:"):
                    if line[15:].lower() == modifier:
                        dn = None
                    continue

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
                        payload = etree.tostring(update)

                        headers = {
                            'Content-Type': 'application/vnd.gosa.event+xml',
                            'HTTP_X_HUB_SENDER': 'backend-monitor',
                            'HTTP_X_HUB_SIGNATURE': get_signature(token, payload)
                        }
                        requests.post(webhook_target, data=payload, headers=headers)

                    dn = ts = ct = None

    except Exception as e:
        print("Error:", str(e))


def main():  # pragma: nocover
    env = Environment.getInstance()
    config = env.config

    # Load configuration
    path = config.get('backend-monitor.audit-log', default='/var/lib/gosa/ldap-audit.log')
    webhook_target = config.get('backend-monitor.webhook-target', default='http://localhost:8000/hooks')
    token = bytes(config.get('backend-monitor.webhook-token'), 'ascii')
    modifier = config.get('backend-monitor.modifier').lower()

    if token is None:
        print("Error: no webhook token found")
        return

    # Main loop
    initially_failed = False
    while True:
        sleep(1)

        # Wait for file to pop up
        if not os.path.exists(path):
            initially_failed = True
            continue

        # Wait for file to be file
        if not os.path.isfile(path):
            initially_failed = True
            continue

        # Check if it is effectively readable
        try:
            with open(path):
                pass
        except IOError:
            initially_failed = True
            continue

        # Listen for changes
        monitor(path, modifier, token, webhook_target, initially_failed)


if __name__ == "__main__":  # pragma: nocover
    try:
        main()
    except KeyboardInterrupt:
        pass
