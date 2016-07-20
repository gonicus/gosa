# This file is part of the clacks framework.
#
#  http://clacks-project.org
#
# Copyright:
#  (C) 2010-2012 GONICUS GmbH, Germany, http://www.gonicus.de
#
# License:
#  GPL-2: http://www.gnu.org/licenses/gpl-2.0.html
#
# See the LICENSE file in the project's top-level directory for details.

"""
.. _dbus-notify:

Clacks D-Bus Notification Plugin
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This plugin allows to notify a single or all users on the client.

"""

import dbus.service
from clacks.common import Environment
from clacks.common.components import Plugin
from clacks.dbus import get_system_bus
import sys
import traceback
import subprocess


class DBusNotifyHandler(dbus.service.Object, Plugin):
    """
    This dbus plugin is able to send notification to the user using the
    systems D-Bus.

    This plugin exports dbus methods that ``cannot`` be accessed directly through
    the clacks-client DBus-Proxy.

    For details on how to use the user notification please see: :class:`clacks.client.plugins.notify.utils.Notify`.

    """

    def __init__(self):
        conn = get_system_bus()
        dbus.service.Object.__init__(self, conn, '/org/clacks/notify')
        self.env = Environment.getInstance()

    @dbus.service.method('org.clacks', in_signature='ssis', out_signature='i')
    def _notify_all(self, title, message, timeout, icon):
        """
        Try to send a notification to all users on a machine user using the 'notify-user' script.
        """
        return(self.call(message=message, title=title, broadcast=True, timeout=timeout,
            icon=icon))

    @dbus.service.method('org.clacks', in_signature='sssis', out_signature='i')
    def _notify(self, user, title, message, timeout, icon):
        """
        Try to send a notification to a user using the 'notify-user' script.
        """
        return(self.call(message=message, title=title, user=user, timeout=timeout,
            icon=icon))

    def call(self, message, title,
        user="",
        broadcast=False,
        timeout=120,
        actions="",
        icon="dialog-information"):

        try:

            # Build up the subprocess command
            # and add parameters on demand.
            cmd = ["notify-user"]
            cmd += [title]
            cmd += [message]

            if broadcast:
                cmd += ["--broadcast"]
            else:
                cmd += ["--user"]
                cmd += [str(user)]

            if icon:
                cmd += ["--icon"]
                cmd += [str(icon)]

            if actions:
                cmd += ["--actions"]
                cmd += [str(actions)]

            if timeout:
                cmd += ["--timeout"]
                cmd += [str(timeout)]

            ret = subprocess.call(cmd)
            return int(ret)

        except Exception:
            traceback.print_exc(file=sys.stdout)
