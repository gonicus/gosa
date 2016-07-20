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

import time
import gettext
import getpass
from gosa.client.plugins.join.methods import join_method
from pkg_resources import resource_filename #@UnresolvedImport

# Include locales
t = gettext.translation('messages', resource_filename("clacks.client", "locale"), fallback=True)
_ = t.ugettext


class Cli(join_method):
    priority = 99

    def __init__(self, parent=None):
        super(Cli, self).__init__()

    def join_dialog(self):
        key = None

        while not key:
            print(_("Please enter username and password to join the clacks infrastructure."))
            username = raw_input(_("User name [%s]: ") % getpass.getuser())
            password = getpass.getpass(_("Password") + ": ")
            key = self.join(username, password)

    def show_error(self, error):
        print(_("Error") + ": " + error)
        time.sleep(3)

    @staticmethod
    def available():
        # This should always work
        return True
