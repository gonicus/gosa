#!/usr/bin/env python3
# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

import warnings
warnings.filterwarnings("ignore")

import os
import re
import sys
import grp
import dbus
from argparse import ArgumentParser
import pwd
import getpass
import signal

# Define return codes
RETURN_ABORTED = 0b10000000
RETURN_TIMEDOUT = 0b1000000
RETURN_CLOSED = 0b0


class Notify(object):
    """
    Allows to send desktop notifications to users.
    """
    __loop = None
    quiet = False
    verbose = False
    children = []

    def __init__(self, quiet=False, verbose=False):
        self.quiet = quiet
        self.verbose = verbose

    def __close(self, *args, **kwargs):

        """
        Closes the current show notification and its mainloop if it exists.
        """
        if self.verbose:
            print("%s: Closing" % (str(os.getpid())))

        if self.__loop:
            self.__loop.quit()

    def send(self, title, message, dbus_session,
        icon="",
        timeout=5000,
        **kwargs):
        """
        send initiates the notification with the given option details.
        """

        # Prepare timeout, use seconds not milliseconds
        if timeout != 5000:
            timeout *= 1000

        # Initially start with result id -1
        self.__res = -1

        # If a list of dbus session addresses was given then
        #  initiate a notification for each.
        if not dbus_session:

            # No dbus session was specified, abort here.
            if not self.quiet:
                print("Requires a DBUS address to send notifications")

            return(RETURN_ABORTED)

        else:
            # Build notification
            notifyid = 0
            try:
                bus = dbus.connection.Connection._new_for_bus(dbus_session)
            except dbus.exceptions.DBusException:
                if not self.quiet:
                    print("Connecting to dbus at '%s' failed." % dbus_session)
                return RETURN_ABORTED
            notifyservice = bus.get_object('org.freedesktop.Notifications', '/org/freedesktop/Notifications')
            notifyservice = dbus.Interface(notifyservice, "org.freedesktop.Notifications")

            # Maybe clean before sending around
            capabilities = notifyservice.GetCapabilities()

            if not "body-markup" in capabilities:
                message = re.sub('<[^<]+?>', '', message)
            if not "body-hyperlinks" in capabilities:
                message = re.sub(r'(<a[^>]*>|</a>)', '', message)

            self.notifyid = notifyservice.Notify("Gosa Client", notifyid, icon, title, message, [], {}, timeout)

        return RETURN_CLOSED

    def send_to_user(self, title, message, user,
        icon="dialog-information",
        timeout=5000,
        **kwargs):

        """
        Sends a notification message to a given user.
        """

        # Use current user if none was given
        if not user:
            user = getpass.getuser()

        # Send the notification to each found dbus address
        dbus_sessions = self.getDBUSAddressesForUser(user)
        res = None
        if not dbus_sessions:
            if not self.quiet:
                print("No DBUS sessions found for user " + user)

            res = RETURN_ABORTED
        else:

            # Walk through found dbus sessions and fork a process for each
            parent_pid = os.getpid()
            self.children = []
            for use_user in dbus_sessions:
                for d_session in set(dbus_sessions[use_user]):
                    # Some verbose output
                    if self.verbose:
                        print("\nInitiating notifications for user: %s" % use_user)
                        print("Session: %s" % d_session)

                    # Detecting groups for user
                    gids = []
                    for agrp in grp.getgrall():
                        if use_user in agrp.gr_mem:
                            gids.append(agrp.gr_gid)

                    # Get system information for the user
                    info = pwd.getpwnam(use_user)

                    # Fork a new sub-process to be able to set the user details
                    # in a save way, the parent should not be affected by this.
                    child_pid = os.fork()

                    # Call the send method in the fork only
                    if child_pid == 0:

                        if self.verbose:
                            print("%s: Forking process for user %s" % (str(os.getpid()), str(info[2])))

                        # Set the users groups
                        if os.geteuid() != info[2]:
                            os.setgroups(gids)
                            os.setgid(info[3])
                            os.seteuid(info[2])

                        # Act on termniation events this process receives,
                        #  by closing the main loop and the notification window.
                        signal.signal(signal.SIGTERM, self.__close)

                        if self.verbose:
                            print("%s: Setting process uid(%s), gid(%s) and groups(%s)" % (
                                str(os.getpid()), str(info[2]), str(info[3]), str(gids)))

                        # Try to send the notification now.
                        res = self.send(title, message, d_session, icon=icon,
                            timeout=timeout)

                        # Exit the cild process
                        sys.exit(res)
                    else:
                        self.children.append(child_pid)

            # Wait for first child returning with an return code.
            if os.getpid() == parent_pid:

                try:
                    # Get the cild process return code.
                    ret_code = os.waitpid(-1, 0)[1]

                    # Dont know why, but we receive an 16 Bit long return code,
                    # but only send an 8 Bit value.
                    res = ret_code >> 8

                except KeyboardInterrupt:
                    res = RETURN_ABORTED
                    pass

                # Now kill all remaining children
                for pid in self.children:
                    try:
                        os.kill(pid, signal.SIGTERM)
                        if self.verbose:
                            print("Killed process %s" % pid)
                    except Exception:
                        pass

        return res

    def getDBUSAddressesForUser(self, user):
        """
        Obtains a list with logged in users from the login manager per dbus
        and looks for the dbus adress given in the .dbus directories in their
        homes.
        """

        obj = dbus.SystemBus().get_object("org.freedesktop.login1",
            "/org/freedesktop/login1")
        interface = dbus.Interface(obj, "org.freedesktop.login1.Manager")
        sessions = {}

        for uid_number, uid, user_path in interface.ListUsers():
            uid_number = int(uid_number)
            uid = str(uid)
            userdbusdir = os.path.join("/home", uid, ".dbus/session-bus")
            if uid_number >= 1000 and (user == uid or user == "*") and os.path.isdir(userdbusdir):
                ids = os.listdir(userdbusdir)
                assert len(ids) == 1
                with open(os.path.join(userdbusdir, ids[0])) as f:
                    lines = f.readlines()
                dbusvars = {}
                for line in lines:
                    line = line.strip()
                    if line.startswith("#"):
                        continue
                    if "=" in line:
                        key, value = line.split("=", 1)
                        dbusvars[key] = value.split(",")[0]
                if not "DBUS_SESSION_BUS_ADDRESS" in dbusvars:
                    continue
                sessions[uid] = [dbusvars["DBUS_SESSION_BUS_ADDRESS"]]
        return sessions


