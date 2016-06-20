# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

import time
import datetime
from inspect import stack
from gosa.common import Environment


class GlobalLock(object):

    instance = None
    __locks = None

    def __init__(self):
        self.env = Environment.getInstance()
        self.__locks = {}

    def _exists(self, name):
        if self.__locks[name]:
            return True
        return False

    def _acquire(self, name, blocking=True, timeout=None):
        if blocking:
            t0 = time.time()
            # Blocking, but we may have to wait
            while self._exists(name):
                time.sleep(1)
                if timeout and time.time() - t0 > timeout:
                    return False

        elif self._exists(name):
            # Non blocking, but exists
            return False

        self.__locks[name] = True
        return True

    def _release(self, name):
        if name in self.__locks:
            del self.__locks[name]

    @staticmethod
    def acquire(name=None, blocking=True, timeout=None):
        if not name:
            name = stack()[1][3]

        gl = GlobalLock.get_instance()
        return gl._acquire(name, blocking, timeout)

    @staticmethod
    def release(name=None):
        if not name:
            name = stack()[1][3]

        GlobalLock.get_instance()._release(name)

    @staticmethod
    def exists(name=None):
        if not name:
            name = stack()[1][3]

        return GlobalLock.get_instance()._exists(name)

    @staticmethod
    def get_instance():
        if not GlobalLock.instance:
            GlobalLock.instance = GlobalLock()

        return GlobalLock.instance
