# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

import time
import gettext
import getpass
from gosa.client.plugins.join.methods import join_method
from pkg_resources import resource_filename #@UnresolvedImport
import socket

# Include locales
t = gettext.translation('messages', resource_filename("gosa.client", "locale"), fallback=True)
_ = t.gettext


class Cli(join_method):
    priority = 99

    def __init__(self, parent=None):
        super(Cli, self).__init__()

    def join_dialog(self):
        key = None

        while not key:
            print(_("Please enter username and password to join the GOsa infrastructure."))
            username = input(_("User name [%s]: ") % getpass.getuser())
            password = getpass.getpass(_("Password") + ": ")
            data = dict()
            data['hostname'] = socket.gethostname()
            data['ipHostNumber'] = socket.gethostbyname(data['hostname'])
            key = self.join(username, password, data)

    def show_error(self, error):
        print(_("Error") + ": " + error)
        time.sleep(3)

    @staticmethod
    def available():
        # This should always work
        return True