def main():

    # Define cli-script parameters
    parser = ArgumentParser(description="Sends a notification dialog "
        "to a user on the local machine.")

    parser.add_argument("title")
    parser.add_argument("message")
    parser.add_argument("-i", "--icon", dest="icon", default="dialog-information",
        help="An icon file to use in the notifcation", metavar="FILE")
    parser.add_argument("-t", "--timeout", dest="timeout",
        help="Seconds the notification is displayed")
    parser.add_argument("-u", "--user", dest="user", help="The target user")
    parser.add_argument("-b", "--broadcast", action="store_true", dest="to_all",
        default=False, help="send message to all users")
    parser.add_argument("-q", "--quiet", action="store_true", dest="quiet",
        default=False, help="don't print status messages to stdout")
    parser.add_argument("-v", "--verbose", action="store_true", dest="verbose",
        default=False, help="Run in verbose mode")

    # Check if at least 'message' and 'title' are given.
    options = parser.parse_args()

    # Check if we've to send the message to all users instead of just one.
    if options.to_all:

        # Check if --user/-u was specified additionally.
        if options.user and not options.quiet:
            print("The option -b/--broadcast cannot be combined with the option -u/--user")

        options.user = "*"

    # If verbose output is enabled, then disable quiet mode.
    if options.verbose:
        options.quiet = False

    # Ensure that the timeout is valid
    if options.timeout:
        options.timeout = int(options.timeout)
    else:
        options.timeout = 5000

    # Create notifcation object
    n = Notify(options.quiet, options.verbose)

    # Call the send method for our notification instance
    sys.exit(n.send_to_user(options.title, options.message, user=options.user, icon=options.icon,
        timeout=options.timeout))


if __name__ == '__main__':
    main()
