# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

"""
This plugin is part of the shell extension module of gosa-dbus.

It starts a Thread and uses inotify to register itself to the kernel to receive
events about changes made in the shelld directory.

"""
import pyinotify
import logging
from gosa.common import Environment


class ShellDNotifier(pyinotify.ProcessEvent):
    """
    It monitors the gosa shell extension directory usually '/etc/gosa/shell.d'
    for modifications and executes the given callback if a modification was detected.

    =========== =====================
    Key         Desc
    =========== =====================
    path        The path to check modification for
    callback    A function to call, once we detected a modification.
    =========== =====================

    """
    path = None
    callback = None

    def __init__(self, path, callback):

        # Initialize the plugin and set path
        self.bp = self.path = path
        self.callback = callback
        self.env = Environment.getInstance()
        self.log = logging.getLogger(__name__)

        # Start the files ystem surveillance thread now
        self.__start()

    def __start(self):
        """
        Starts the survailance. This is automatically called in the constructor.
        """
        wm = pyinotify.WatchManager()
        res = wm.add_watch(self.path, pyinotify.IN_MOVED_FROM | pyinotify.IN_ATTRIB | pyinotify.IN_MODIFY | pyinotify.IN_DELETE | pyinotify.IN_MOVED_TO, rec=True, auto_add=True) #@UndefinedVariable
        if self.path not in res or res[self.path] != 1:
            raise Exception("failed to add watch to '%s'" % (self.path,))

        notifier = pyinotify.ThreadedNotifier(wm, self)
        notifier.daemon = True
        notifier.start()

    def process_IN_MOVED_TO(self, event):
        """
        Method to process moved files
        """
        self.__handle(event.pathname)

    def process_IN_MOVED_FROM(self, event):
        """
        Method to process moved files
        """
        self.__handle(event.pathname)

    def process_IN_ATTRIB(self, event):
        """
        Method to process attribute modification events
        """
        self.__handle(event.pathname)

    def process_IN_MODIFY(self, event):
        """
        Method to process file modifications events
        """
        self.__handle(event.pathname)

    def process_IN_DELETE(self, event):
        """
        Method to process file delete events
        """
        self.__handle(event.pathname)

    def __handle(self, path):
        """
        This method call the 'callback' method once it receives a
        kernel event about moved ot modified files.
        """

        # Use the callback method to announce the new change event
        self.callback(path)
