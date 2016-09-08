# This file is part of the GOsa framework.
#
#  http://gosa-project.org
#
# Copyright:
#  (C) 2016 GONICUS GmbH, Germany, http://www.gonicus.de
#
# See the LICENSE file in the project's top-level directory for details.

import sys
import gettext
from pkg_resources import resource_filename
from gosa.common.components.auth import *
from u2flib_host import u2f

# Set locale domain
t = gettext.translation('messages', resource_filename("gosa.shell", "locale"), fallback=True)
_ = t.gettext


class ConsoleHandler(object):
    """ Handle authentication process on console """
    __username = None

    def __init__(self, proxy):
        self.proxy = proxy

    def login(self, username, password):
        """ start the login process """
        self.__username = username
        try:
            res = self.proxy.login(username, password)
            return self.__handle_result(res)
        except Exception:
            print(_("Login of user '%s' failed") % self.__username)
            sys.exit(1)

    def __handle_result(self, result_code):
        """
        Handle the results of the different login steps (login, 2FA, U2F) and process with
        the next required step until the login process succeeds or fails.
        """
        try:
            if result_code == AUTH_FAILED:
                print(_("Login of user '%s' failed") % self.__username)
                sys.exit(1)

            elif result_code == AUTH_OTP_REQUIRED:
                key = input(_("OTP-Passkey: "))
                return self.__handle_result(int(self.proxy.verify(key)))

            elif 'state' in result_code  and result_code['state'] == AUTH_U2F_REQUIRED and 'u2f_data' in result_code:
                for device in u2f.list_devices():
                    with device as dev:
                        data = u2f.authenticate(device, result_code['u2f_data'], self.proxy.get_facet())
                        res = self.proxy.verify(data)
                        if 'counter' in res and 'touch' in res:
                            return True

                return False
            elif result_code == AUTH_SUCCESS:
                return True

        except Exception as e:
            print(e)
            sys.exit(1)

        return False
