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

import curses
import time
import gettext
from clacks.client.plugins.join.methods import join_method
from pkg_resources import resource_filename #@UnresolvedImport

# Include locales
t = gettext.translation('messages', resource_filename("clacks.client", "locale"), fallback=True)
_ = t.ugettext


class CursesGUI(join_method):
    priority = 90

    def __init__(self, parent=None):
        super(CursesGUI, self).__init__()

    def start_gui(self):
        self.screen = curses.initscr()
        self.height, self.width = self.screen.getmaxyx()

        # Colors
        curses.start_color()
        curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLUE)

        # Refresh screen
        self.screen.bkgd(curses.color_pair(1))
        self.screen.refresh()

    def end_gui(self):
        curses.endwin()

    def get_pw(self):
        curses.noecho()
        curses.cbreak()
        password = ""
        pos = 0
        self.screen.move(self.start_y + 4, self.start_x + 11 + pos)

        while 1:
            c = self.screen.getch()
            if c == 10:
                break
            elif c == 127:

                if (pos > 0):
                    pos = pos - 1

                self.screen.move(self.start_y + 4, self.start_x + 11 + pos)
                self.screen.addch(" ")
                self.screen.move(self.start_y + 4, self.start_x + 11 + pos)
                self.screen.refresh()
                password = password[0:len(password) - 1]
            else:
                self.screen.move(self.start_y + 4, self.start_x + 11 + pos)
                pos = pos + 1
                self.screen.addch("*")
                self.screen.refresh()
                password = password + chr(c)

        curses.nocbreak()
        curses.echo()

        return password

    def join_dialog(self):
        key = None
        self.start_gui()

        headline = _("Please enter the credentials of an administrative user to join this client.")
        self.start_x = (self.width - len(headline)) / 2 - 1
        self.start_y = self.height / 2 - 5

        while not key:
            self.screen.addstr(self.start_y, self.start_x, headline)
            self.screen.addstr(self.start_y + 1, self.start_x, "(" + _("Press Ctrl-C to cancel") + ")")
            self.screen.addstr(self.start_y + 3, self.start_x, _("User name") + ":")
            self.screen.addstr(self.start_y + 4, self.start_x, _("Password") + ":")
            self.screen.refresh()

            username = self.screen.getstr(self.start_y + 3, self.start_x + 11, 16)
            password = self.get_pw()
            if not username or not password:
                self.show_error("Please enter a user name and a password!")
                continue
            key = self.join(username, password)

        self.end_gui()

    def show_error(self, error):
        self.screen.addstr(self.start_y + 6, self.start_x, error)
        self.screen.refresh()
        time.sleep(3)
        self.screen.clear()

    @staticmethod
    def available():
        # No special needs for curses, just set us to True
        return True
