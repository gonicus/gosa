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
from gosa.client.plugins.join.methods import join_method
from pkg_resources import resource_filename #@UnresolvedImport

# Include locales
from gosa.common import Environment

t = gettext.translation('messages', resource_filename("gosa.client", "locale"), fallback=True)
_ = t.gettext


class Otp(join_method):
    priority = 0

    def __init__(self, parent=None):
        super(Otp, self).__init__()

    def join_dialog(self):
        env = Environment.getInstance()
        self.join(env.config.get("core.id"), env.config.get("core.otp"))

    def show_error(self, error):
        print(_("Error") + ": " + error)
        time.sleep(3)

    def modify_config(self, parser):
        # delete OTP after successful join
        parser.remove_option("core", "otp")

    @staticmethod
    def available():
        # This should always work
        try:
            env = Environment.getInstance()
            return env.config.get("core.otp") is not None
        except:
            return False
